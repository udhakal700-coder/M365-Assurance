import json
from collections import Counter
from datetime import datetime, timedelta, timezone

from config import CONTROLS_PATH, SEVERITY_POINTS, STALE_ACCOUNT_DAYS, STATUS_ORDER
from services.analytics import AssuranceAnalytics
from services.tenant_data import TenantDataService


class AssessmentEngine:
    """Evaluates synthetic Entra ID and Microsoft 365 configuration evidence."""

    PRIVILEGED_ROLES = {
        "Global Administrator", "Privileged Role Administrator", "Security Administrator",
        "Exchange Administrator", "SharePoint Administrator", "Conditional Access Administrator",
    }

    def __init__(self, tenant_data, controls_path=None, as_of=None):
        self.data = tenant_data
        self.controls_path = controls_path or CONTROLS_PATH
        self.as_of = as_of or datetime.now(timezone.utc)
        self.controls = self._load_controls()
        self._validate_tenant()

    def _load_controls(self):
        with self.controls_path.open("r", encoding="utf-8-sig") as file:
            controls = json.load(file)
        if not isinstance(controls, list):
            raise ValueError("Assessment controls must be a JSON list")
        return controls

    def _validate_tenant(self):
        self.validation_report = TenantDataService.validate(self.data)
        if not self.validation_report.valid:
            raise ValueError("Tenant data is invalid: " + "; ".join(self.validation_report.errors))

    @staticmethod
    def parse_time(value):
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

    def enabled_users(self):
        return [user for user in self.data["users"] if user.get("account_enabled", False)]

    def privileged_users(self):
        return [user for user in self.enabled_users() if self.PRIVILEGED_ROLES.intersection(user.get("roles", []))]

    def stale_users(self, days=STALE_ACCOUNT_DAYS):
        cutoff = self.as_of - timedelta(days=days)
        stale = []
        for user in self.enabled_users():
            try:
                if self.parse_time(user.get("last_activity")) < cutoff:
                    stale.append(user)
            except (TypeError, ValueError):
                stale.append(user)
        return stale

    def user_metrics(self):
        users, enabled, stale = self.data["users"], self.enabled_users(), self.stale_users()
        mfa_users = [user for user in enabled if user.get("mfa_registered", False)]
        return {
            "total_users": len(users),
            "enabled_users": len(enabled),
            "active_users": len([user for user in enabled if user not in stale]),
            "stale_users": len(stale),
            "disabled_users": len(users) - len(enabled),
            "guest_users": len([user for user in enabled if user.get("account_type") == "Guest"]),
            "privileged_users": len(self.privileged_users()),
            "mfa_registered_users": len(mfa_users),
            "mfa_coverage": round((len(mfa_users) / len(enabled) * 100) if enabled else 100),
            "departments": len({user.get("department") for user in enabled if user.get("department") != "External"}),
        }

    def hierarchy_summary(self):
        return dict(Counter(user.get("hierarchy_level", "Unclassified") for user in self.enabled_users()))

    def _result(self, control, status, finding, affected=None, evidence=None):
        affected = affected or []
        effort = control.get("expected_effort", "Medium")
        implementation_steps = control.get("implementation_steps") or [
            "Confirm the affected identities, configuration and approved scope.",
            "Implement the recommended change through the appropriate Microsoft 365 administration portal.",
            "Record the change owner, approval and implementation date.",
        ]
        validation_steps = control.get("validation_steps") or [
            "Collect fresh read-only evidence after implementation.",
            "Re-run the applicable control and confirm the affected population is cleared.",
            "Retain the validation evidence with the assessment record.",
        ]
        return {
            "control_id": control["control_id"], "control_name": control["control_name"],
            "category": control["category"], "status": status, "severity": control["severity"],
            "weight": int(control.get("weight", SEVERITY_POINTS.get(control["severity"], 1))),
            "finding": finding, "business_impact": control["business_impact"],
            "affected_count": len(affected), "affected_entities": affected,
            "evidence": evidence or {}, "recommendation": control["recommendation"],
            "remediation_owner": control.get("remediation_owner", "Microsoft 365 Administrator"),
            "target_timeframe": control.get("target_timeframe", "Within 30 days"),
            "source_name": control["source_name"], "source_url": control["source_url"],
            "licensing_note": control.get("licensing_note", ""),
            "required_license": control.get("required_license", control.get("licensing_note", "No additional licence requirement identified; validate against the tenant subscription.")),
            "expected_effort": effort,
            "implementation_steps": implementation_steps,
            "validation_steps": validation_steps,
            "exception_option": "Management may accept or defer this risk with a documented business rationale, accountable owner, expiry date and scheduled review.",
        }

    def _evaluate_control(self, control):
        test = control["test"]
        enabled, privileged = self.enabled_users(), self.privileged_users()
        configuration = self.data["security_configuration"]

        if test == "privileged_mfa":
            affected = [user["upn"] for user in privileged if not user.get("mfa_registered")]
            status = "Pass" if not affected else "Action required"
            finding = "All enabled privileged accounts are registered for MFA." if not affected else f"{len(affected)} privileged account(s) are not registered for MFA."
            return self._result(control, status, finding, affected, {"privileged_accounts_checked": len(privileged)})

        if test == "user_mfa_coverage":
            affected = [user["upn"] for user in enabled if not user.get("mfa_registered")]
            coverage = round(((len(enabled) - len(affected)) / len(enabled) * 100) if enabled else 100)
            target = int(control.get("minimum_percent", 100))
            return self._result(control, "Pass" if coverage >= target else "Action required",
                                f"MFA registration coverage is {coverage}% (target: {target}%).", affected,
                                {"enabled_users": len(enabled), "coverage_percent": coverage, "target_percent": target})

        if test == "global_admin_count":
            admins = [user for user in enabled if "Global Administrator" in user.get("roles", [])]
            minimum, maximum = int(control.get("minimum", 2)), int(control.get("maximum", 4))
            status = "Pass" if minimum <= len(admins) <= maximum else "Review"
            return self._result(control, status, f"{len(admins)} enabled Global Administrator account(s) were identified; assessment range: {minimum}–{maximum}.",
                                [user["upn"] for user in admins], {"count": len(admins), "assessment_range": f"{minimum}-{maximum}"})

        if test in {"stale_accounts", "stale_guests"}:
            days = int(control.get("inactive_days", STALE_ACCOUNT_DAYS))
            target_type = "Guest" if test == "stale_guests" else "Member"
            stale = [user for user in self.stale_users(days) if user.get("account_type") == target_type]
            label = "guest" if target_type == "Guest" else "member"
            return self._result(control, "Pass" if not stale else "Action required",
                                f"{len(stale)} enabled {label} account(s) have no activity within {days} days.",
                                [user["upn"] for user in stale], {"inactivity_threshold_days": days})

        if test == "boolean_control":
            field, value = control["field"], configuration.get(control["field"])
            if value is True:
                status, finding = "Pass", control["pass_message"]
            elif value is False:
                status, finding = "Action required", control["fail_message"]
            else:
                status, finding = "Not assessed", f"No evidence was supplied for {control['control_name'].lower()}."
            return self._result(control, status, finding, evidence={"configuration_field": field, "observed_value": value})

        if test == "external_forwarding":
            forwarding = [mailbox for mailbox in self.data["mailboxes"] if mailbox.get("external_forwarding_enabled")]
            affected = [mailbox["upn"] for mailbox in forwarding]
            finding = "No automatic external mailbox forwarding was identified." if not affected else f"{len(affected)} mailbox(es) automatically forward email externally."
            return self._result(control, "Pass" if not affected else "Action required", finding, affected,
                                {mailbox["upn"]: mailbox.get("forward_to", "External destination") for mailbox in forwarding})

        if test == "risky_signins":
            days = int(control.get("lookback_days", 30))
            cutoff, risky = self.as_of - timedelta(days=days), []
            for event in self.data["signins"]:
                try:
                    recent = self.parse_time(event.get("timestamp")) >= cutoff
                except (TypeError, ValueError):
                    recent = False
                if recent and event.get("risk_level") in {"high", "medium"} and event.get("risk_state") != "remediated":
                    risky.append(event)
            affected = sorted({event.get("upn", "Unknown") for event in risky})
            return self._result(control, "Pass" if not risky else "Review",
                                f"{len(risky)} unresolved medium/high-risk sign-in(s) were recorded in the last {days} days.",
                                affected, {"events": len(risky), "lookback_days": days})

        raise ValueError(f"Unsupported assessment test: {test}")

    def evaluate(self):
        results = [self._evaluate_control(control) for control in self.controls]
        results.sort(key=lambda item: (STATUS_ORDER.get(item["status"], 9), -item["weight"], item["control_id"]))
        scorable = [item for item in results if item["status"] != "Not assessed"]
        maximum = sum(item["weight"] for item in scorable)
        achieved = sum(item["weight"] for item in scorable if item["status"] == "Pass")
        achieved += sum(item["weight"] * 0.5 for item in scorable if item["status"] == "Review")
        score = round((achieved / maximum * 100) if maximum else 0)
        status_counts = Counter(item["status"] for item in results)
        issue_severities = Counter(item["severity"] for item in results if item["status"] in {"Action required", "Review"})
        summary = {
            **self.user_metrics(), "posture_score": score,
            "maturity": "Strong" if score >= 85 else "Developing" if score >= 65 else "Needs improvement" if score >= 40 else "High exposure",
            "controls_total": len(results), "controls_passed": status_counts["Pass"],
            "controls_action_required": status_counts["Action required"], "controls_review": status_counts["Review"],
            "controls_not_assessed": status_counts["Not assessed"], "critical_issues": issue_severities["Critical"],
            "high_issues": issue_severities["High"],
        }
        analytics_service = AssuranceAnalytics(self.data, as_of=self.as_of)
        analytics = {
            "usage": analytics_service.usage_summary(30),
            "identity": analytics_service.identity_summary(),
            "audit": analytics_service.audit_summary(30),
            "evidence_inventory": analytics_service.evidence_inventory(),
            "recommendation_matrix": analytics_service.recommendation_matrix(results),
        }
        assessment = {
            "tenant": self.data["tenant"], "scenario": self.data.get("scenario", "Current environment"),
            "assessment_profile": self.data.get("assessment_profile", {}),
            "assessed_at": self.as_of.isoformat().replace("+00:00", "Z"), "summary": summary,
            "results": results, "users": self.data["users"], "mailboxes": self.data["mailboxes"],
            "signins": self.data["signins"], "hierarchy": self.hierarchy_summary(),
            "groups": self.data.get("groups", []), "licenses": self.data.get("licenses", []),
            "devices": self.data.get("devices", []), "applications": self.data.get("applications", []),
            "usage_reports": self.data.get("usage_reports", []),
            "weekly_usage": self.data.get("weekly_usage", []),
            "service_capacity": self.data.get("service_capacity", []),
            "audit_logs": self.data.get("audit_logs", []),
            "usage_metadata": self.data.get("usage_metadata", {}),
            "authentication_methods": self.data.get("authentication_methods", []),
            "group_memberships": self.data.get("group_memberships", []),
            "license_assignments": self.data.get("license_assignments", []),
            "conditional_access_policies": self.data.get("conditional_access_policies", []),
            "sharing_links": self.data.get("sharing_links", []),
            "service_health": self.data.get("service_health", []),
            "historical_assessments": self.data.get("historical_assessments", []),
            "validation": {
                "valid": self.validation_report.valid,
                "errors": self.validation_report.errors,
                "warnings": self.validation_report.warnings,
                "statistics": self.validation_report.statistics,
                "completeness": self.validation_report.completeness,
            },
            "analytics": analytics,
            "correlated_stories": TenantDataService.correlated_stories(self.data),
        }
        assessment["executive_narrative"] = TenantDataService.executive_narrative(
            assessment, analytics["usage"]
        )
        return assessment
