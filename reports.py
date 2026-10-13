from collections import Counter
from datetime import datetime, timezone
from html import escape


def _badge(status):
    color = {
        "Pass": "#107c10",
        "Action required": "#d13438",
        "Review": "#ca5010",
        "Not assessed": "#605e5c",
    }.get(status, "#605e5c")
    return (
        f'<span class="badge" style="background:{color}">'
        f"{escape(status)}</span>"
    )


def _category_scores(results):
    categories = []
    for category in sorted({item["category"] for item in results}):
        items = [
            item
            for item in results
            if item["category"] == category and item["status"] != "Not assessed"
        ]
        maximum = sum(item["weight"] for item in items)
        achieved = sum(item["weight"] for item in items if item["status"] == "Pass")
        achieved += sum(
            item["weight"] * 0.5 for item in items if item["status"] == "Review"
        )
        score = round(achieved / maximum * 100) if maximum else 0
        categories.append((category, score))
    return categories


def build_html_report(assessment, assessor="M365 Assurance Consultant"):
    tenant = assessment["tenant"]
    summary = assessment["summary"]
    results = assessment["results"]
    generated = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    prepared_by = escape(str(assessor).strip() or "M365 Assurance Consultant")

    priority = [
        item for item in results if item["status"] in {"Action required", "Review"}
    ]
    severity_counts = Counter(item["severity"] for item in priority)
    usage = assessment.get("usage_reports", [])
    enabled_members = {
        user.get("upn")
        for user in assessment.get("users", [])
        if user.get("account_enabled") and user.get("account_type") == "Member"
    }
    core_fields = {
        "Teams": "teams_active",
        "Exchange": "exchange_active",
        "OneDrive": "onedrive_active",
        "SharePoint": "sharepoint_active",
    }
    member_usage = [row for row in usage if row.get("upn") in enabled_members]
    adopted_users = sum(any(row.get(field) for field in core_fields.values()) for row in member_usage)
    adoption_rate = round(adopted_users / len(enabled_members) * 100) if enabled_members else 0
    workload_activity = {
        workload: sum(bool(row.get(field)) for row in member_usage)
        for workload, field in core_fields.items()
    }
    licenses = assessment.get("licenses", [])
    purchased = sum(item.get("purchased", 0) for item in licenses)
    assigned = sum(item.get("assigned", 0) for item in licenses)
    licence_efficiency = round(assigned / purchased * 100) if purchased else 0
    audit_events = assessment.get("audit_logs", [])

    category_html = "".join(
        f"""
        <div class="domain">
          <div class="domain-head"><span>{escape(category)}</span><strong>{score}%</strong></div>
          <div class="bar"><span style="width:{score}%"></span></div>
        </div>
        """
        for category, score in _category_scores(results)
    )

    priority_html = "".join(
        f"""
        <div class="priority {escape(item['severity'].lower())}">
          <div><small>{escape(item['control_id'])} · {escape(item['category'])}</small>
          <h3>{escape(item['control_name'])}</h3><p>{escape(item['finding'])}</p></div>
          <div class="priority-meta"><strong>{escape(item['severity'])}</strong><br>
          {escape(item['remediation_owner'])}<br><small>{escape(item['target_timeframe'])}</small></div>
        </div>
        """
        for item in priority[:6]
    )

    control_rows = "".join(
        f"""
        <tr>
          <td><strong>{escape(item['control_id'])}</strong><br><small>{escape(item['category'])}</small></td>
          <td><strong>{escape(item['control_name'])}</strong><br>{escape(item['finding'])}</td>
          <td>{_badge(item['status'])}</td>
          <td>{escape(item['severity'])}</td>
          <td>{item['affected_count']}</td>
          <td>{escape(item['recommendation'])}<br>
          <small>Owner: {escape(item['remediation_owner'])} · {escape(item['target_timeframe'])}</small></td>
        </tr>
        """
        for item in results
    )

    roadmap_groups = [
        (
            "0–7 days",
            [item for item in priority if "0–7" in item["target_timeframe"] or "Within 7" in item["target_timeframe"]],
        ),
        (
            "8–14 days",
            [item for item in priority if "14" in item["target_timeframe"]],
        ),
        (
            "15–30 days",
            [item for item in priority if "30" in item["target_timeframe"]],
        ),
        (
            "30–90 days",
            [
                {
                    "control_id": "GOV",
                    "control_name": "Repeat assessment, review exceptions and report progress",
                }
            ],
        ),
    ]
    roadmap_html = "".join(
        f"""
        <div class="roadmap"><h3>{escape(timeframe)}</h3>
        {''.join(f'<p><strong>{escape(item["control_id"])}</strong> · {escape(item["control_name"])}</p>' for item in items) or '<p>No actions scheduled.</p>'}
        </div>
        """
        for timeframe, items in roadmap_groups
    )

    estate = [
        ("Directory identities", len(assessment.get("users", []))),
        ("Groups", len(assessment.get("groups", []))),
        ("Devices", len(assessment.get("devices", []))),
        ("Enterprise applications", len(assessment.get("applications", []))),
        ("Sign-in evidence", len(assessment.get("signins", []))),
        ("Usage records", len(usage)),
        ("Audit events", len(audit_events)),
    ]
    estate_html = "".join(
        f'<div class="mini"><span>{escape(label)}</span><strong>{value}</strong></div>'
        for label, value in estate
    )

    usage_rows = "".join(
        f"<tr><td><strong>{escape(workload)}</strong></td><td>{active}</td>"
        f"<td>{round(active / len(enabled_members) * 100) if enabled_members else 0}%</td></tr>"
        for workload, active in workload_activity.items()
    )

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Microsoft 365 Assurance Report</title>
<style>
@page{{size:A4 landscape;margin:13mm}}
*{{box-sizing:border-box}}body{{font-family:'Segoe UI',Arial,sans-serif;color:#242424;margin:0;background:#f5f5f5;line-height:1.42}}
.top{{height:9px;background:#0078d4}}.page{{max-width:1180px;margin:28px auto;background:#fff;padding:42px 46px;box-shadow:0 4px 18px #00000018}}
.brand{{display:flex;align-items:center;justify-content:space-between;color:#0078d4;font-size:13px;font-weight:700}}.brand-mark{{display:inline-block;background:#0078d4;color:#fff;padding:7px 10px;margin-right:9px}}
h1{{font-size:31px;font-weight:600;margin:14px 0 5px}}h2{{margin:31px 0 12px;font-size:20px;font-weight:600;border-bottom:1px solid #e1dfdd;padding-bottom:7px}}h3{{font-size:13px;margin:2px 0 5px}}p{{font-size:12px}}small,.muted{{color:#616161;font-size:10px}}
.notice{{background:#eff6fc;border-left:4px solid #0078d4;padding:12px 15px;margin:20px 0;font-size:11px}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px}}.card{{border:1px solid #e1dfdd;border-top:3px solid #0078d4;padding:14px;min-height:94px}}.label{{color:#616161;font-size:10px;text-transform:uppercase}}.value{{font-size:27px;font-weight:600;margin-top:5px}}.score{{font-size:34px;color:#0078d4;font-weight:600}}
.split{{display:grid;grid-template-columns:1fr 1fr;gap:22px}}.domain{{margin:10px 0}}.domain-head{{display:flex;justify-content:space-between;font-size:11px}}.bar{{height:8px;background:#edebe9;margin-top:4px}}.bar span{{height:8px;background:#0078d4;display:block}}
.priority{{display:grid;grid-template-columns:1fr 155px;gap:14px;border:1px solid #e1dfdd;border-left:4px solid #ca5010;padding:11px 13px;margin:7px 0}}.priority.critical{{border-left-color:#d13438}}.priority p{{margin:3px 0}}.priority-meta{{font-size:10px;text-align:right;color:#605e5c}}
.estate{{display:grid;grid-template-columns:repeat(7,1fr);gap:8px}}.mini{{border:1px solid #e1dfdd;padding:10px;display:flex;justify-content:space-between;font-size:10px}}.mini strong{{font-size:17px}}
.roadmap-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:9px}}.roadmap{{border:1px solid #e1dfdd;border-top:4px solid #0078d4;padding:11px;min-height:135px}}.roadmap p{{font-size:10px;border-top:1px solid #edebe9;padding-top:6px}}
table{{width:100%;border-collapse:collapse;font-size:9px}}th{{background:#f3f2f1;text-align:left;padding:8px;border-bottom:2px solid #c8c6c4}}td{{padding:8px;border-bottom:1px solid #edebe9;vertical-align:top}}.badge{{color:#fff;padding:3px 6px;font-size:9px;font-weight:600;white-space:nowrap}}
.footer{{margin-top:25px;padding-top:9px;border-top:1px solid #e1dfdd;color:#797775;font-size:9px}}
@media print{{body{{background:#fff}}.page{{box-shadow:none;margin:0;max-width:none;padding:0}}h2{{break-after:avoid}}table{{break-inside:auto}}tr{{break-inside:avoid}}}}
</style>
</head>
<body><div class="top"></div><main class="page">
<div class="brand"><div><span class="brand-mark">M</span>M365 Assurance</div><span>CLIENT ASSESSMENT REPORT</span></div>
<h1>Microsoft 365 Assurance, Usage &amp; Governance</h1>
<p class="muted">Assessment domain: {escape(tenant['primary_domain'])}<br>
Prepared by {prepared_by} · {generated} · Scenario: {escape(assessment['scenario'])}</p>
<div class="notice"><strong>Assessment scope:</strong> Synthetic Microsoft Entra ID and Microsoft 365 evidence. Validate results against the live tenant, licensing, business requirements and approved exceptions before any production change.</div>

<h2>1. Executive summary</h2>
<div class="grid">
  <div class="card"><div class="label">Posture score</div><div class="score">{summary['posture_score']}/100</div><small>{escape(summary['maturity'])}</small></div>
  <div class="card"><div class="label">Enabled identities</div><div class="value">{summary['enabled_users']}</div><small>{summary['guest_users']} guests · {summary['privileged_users']} privileged</small></div>
  <div class="card"><div class="label">MFA coverage</div><div class="value">{summary['mfa_coverage']}%</div><small>{summary['mfa_registered_users']} enabled identities registered</small></div>
  <div class="card"><div class="label">Action required</div><div class="value">{summary['controls_action_required']}</div><small>{severity_counts['Critical']} critical · {severity_counts['High']} high</small></div>
  <div class="card"><div class="label">Inactive users</div><div class="value">{summary['stale_users']}</div><small>Enabled and inactive for 90+ days</small></div>
  <div class="card"><div class="label">M365 adoption</div><div class="value">{adoption_rate}%</div><small>{adopted_users} active members · {licence_efficiency}% licence use</small></div>
</div>

<div class="split">
<section><h2>2. Security-domain health</h2>{category_html}</section>
<section><h2>3. Priority management findings</h2>{priority_html or '<p>No open findings in this scenario.</p>'}</section>
</div>

<h2>4. Usage and adoption</h2>
<p>Core-service activity helps distinguish adoption opportunities from security-control weaknesses. Activity alone does not prove productivity or business value.</p>
<table><thead><tr><th>Workload</th><th>Active members</th><th>Adoption</th></tr></thead><tbody>{usage_rows}</tbody></table>
<h2>5. Evidence coverage</h2><div class="estate">{estate_html}</div>
<h2>6. Recommended improvement roadmap</h2><div class="roadmap-grid">{roadmap_html}</div>

<h2>7. Detailed control results</h2>
<table><thead><tr><th>Control</th><th>Assessment result</th><th>Outcome</th><th>Risk</th><th>Affected</th><th>Recommended action</th></tr></thead><tbody>{control_rows}</tbody></table>

<h2>8. Interpretation and limitations</h2>
<p>The weighted score awards full control weight to Pass, half to Review and zero to Action required. Not-assessed controls are excluded from the denominator. The score is a prioritisation aid and should be read together with the detailed evidence and business context.</p>
<p>This deliverable is not a SOC service, continuous monitoring platform, penetration test, Microsoft certification, legal opinion or guarantee of security. A production assessment requires written authorisation, approved read-only evidence collection, tenant-specific validation and formal change control.</p>
<div class="footer">M365 Assurance · Microsoft 365 Assurance, Usage &amp; Governance · Generated {generated}</div>
</main></body></html>"""
