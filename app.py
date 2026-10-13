import copy
from datetime import date, timedelta
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import APP_NAME, APP_VERSION
from db import AssessmentStore
from engine import AssessmentEngine
from reports import build_html_report
from services.scenarios import SCENARIOS, load_scenario
from services.tenant_data import TenantDataService


st.set_page_config(page_title=APP_NAME, page_icon="◫", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
:root{--nav:#0f172a;--blue:#0f6cbd;--ink:#172033;--muted:#667085;--line:#e4e7ec;--canvas:#f5f7fa;--green:#107c10;--amber:#ca5010;--red:#c50f1f;--violet:#6b4eff}
html,body,[class*="css"]{font-family:Inter,"Segoe UI",Arial,sans-serif;color:var(--ink)}
.stApp{background:var(--canvas)}.block-container{max-width:1580px;padding:0 2rem 4rem}
#MainMenu,footer,[data-testid="stDecoration"]{display:none}[data-testid="stHeader"]{background:transparent;height:0}
[data-testid="stSidebar"]{background:var(--nav);border:0;width:286px!important}[data-testid="stSidebar"] *{color:#dce6f2}
[data-testid="stSidebar"] hr{border-color:#334155;margin:.8rem 0}[data-testid="stSidebar"] .stCaptionContainer p{color:#94a3b8!important;font-size:9px!important;letter-spacing:.1em;font-weight:700}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{font-size:10px;color:#cbd5e1}[data-testid="stSidebar"] div[data-baseweb="select"]>div,[data-testid="stSidebar"] div[data-baseweb="input"]>div{background:#1e293b;border-color:#475569}
[data-testid="stSidebar"] .stDownloadButton button{background:#fff;color:#172033;border:0;width:100%}
.brand{display:flex;align-items:center;gap:11px;padding:8px 2px 17px}.brand-mark{width:37px;height:37px;border-radius:8px;background:linear-gradient(135deg,#60a5fa,#0f6cbd);display:grid;place-items:center;color:#fff;font-weight:700;font-size:18px;box-shadow:0 8px 22px #0005}.brand-name{font-size:16px;font-weight:700;color:#fff}.brand-sub{font-size:9px;color:#94a3b8;margin-top:2px}.side-card{border:1px solid #334155;border-radius:8px;padding:11px 12px;background:#172033;font-size:10px;line-height:1.6}.side-card strong{display:block;color:#fff;font-size:12px;margin-bottom:2px}
.appbar{height:58px;margin:0 -2rem;padding:0 2rem;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between}.appbar-product{display:flex;align-items:center;gap:9px;font-size:12px;font-weight:600}.online{width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 0 4px #dcfce7}.appbar-meta{font-size:10px;color:var(--muted)}
.page-head{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;padding:25px 0 17px}.eyebrow{color:var(--blue);font-size:9px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px}.page-title{font-size:28px;font-weight:700;letter-spacing:-.03em;margin:0}.page-subtitle{font-size:12px;color:var(--muted);margin:7px 0 0;max-width:840px;line-height:1.55}.context{display:flex;gap:7px;flex-wrap:wrap;justify-content:flex-end}.pill{border:1px solid var(--line);background:#fff;border-radius:999px;padding:6px 10px;font-size:9px;color:#475467;white-space:nowrap}
div[data-baseweb="tab-list"]{gap:4px;background:#fff;border:1px solid var(--line);border-radius:9px;padding:5px;margin-bottom:18px;box-shadow:0 1px 2px #10182808;overflow-x:auto}button[data-baseweb="tab"]{border-radius:6px!important;padding:10px 13px!important;font-size:10px!important;font-weight:600!important;color:#667085!important;white-space:nowrap}button[data-baseweb="tab"]:hover{background:#f2f4f7!important;color:#0f6cbd!important}button[data-baseweb="tab"][aria-selected="true"]{background:#0f6cbd!important;color:#fff!important}button[data-baseweb="tab"][aria-selected="true"] p{color:#fff!important}
.metric{background:#fff;border:1px solid var(--line);border-radius:9px;padding:15px 16px;min-height:108px;box-shadow:0 1px 2px #10182808;position:relative;overflow:hidden}.metric:before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--accent,#0f6cbd)}.metric-label{font-size:10px;color:var(--muted);font-weight:600}.metric-value{font-size:27px;line-height:1.1;font-weight:700;letter-spacing:-.03em;margin:8px 0 5px}.metric-note{font-size:9px;color:#98a2b3;line-height:1.35}.metric.good{--accent:#107c10}.metric.warn{--accent:#ca5010}.metric.risk{--accent:#c50f1f}.metric.violet{--accent:#6b4eff}
.detail-head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;border-bottom:1px solid #eaecf0;padding-bottom:12px;margin-bottom:13px}.detail-kicker{font-size:8px;color:#0f6cbd;font-weight:700;letter-spacing:.09em;text-transform:uppercase}.detail-title{font-size:18px;font-weight:700;margin-top:3px}.detail-copy{font-size:10px;color:#667085;margin-top:5px;line-height:1.5}.detail-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.detail-item{background:#f8fafc;border:1px solid #eaecf0;border-radius:7px;padding:10px}.detail-label{font-size:8px;color:#667085;text-transform:uppercase;font-weight:700;letter-spacing:.06em}.detail-value{font-size:11px;color:#172033;margin-top:5px;line-height:1.45;overflow-wrap:anywhere}.card-action .stButton>button{margin-top:-1px;border-radius:0 0 8px 8px!important;border-color:#e4e7ec!important;background:#fff!important;color:#0f6cbd!important;box-shadow:none!important}.card-action .stButton>button:hover{background:#f5f9fd!important;border-color:#84b9e6!important}.priority-action .stButton>button{min-height:27px!important;height:27px!important;margin-top:-6px;background:#fff!important;color:#0f6cbd!important;border-color:#e4e7ec!important}
[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;border:1px solid var(--line)!important;border-radius:9px!important;box-shadow:0 1px 2px #10182808}.panel-title{font-size:13px;font-weight:700;margin:0 0 3px}.panel-subtitle{font-size:9px;color:var(--muted);margin-bottom:9px;line-height:1.45}.section{margin:24px 0 11px}.section-title{font-size:17px;font-weight:700}.section-copy{font-size:10px;color:var(--muted);margin-top:3px}
.priority{border:1px solid var(--line);border-radius:7px;padding:10px 11px;margin:7px 0;background:#fff;display:grid;grid-template-columns:7px 1fr auto;gap:9px;align-items:start}.priority-dot{width:7px;height:7px;border-radius:50%;margin-top:5px;background:var(--tone,#667085)}.priority.Critical{--tone:#c50f1f}.priority.High{--tone:#e05d16}.priority.Medium{--tone:#ca5010}.priority-name{font-size:11px;font-weight:600}.priority-meta{font-size:9px;color:var(--muted);margin-top:3px}.priority-owner{text-align:right;font-size:9px;color:#475467}
.status{display:inline-flex;align-items:center;border-radius:999px;padding:4px 7px;font-size:8px;font-weight:700;white-space:nowrap}.status.pass,.status.Completed{background:#ecfdf3;color:#067647}.status.action,.status.Blocked{background:#fef3f2;color:#b42318}.status.review,.status.In-progress{background:#fffaeb;color:#b54708}.status.Planned{background:#eff8ff;color:#175cd3}.status.Not-started,.status.na{background:#f2f4f7;color:#475467}
.callout{border-radius:7px;padding:11px 12px;font-size:10px;line-height:1.55;background:#eff8ff;color:#184e7a;border:1px solid #b2ddff}.callout strong{display:block;font-size:10px;margin-bottom:2px}.callout.warn{background:#fffaeb;color:#7a2e0e;border-color:#fedf89}.callout.risk{background:#fef3f2;color:#7a271a;border-color:#fecdca}.callout.neutral{background:#f8fafc;color:#475467;border-color:#e2e8f0}
.key{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px solid #f2f4f7;font-size:9px}.key span:first-child{color:var(--muted)}.key span:last-child{font-weight:600;text-align:right;overflow-wrap:anywhere}.domain-row{display:grid;grid-template-columns:165px 1fr 40px;gap:10px;align-items:center;padding:8px 0;border-bottom:1px solid #f2f4f7;font-size:10px}.domain-bar{height:7px;background:#eef2f6;border-radius:999px;overflow:hidden}.domain-fill{height:7px;border-radius:999px;background:var(--bar,#0f6cbd)}
.profile{border-radius:9px;overflow:hidden;border:1px solid var(--line);background:#fff}.profile-hero{background:linear-gradient(135deg,#172554,#0f6cbd);padding:18px;color:#fff}.avatar{width:44px;height:44px;border-radius:10px;background:#fff;color:#0f6cbd;display:grid;place-items:center;font-weight:700;font-size:15px;margin-bottom:12px}.profile-name{font-size:17px;font-weight:700}.profile-role{font-size:10px;color:#bfdbfe;margin-top:4px}.profile-body{padding:12px 15px}
.control-card{border:1px solid var(--line);border-radius:8px;background:#fff;padding:13px 14px;margin:8px 0;box-shadow:0 1px 2px #10182808}.control-top{display:flex;justify-content:space-between;gap:14px}.control-id{font-size:8px;font-weight:700;color:var(--blue);letter-spacing:.05em;text-transform:uppercase}.control-name{font-size:12px;font-weight:700;margin-top:3px}.control-finding{font-size:10px;color:#475467;margin-top:7px;line-height:1.5}.control-footer{display:grid;grid-template-columns:1.5fr .8fr .7fr;gap:12px;border-top:1px solid #f2f4f7;margin-top:10px;padding-top:9px}.mini-label{font-size:7px;text-transform:uppercase;letter-spacing:.07em;color:#98a2b3;font-weight:700}.mini-value{font-size:9px;color:#344054;margin-top:3px;line-height:1.45}
.source-card{border:1px solid var(--line);border-radius:8px;padding:13px;background:#fff;height:100%}.source-kicker{font-size:8px;color:var(--blue);font-weight:700;letter-spacing:.08em;text-transform:uppercase}.source-title{font-size:12px;font-weight:700;margin:5px 0}.source-copy{font-size:9px;color:var(--muted);line-height:1.5;min-height:42px}
[data-testid="stDataFrame"]{border:1px solid var(--line);border-radius:7px;overflow:hidden}.stButton>button,.stDownloadButton>button,.stLinkButton>a{border-radius:6px!important;font-weight:600;min-height:35px;font-size:10px!important}.stButton>button[kind="primary"]{background:#0f6cbd;border-color:#0f6cbd}div[data-baseweb="select"]>div,div[data-baseweb="input"]>div,textarea{border-radius:6px!important;border-color:var(--line)!important}.footer-note{font-size:8px;color:#98a2b3;border-top:1px solid var(--line);margin-top:28px;padding-top:12px}
@media(max-width:1050px){.block-container{padding:0 1rem 3rem}.appbar{margin:0 -1rem;padding:0 1rem}.page-head{align-items:flex-start;flex-direction:column}.context{justify-content:flex-start}.control-footer{grid-template-columns:1fr}.domain-row{grid-template-columns:130px 1fr 38px}}
</style>
""",
    unsafe_allow_html=True,
)

PAGE_TEXT = {
    "Executive overview": "A management view of adoption, identity health, control exposure and the next decisions to make.",
    "Usage & adoption": "Measure Microsoft 365 engagement, workload adoption, storage consumption and licence efficiency.",
    "Identity & sign-ins": "Review the Entra ID directory, MFA, lifecycle, devices, sign-in outcomes and identity risk.",
    "Audit explorer": "Search synthetic Purview-style events across file, email, permission, application and administrative activity.",
    "Access governance": "Understand hierarchy, privileged roles, group ownership, guest access and application consent risk.",
    "Security posture": "Assess common SME configuration risks against Microsoft-aligned controls and evidence.",
    "Actions & reports": "Assign remediation ownership, preserve snapshots and export a client-ready assessment report.",
}
M365_USAGE_URL = "https://learn.microsoft.com/en-us/microsoft-365/admin/activity-reports/activity-reports?view=o365-worldwide"
PURVIEW_AUDIT_URL = "https://learn.microsoft.com/en-us/purview/audit-search"
ENTRA_SIGNIN_URL = "https://learn.microsoft.com/en-us/entra/identity/monitoring-health/concept-sign-ins"


def h(value): return escape(str(value if value is not None else ""))
def slug(value): return str(value).replace(" ", "-")


def metric(label, value, note, tone=""):
    st.markdown(f'<div class="metric {tone}"><div class="metric-label">{h(label)}</div><div class="metric-value">{h(value)}</div><div class="metric-note">{h(note)}</div></div>', unsafe_allow_html=True)


def panel_title(title, subtitle=""):
    st.markdown(f'<div class="panel-title">{h(title)}</div><div class="panel-subtitle">{h(subtitle)}</div>', unsafe_allow_html=True)


def section(title, copy=""):
    st.markdown(f'<div class="section"><div class="section-title">{h(title)}</div><div class="section-copy">{h(copy)}</div></div>', unsafe_allow_html=True)


def tab_intro(title):
    st.markdown(f'<div class="section" style="margin-top:4px"><div class="section-title">{h(title)}</div><div class="section-copy">{h(PAGE_TEXT[title])}</div></div>', unsafe_allow_html=True)


def chart_style(figure, height=300, legend=True):
    figure.update_layout(height=height, margin=dict(l=8,r=8,t=18,b=8), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_family="Inter, Segoe UI, sans-serif", font_color="#475467", font_size=9, legend=dict(orientation="h", y=-.18) if legend else None, xaxis=dict(gridcolor="#f2f4f7", zeroline=False), yaxis=dict(gridcolor="#f2f4f7", zeroline=False))
    return figure


def score_ring(score):
    color = "#107c10" if score >= 85 else "#0f6cbd" if score >= 65 else "#ca5010" if score >= 40 else "#c50f1f"
    return chart_style(go.Figure(go.Indicator(mode="gauge+number", value=score, number={"suffix":"/100","font":{"size":31,"color":"#172033"}}, gauge={"shape":"angular","axis":{"range":[0,100],"visible":False},"bar":{"color":color,"thickness":.22},"bgcolor":"#eef2f6","borderwidth":0})), 215, False)


def status_badge(status):
    css = {"Pass":"pass","Action required":"action","Review":"review","Not assessed":"na"}.get(status, slug(status))
    return f'<span class="status {h(css)}">{h(status)}</span>'


def users_frame(assessment):
    frame = pd.DataFrame(assessment["users"])
    frame["last_activity"] = pd.to_datetime(frame["last_activity"], utc=True, errors="coerce")
    cutoff = pd.Timestamp(assessment["assessed_at"]) - timedelta(days=90)
    frame["Lifecycle"] = frame.apply(lambda row: "Disabled" if not row["account_enabled"] else ("Inactive" if pd.isna(row["last_activity"]) or row["last_activity"] < cutoff else "Active"), axis=1)
    frame["MFA"] = frame["mfa_registered"].map({True:"Registered",False:"Not registered"})
    frame["Directory role"] = frame["roles"].apply(lambda roles: ", ".join(roles) if roles else "Standard user")
    return frame


def category_scores(results):
    rows = []
    for category in sorted({item["category"] for item in results}):
        items = [item for item in results if item["category"] == category and item["status"] != "Not assessed"]
        maximum = sum(item["weight"] for item in items)
        achieved = sum(item["weight"] for item in items if item["status"] == "Pass") + sum(item["weight"] * .5 for item in items if item["status"] == "Review")
        rows.append({"Category":category,"Score":round(achieved / maximum * 100) if maximum else 0,"Open":sum(item["status"] in {"Action required","Review"} for item in items)})
    return pd.DataFrame(rows)


def privacy_copy(assessment, aliases):
    masked = copy.deepcopy(assessment)
    def mask_value(value):
        if isinstance(value, dict): return {aliases.get(key,key):mask_value(item) for key,item in value.items()}
        if isinstance(value, list): return [mask_value(item) for item in value]
        return aliases.get(value,value) if isinstance(value,str) else value
    for user in masked["users"]:
        original, alias = user["upn"], aliases.get(user["upn"], "User")
        user["display_name"], user["upn"] = alias, alias
        user["manager_upn"] = aliases.get(user.get("manager_upn"), user.get("manager_upn"))
    for collection, fields in [(masked.get("mailboxes",[]),["upn","forward_to"]),(masked.get("signins",[]),["upn"]),(masked.get("groups",[]),["owner_upn"]),(masked.get("devices",[]),["owner_upn"]),(masked.get("usage_reports",[]),["upn"]),(masked.get("audit_logs",[]),["actor_upn","target"])]:
        for item in collection:
            for field in fields:
                if item.get(field) in aliases: item[field] = aliases[item[field]]
    for result in masked.get("results",[]):
        result["affected_entities"] = mask_value(result.get("affected_entities",[]))
        result["evidence"] = mask_value(result.get("evidence",{}))
    return masked


store = AssessmentStore()
with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-mark">M</div><div><div class="brand-name">M365 Assurance</div><div class="brand-sub">Assurance · usage · governance</div></div></div>', unsafe_allow_html=True)
    st.caption("PRODUCT WORKSPACE")
    st.markdown('<div class="side-card"><strong>Unified Microsoft 365 view</strong>Usage, identity, audit, governance, posture and delivery in one client workspace.</div>', unsafe_allow_html=True)
    st.markdown("---"); st.caption("ASSESSMENT CONTEXT")
    scenario = st.selectbox("Scenario", list(SCENARIOS))
    reporting_days = st.selectbox("Reporting period", [7,30,90], index=1, format_func=lambda days: f"Last {days} days")
    conceal_names = st.toggle("Conceal user names", value=True, help="Masks names in on-screen tables and exported report data.")
    show_passed = st.toggle("Include passed controls", value=True)
    assessor = st.text_input("Prepared by", value="M365 Assurance Consultant")

assessment = AssessmentEngine(load_scenario(scenario)).evaluate()
summary, results, tenant = assessment["summary"], assessment["results"], assessment["tenant"]
users = users_frame(assessment)
groups, licenses = pd.DataFrame(assessment["groups"]), pd.DataFrame(assessment["licenses"])
devices, applications = pd.DataFrame(assessment["devices"]), pd.DataFrame(assessment["applications"])
signins, usage = pd.DataFrame(assessment["signins"]), pd.DataFrame(assessment["usage_reports"])
weekly_usage, capacity, audit = pd.DataFrame(assessment["weekly_usage"]), pd.DataFrame(assessment["service_capacity"]), pd.DataFrame(assessment["audit_logs"])
authentication_methods = pd.DataFrame(assessment["authentication_methods"])
license_assignments = pd.DataFrame(assessment["license_assignments"])
conditional_access = pd.DataFrame(assessment["conditional_access_policies"])
sharing_links = pd.DataFrame(assessment["sharing_links"])
validation = assessment["validation"]
correlated_stories = assessment["correlated_stories"]
aliases = {row.upn:f"User {index:03d}" for index, row in enumerate(users.itertuples(),1)}


def shown(value): return aliases.get(value, value) if conceal_names else value


users["Shown name"] = users.apply(lambda row: aliases[row["upn"]] if conceal_names else row["display_name"], axis=1)
users["Shown UPN"] = users["upn"].map(shown)
usage["last_activity"] = pd.to_datetime(usage["last_activity"], utc=True, errors="coerce")
signins["timestamp"] = pd.to_datetime(signins["timestamp"], utc=True, errors="coerce")
audit["timestamp"] = pd.to_datetime(audit["timestamp"], utc=True, errors="coerce")
as_of = pd.Timestamp(assessment["assessed_at"]); period_cutoff = as_of - pd.to_timedelta(int(reporting_days), unit="D")
recent_signins, recent_audit = signins[signins["timestamp"] >= period_cutoff].copy(), audit[audit["timestamp"] >= period_cutoff].copy()
eligible_upns = set(users[(users["account_enabled"]) & (users["account_type"] == "Member")]["upn"])
eligible_usage = usage[usage["upn"].isin(eligible_upns)].copy(); recent_usage = eligible_usage[eligible_usage["last_activity"] >= period_cutoff].copy()
workload_fields = {"Teams":"teams_active","Exchange":"exchange_active","OneDrive":"onedrive_active","SharePoint":"sharepoint_active"}
workload_counts = {label:int(recent_usage[field].sum()) for label, field in workload_fields.items()}
adopted_users = int(recent_usage[list(workload_fields.values())].any(axis=1).sum()) if not recent_usage.empty else 0
adoption_rate = round(adopted_users / max(len(eligible_upns),1) * 100)
licence_utilisation = round(licenses["assigned"].sum() / licenses["purchased"].sum() * 100) if not licenses.empty else 0
storage_used = capacity["used_gb"].sum() if not capacity.empty else 0
actions = store.remediation_actions(); action_map = {item["control_id"]:item for item in actions}
open_results = [item for item in results if item["status"] in {"Action required","Review"}]
completed_actions = sum(action_map.get(item["control_id"],{}).get("status") == "Completed" for item in open_results)
remediation_progress = round(completed_actions / len(open_results) * 100) if open_results else 100
device_compliance = round(devices["compliant"].mean() * 100) if not devices.empty else 0
identity_health = round(summary["mfa_coverage"] * .55 + (summary["active_users"] / max(summary["enabled_users"],1) * 100) * .25 + device_compliance * .20)


@st.dialog("Assessment detail", width="large")
def show_executive_detail(detail_key):
    detail_titles = {
        "security_posture": ("Security posture", "Control performance, maturity and outstanding exposure."),
        "active_users": ("Active users", "Enabled identities and their recent lifecycle position."),
        "m365_adoption": ("Microsoft 365 adoption", "Workload engagement for eligible internal members."),
        "open_problems": ("Open problems", "Assessment findings that require action or review."),
        "licence_use": ("Licence utilisation", "Purchased, assigned and potentially avoidable licence capacity."),
    }
    title, copy_text = detail_titles[detail_key]
    st.markdown(f'<div class="detail-head"><div><div class="detail-kicker">Executive drill-down</div><div class="detail-title">{h(title)}</div><div class="detail-copy">{h(copy_text)}</div></div></div>', unsafe_allow_html=True)
    if detail_key == "security_posture":
        a, b, c = st.columns(3)
        a.metric("Posture score", f"{summary['posture_score']}/100"); b.metric("Controls passed", f"{summary['controls_passed']}/{summary['controls_total']}"); c.metric("Evidence completeness", f"{validation['completeness']}%")
        st.dataframe(category_scores(results), width="stretch", hide_index=True)
    elif detail_key == "active_users":
        active_detail = users[users["Lifecycle"] == "Active"][["Shown name","Shown UPN","department","job_title","MFA","Directory role","last_activity"]].copy()
        active_detail["last_activity"] = active_detail["last_activity"].dt.strftime("%d %b %Y")
        st.dataframe(active_detail.rename(columns={"Shown name":"Name","Shown UPN":"User principal name","department":"Department","job_title":"Job title","last_activity":"Last activity"}), width="stretch", hide_index=True)
    elif detail_key == "m365_adoption":
        adoption_detail = usage[usage["upn"].isin(eligible_upns)].copy(); adoption_detail["User"] = adoption_detail["upn"].map(shown)
        for label, field in workload_fields.items(): adoption_detail[label] = adoption_detail[field].map({True:"Active",False:"Inactive"})
        st.dataframe(adoption_detail[["User","department","Teams","Exchange","OneDrive","SharePoint","last_activity"]].rename(columns={"department":"Department","last_activity":"Last activity"}), width="stretch", hide_index=True)
    elif detail_key == "open_problems":
        problem_rows = [{"Control":item["control_id"],"Problem":item["control_name"],"Severity":item["severity"],"Status":item["status"],"Affected":item["affected_count"],"Owner":item["remediation_owner"],"Target":item["target_timeframe"]} for item in open_results]
        st.dataframe(pd.DataFrame(problem_rows), width="stretch", hide_index=True)
    elif detail_key == "licence_use":
        licence_detail = licenses.copy(); licence_detail["Available value / month (AUD)"] = (licence_detail["available"] * licence_detail["monthly_unit_cost_aud"]).round(2)
        st.dataframe(licence_detail.rename(columns={"sku":"Licence","purchased":"Purchased","assigned":"Assigned","available":"Available","monthly_unit_cost_aud":"Unit cost / month (AUD)"}), width="stretch", hide_index=True)
        st.info("Licence values are illustrative assessment evidence. Confirm contractual terms and business demand before making subscription changes.")


@st.dialog("Recommendation detail", width="large")
def show_finding_detail(finding):
    st.markdown(f'<div class="detail-head"><div><div class="detail-kicker">{h(finding["control_id"])} · {h(finding["severity"])} · {h(finding["status"])}</div><div class="detail-title">{h(finding["control_name"])}</div><div class="detail-copy">{h(finding["finding"])}</div></div></div>', unsafe_allow_html=True)
    detail_fields = [("Business impact",finding["business_impact"]),("Affected entities",", ".join(map(shown,finding["affected_entities"])) or "Tenant-wide setting"),("Accountable owner",finding["remediation_owner"]),("Target timeframe",finding["target_timeframe"]),("Expected effort",finding["expected_effort"]),("Required licence",finding["required_license"])]
    st.markdown('<div class="detail-grid">' + ''.join(f'<div class="detail-item"><div class="detail-label">{h(label)}</div><div class="detail-value">{h(value)}</div></div>' for label,value in detail_fields) + '</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Recommended change**"); st.write(finding["recommendation"])
        st.markdown("**Implementation steps**")
        for index, step in enumerate(finding["implementation_steps"],1): st.write(f"{index}. {step}")
    with col_b:
        st.markdown("**Validation steps**")
        for index, step in enumerate(finding["validation_steps"],1): st.write(f"{index}. {step}")
        st.markdown("**Exception / acceptance option**"); st.write(finding["exception_option"])
        st.link_button("Open Microsoft reference", finding["source_url"], width="stretch")


@st.dialog("Workload activity", width="large")
def show_workload_detail(workload):
    active_field = workload_fields[workload]
    workload_detail = usage[usage["upn"].isin(eligible_upns)].copy(); workload_detail["User"] = workload_detail["upn"].map(shown); workload_detail["Activity"] = workload_detail[active_field].map({True:"Active",False:"Inactive"})
    active_count = int(workload_detail[active_field].sum())
    st.markdown(f'<div class="detail-head"><div><div class="detail-kicker">Microsoft 365 workload</div><div class="detail-title">{h(workload)}</div><div class="detail-copy">{active_count} active members during the selected {reporting_days}-day reporting period.</div></div></div>', unsafe_allow_html=True)
    st.dataframe(workload_detail[["User","department","Activity","last_activity"]].rename(columns={"department":"Department","last_activity":"Last activity"}), width="stretch", hide_index=True)

with st.sidebar:
    st.markdown("---")
    st.markdown(f'<div class="side-card"><strong>{h(scenario)}</strong>{summary["posture_score"]}/100 posture · {adoption_rate}% adoption<br>{len(open_results)} actions · {remediation_progress}% delivered</div>', unsafe_allow_html=True)
    report_assessment = privacy_copy(assessment, aliases) if conceal_names else assessment
    report_html = build_html_report(report_assessment, assessor=assessor)
    st.download_button("Download client report", report_html.encode("utf-8"), "M365_Assurance_Report.html", "text/html", width="stretch")
    st.caption(f"VERSION {APP_VERSION} · SYNTHETIC DATA")

st.markdown('<div class="appbar"><div class="appbar-product"><span class="online"></span><span>M365 Assurance</span><span style="color:#d0d5dd">/</span><span style="color:#667085;font-weight:500">Client workspace</span></div><div class="appbar-meta">Microsoft 365 · Purview · Entra ID</div></div>', unsafe_allow_html=True)
assessed = pd.Timestamp(assessment["assessed_at"]).strftime("%d %b %Y · %H:%M UTC")
st.markdown(f'<div class="page-head"><div><div class="eyebrow">Microsoft 365 assurance workspace</div><h1 class="page-title">Usage, identity, audit and security posture</h1><p class="page-subtitle">A tenant-friendly assessment product for SMEs: understand who is active, how Microsoft 365 is used, what changed, where common risks exist and who owns the improvement.</p></div><div class="context"><span class="pill">{h(tenant["primary_domain"])}</span><span class="pill">{h(scenario)}</span><span class="pill">{reporting_days}-day view</span><span class="pill">Assessed {h(assessed)}</span></div></div>', unsafe_allow_html=True)

(overview_tab, usage_tab, identity_tab, audit_tab, governance_tab, posture_tab, actions_tab) = st.tabs(["Executive overview","Usage & adoption","Identity & sign-ins","Audit explorer","Access governance","Security posture","Actions & reports"])

with overview_tab:
    tab_intro("Executive overview")
    columns = st.columns(5)
    values = [
        ("Security posture", f"{summary['posture_score']}/100", summary["maturity"], "violet", "security_posture"),
        ("Active users", summary["active_users"], f"{summary['enabled_users']} enabled identities", "good", "active_users"),
        ("M365 adoption", f"{adoption_rate}%", f"{adopted_users} of {len(eligible_upns)} members active", "good", "m365_adoption"),
        ("Open problems", len(open_results), f"{summary['critical_issues']} critical · {summary['high_issues']} high", "risk", "open_problems"),
        ("Licence use", f"{licence_utilisation}%", f"{int(licenses['available'].sum())} unassigned seats", "warn", "licence_use"),
    ]
    for column, value in zip(columns, values):
        label, amount, note, tone, detail_key = value
        with column:
            metric(label, amount, note, tone)
            st.markdown('<div class="card-action">', unsafe_allow_html=True)
            if st.button("Review details", key=f"executive_{detail_key}", width="stretch"):
                show_executive_detail(detail_key)
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="callout"><strong>Executive interpretation</strong>{h(assessment["executive_narrative"])} Evidence completeness is {validation["completeness"]}%.</div>', unsafe_allow_html=True)

    left, middle, right = st.columns([.9,1.15,1.2])
    with left:
        with st.container(border=True):
            panel_title("Posture score", "Weighted outcome across 13 SME controls")
            st.plotly_chart(score_ring(summary["posture_score"]), width="stretch", config={"displayModeBar":False})
            st.markdown(f'<div class="callout warn"><strong>{h(summary["maturity"])}</strong>{summary["controls_passed"]} of {summary["controls_total"]} controls currently pass.</div>', unsafe_allow_html=True)
    with middle:
        with st.container(border=True):
            panel_title("Security domain health", "Control performance by assessment area")
            category = category_scores(results).sort_values("Score")
            for _, row in category.iterrows():
                tone = "#107c10" if row["Score"] >= 80 else "#0f6cbd" if row["Score"] >= 60 else "#ca5010" if row["Score"] >= 35 else "#c50f1f"
                st.markdown(f'<div class="domain-row"><span>{h(row["Category"])}</span><div class="domain-bar"><div class="domain-fill" style="width:{int(row["Score"])}%;--bar:{tone}"></div></div><strong>{int(row["Score"])}%</strong></div>', unsafe_allow_html=True)
    with right:
        with st.container(border=True):
            panel_title("Priority actions", "Highest-impact issues requiring a decision")
            for item in open_results[:5]:
                delivery = action_map.get(item["control_id"],{}).get("status","Not started")
                st.markdown(f'<div class="priority {h(item["severity"])}"><span class="priority-dot"></span><div><div class="priority-name">{h(item["control_name"])}</div><div class="priority-meta">{h(item["control_id"])} · {item["affected_count"]} affected · {h(item["target_timeframe"])}</div></div><div class="priority-owner">{status_badge(delivery)}<br>{h(item["remediation_owner"])}</div></div>', unsafe_allow_html=True)
                st.markdown('<div class="priority-action">', unsafe_allow_html=True)
                if st.button("Review evidence and recommendation", key=f"priority_{item['control_id']}", width="stretch"):
                    show_finding_detail(item)
                st.markdown('</div>', unsafe_allow_html=True)

    section("Microsoft 365 service snapshot", "Active members by core workload for the selected reporting period.")
    workload_cols = st.columns(4)
    workload_notes = {"Teams":"Chat, meetings and calls","Exchange":"Email activity","OneDrive":"Personal file activity","SharePoint":"Sites and shared content"}
    for column, (workload, count) in zip(workload_cols, workload_counts.items()):
        with column:
            metric(workload, count, f"{workload_notes[workload]} · {reporting_days} days")
            st.markdown('<div class="card-action">', unsafe_allow_html=True)
            if st.button("View workload", key=f"workload_{workload}", width="stretch"):
                show_workload_detail(workload)
            st.markdown('</div>', unsafe_allow_html=True)

    section("Evidence coverage", "The product combines three Microsoft administration views with a structured SME assessment.")
    evidence_cols = st.columns(3)
    evidence_cards = [
        ("Microsoft 365 usage","Adoption, active users, storage and licence efficiency.",f"{len(usage)} user usage records"),
        ("Microsoft Purview audit","Searchable user and administrator operations across workloads.",f"{len(recent_audit)} events in view"),
        ("Microsoft Entra ID","Directory, MFA, sign-ins, roles, guests, groups and applications.",f"{len(users)} identities · {len(recent_signins)} sign-ins"),
    ]
    for column, (title, copy_text, evidence) in zip(evidence_cols, evidence_cards):
        with column:
            st.markdown(f'<div class="source-card"><div class="source-kicker">Integrated evidence</div><div class="source-title">{h(title)}</div><div class="source-copy">{h(copy_text)}</div><div class="key"><span>Current dataset</span><span>{h(evidence)}</span></div></div>', unsafe_allow_html=True)
    with st.expander("Data sources and Microsoft portal paths"):
        a, b, c = st.columns(3)
        with a:
            st.markdown("**Usage & adoption**  \nMicrosoft 365 admin center → **Reports → Usage**. Review activity, mailbox/OneDrive/SharePoint storage and service-specific reports.")
            st.link_button("Open Microsoft guidance", M365_USAGE_URL, width="stretch")
        with b:
            st.markdown("**Unified audit**  \nMicrosoft Purview portal → **Audit**. Search by time, user, operation, record type, file/site and workload.")
            st.link_button("Open Purview guidance", PURVIEW_AUDIT_URL, width="stretch")
        with c:
            st.markdown("**Identity & sign-ins**  \nMicrosoft Entra admin center → **Identity → Monitoring & health → Sign-in logs**. Review outcomes and risk context.")
            st.link_button("Open Entra guidance", ENTRA_SIGNIN_URL, width="stretch")


with usage_tab:
    tab_intro("Usage & adoption")
    usage_cols = st.columns(4)
    usage_values = [
        ("Active members", adopted_users, f"At least one core workload · {reporting_days} days", "good"),
        ("Adoption rate", f"{adoption_rate}%", "Enabled internal identities", "good"),
        ("Storage used", f"{storage_used:,.1f} GB", "Exchange, OneDrive and SharePoint", ""),
        ("Licence efficiency", f"{licence_utilisation}%", f"{int(licenses['assigned'].sum())} of {int(licenses['purchased'].sum())} seats assigned", "warn"),
    ]
    for column, value in zip(usage_cols, usage_values):
        with column: metric(*value)

    with st.expander("Workload deep dive", expanded=False):
        selected_workload = st.segmented_control("Microsoft 365 workload", ["Teams","Exchange","OneDrive","SharePoint","Microsoft 365 Apps"], default="Teams")
        workload_map = {
            "Teams": ("teams_active", ["teams_messages","teams_meetings","teams_calls_minutes"]),
            "Exchange": ("exchange_active", ["emails_sent","emails_received","mailbox_storage_gb"]),
            "OneDrive": ("onedrive_active", ["onedrive_files","onedrive_storage_gb"]),
            "SharePoint": ("sharepoint_active", ["sharepoint_actions"]),
        }
        if selected_workload in workload_map:
            active_field, measures = workload_map[selected_workload]
            deep = eligible_usage.copy(); active_count = int(deep[active_field].sum()); inactive_count = int((~deep[active_field]).sum())
            cols = st.columns(4)
            deep_values = [("Active users",active_count,f"{reporting_days}-day activity","good"),("Inactive licensed",inactive_count,"Validate business need","warn")]
            for field in measures[:2]: deep_values.append((field.replace("_"," ").title(),f'{deep[field].sum():,.1f}',"Recorded activity",""))
            while len(deep_values) < 4: deep_values.append(("Adoption",f'{round(active_count / max(len(deep),1) * 100)}%',"Eligible members","violet"))
            for column, value in zip(cols, deep_values):
                with column: metric(*value)
            department = deep.groupby("department",as_index=False).agg(Eligible=("upn","count"),Active=(active_field,"sum")); department["Adoption %"] = (department["Active"] / department["Eligible"] * 100).round()
            chart_col, users_col = st.columns([1.35,1])
            with chart_col:
                figure = px.bar(department,x="department",y="Adoption %",text="Adoption %",range_y=[0,100],color_discrete_sequence=["#0f6cbd"])
                figure.update_xaxes(title=None); figure.update_yaxes(title="Adoption %")
                st.plotly_chart(chart_style(figure,250,False),width="stretch",config={"displayModeBar":False})
            with users_col:
                inactive_rows = deep[~deep[active_field]].copy(); inactive_rows["User"] = inactive_rows["upn"].map(shown)
                panel_title("Licensed users without activity", "Candidates for validation or licence review")
                if inactive_rows.empty: st.success("All eligible users recorded activity.")
                else: st.dataframe(inactive_rows[["User","department","last_activity"]].rename(columns={"department":"Department","last_activity":"Last activity"}),width="stretch",hide_index=True)
        else:
            assigned = license_assignments[license_assignments["sku"].str.contains("365",case=False,na=False)].copy()
            inactive = assigned[~assigned["upn"].isin(set(recent_usage["upn"]))].copy(); inactive["User"] = inactive["upn"].map(shown)
            cols = st.columns(3)
            for column, value in zip(cols, [("Assigned users",len(assigned),"Microsoft 365 licence assignments",""),("Active users",adopted_users,"Any core workload","good"),("No recent activity",len(inactive),"Review candidates","warn")]):
                with column: metric(*value)
            if not inactive.empty: st.dataframe(inactive[["User","sku","assignment_state"]].rename(columns={"sku":"Licence","assignment_state":"State"}),width="stretch",hide_index=True)

    chart_left, chart_right = st.columns([1,1.5])
    active_frame = pd.DataFrame({"Workload":list(workload_counts),"Active users":list(workload_counts.values())})
    with chart_left:
        with st.container(border=True):
            panel_title("Active users by workload", f"Selected {reporting_days}-day period")
            figure = px.bar(active_frame, x="Workload", y="Active users", text="Active users", color="Workload", color_discrete_sequence=["#0f6cbd","#6b4eff","#0891b2","#107c10"])
            figure.update_xaxes(title=None); figure.update_yaxes(title="Users",dtick=1); figure.update_traces(textposition="outside")
            st.plotly_chart(chart_style(figure,315,False), width="stretch", config={"displayModeBar":False})
    with chart_right:
        with st.container(border=True):
            panel_title("Weekly adoption trend", "Synthetic active-user trend by core service")
            trend = weekly_usage.copy(); trend["week_start"] = pd.to_datetime(trend["week_start"], utc=True)
            trend = trend[trend["week_start"] >= period_cutoff.floor("D")]
            if trend.empty: trend = weekly_usage.tail(1).assign(week_start=pd.to_datetime(weekly_usage.tail(1)["week_start"], utc=True))
            trend = trend.melt(id_vars="week_start", var_name="Workload", value_name="Active users")
            figure = px.line(trend, x="week_start", y="Active users", color="Workload", markers=True, color_discrete_sequence=["#0f6cbd","#6b4eff","#0891b2","#107c10"])
            figure.update_xaxes(title=None); figure.update_yaxes(title="Active users",dtick=1)
            st.plotly_chart(chart_style(figure,315), width="stretch", config={"displayModeBar":False})

    section("Capacity and licence position", "Separate adoption from capacity: low consumption is not automatically a problem, but unused licences may warrant review.")
    cap_col, lic_col = st.columns(2)
    with cap_col:
        with st.container(border=True):
            panel_title("Service storage", "Used versus allocated capacity")
            cap = capacity.copy(); cap["Utilisation"] = (cap["used_gb"] / cap["allocated_gb"] * 100).round(1)
            cap_long = cap.melt(id_vars=["service","status"], value_vars=["used_gb","allocated_gb"], var_name="Measure", value_name="GB")
            figure = px.bar(cap_long, y="service", x="GB", color="Measure", barmode="group", log_x=True, color_discrete_map={"used_gb":"#0f6cbd","allocated_gb":"#d0d5dd"})
            figure.update_xaxes(title="GB (log scale)"); figure.update_yaxes(title=None)
            st.plotly_chart(chart_style(figure,250), width="stretch", config={"displayModeBar":False})
            st.dataframe(cap[["service","used_gb","allocated_gb","Utilisation","status"]].rename(columns={"service":"Service","used_gb":"Used GB","allocated_gb":"Allocated GB","status":"Status"}), width="stretch", hide_index=True)
    with lic_col:
        with st.container(border=True):
            panel_title("Licence efficiency", "Purchased, assigned and available seats")
            licence_chart = licenses.melt(id_vars="sku", value_vars=["assigned","available"], var_name="State", value_name="Seats")
            figure = px.bar(licence_chart, y="sku", x="Seats", color="State", orientation="h", barmode="stack", color_discrete_map={"assigned":"#0f6cbd","available":"#d0d5dd"})
            figure.update_xaxes(title="Seats",dtick=1); figure.update_yaxes(title=None)
            st.plotly_chart(chart_style(figure,250), width="stretch", config={"displayModeBar":False})
            unused_value = (licenses["available"] * licenses["monthly_unit_cost_aud"]).sum()
            st.markdown(f'<div class="callout neutral"><strong>Review opportunity</strong>Illustrative unassigned monthly value: A${unused_value:,.2f}. Validate current licensing and business demand before changing subscriptions.</div>', unsafe_allow_html=True)

    section("Per-user activity", "Filter the report as a Microsoft 365 administrator would. Names follow the privacy setting in the sidebar.")
    f1, f2, f3 = st.columns([1,1,1.4])
    departments = sorted(usage["department"].unique())
    dept_filter = f1.multiselect("Department", departments, default=departments, key="usage_department")
    service_filter = f2.selectbox("Workload activity", ["Any workload"] + list(workload_fields), key="usage_service")
    activity_query = f3.text_input("Search activity report", placeholder="User or department", key="usage_query")
    usage_view = usage[usage["department"].isin(dept_filter)].copy()
    if service_filter != "Any workload": usage_view = usage_view[usage_view[workload_fields[service_filter]]]
    if activity_query: usage_view = usage_view[usage_view.astype(str).apply(lambda row: row.str.contains(activity_query, case=False, regex=False).any(), axis=1)]
    usage_view["User"] = usage_view["upn"].map(shown); usage_view["Last activity"] = usage_view["last_activity"].dt.strftime("%d %b %Y")
    for label, field in workload_fields.items(): usage_view[label] = usage_view[field].map({True:"Active",False:"Inactive"})
    usage_columns = ["User","department","Teams","teams_messages","Exchange","emails_sent","OneDrive","onedrive_storage_gb","SharePoint","sharepoint_actions","Last activity"]
    usage_labels = {"department":"Department","teams_messages":"Teams messages","emails_sent":"Emails sent","onedrive_storage_gb":"OneDrive GB","sharepoint_actions":"SharePoint actions"}
    usage_export = usage_view[usage_columns].rename(columns=usage_labels)
    st.dataframe(usage_export, width="stretch", hide_index=True, height=420)
    st.download_button("Export filtered usage report", usage_export.to_csv(index=False).encode("utf-8"), "M365_Assurance_Usage.csv", "text/csv")
    st.caption("Usage statistics are synthetic and intended to demonstrate a reporting workflow. Production Microsoft 365 reports may have reporting latency and licence-dependent fields.")

with identity_tab:
    tab_intro("Identity & sign-ins")
    identity_overview, directory_view_tab, signin_view_tab, user_360_tab = st.tabs(["Identity overview","Directory users","Sign-in activity","User 360"])
    with identity_overview:
        enabled = users[users["account_enabled"]].copy()
        privileged = enabled[enabled["roles"].apply(lambda roles: bool(AssessmentEngine.PRIVILEGED_ROLES.intersection(roles)))]
        inactive = enabled[enabled["Lifecycle"] == "Inactive"]
        guests = enabled[enabled["account_type"] == "Guest"]
        cols = st.columns(5)
        values = [
            ("Enabled identities",summary["enabled_users"],f"{summary['total_users']} directory objects",""),
            ("MFA coverage",f"{summary['mfa_coverage']}%",f"{summary['mfa_registered_users']} registered","good"),
            ("Inactive",summary["stale_users"],"Enabled for 90+ inactive days","warn"),
            ("External guests",summary["guest_users"],"Sponsor review required","violet"),
            ("Privileged",summary["privileged_users"],"Administrative identities","risk"),
        ]
        for column, value in zip(cols, values):
            with column: metric(*value)
        left, right = st.columns([1.4,1])
        with left:
            with st.container(border=True):
                panel_title("MFA adoption by department", "Enabled identities")
                mfa = enabled.groupby("department",as_index=False).agg(Enabled=("user_id","count"),Registered=("mfa_registered","sum")); mfa["Not registered"] = mfa["Enabled"] - mfa["Registered"]
                mfa = mfa.melt(id_vars="department", value_vars=["Registered","Not registered"], var_name="MFA", value_name="Users")
                fig = px.bar(mfa, x="department", y="Users", color="MFA", barmode="stack", color_discrete_map={"Registered":"#107c10","Not registered":"#c50f1f"})
                fig.update_xaxes(title=None,tickangle=-20); fig.update_yaxes(title="Users",dtick=1)
                st.plotly_chart(chart_style(fig,315), width="stretch", config={"displayModeBar":False})
        with right:
            with st.container(border=True):
                panel_title("Identity lifecycle", "Active, inactive and disabled objects")
                lifecycle = users["Lifecycle"].value_counts().rename_axis("State").reset_index(name="Users")
                fig = px.pie(lifecycle, names="State", values="Users", hole=.68, color="State", color_discrete_map={"Active":"#0f6cbd","Inactive":"#ca5010","Disabled":"#98a2b3"})
                fig.update_traces(textinfo="label+value",textfont_size=9)
                st.plotly_chart(chart_style(fig,315,False), width="stretch", config={"displayModeBar":False})
        section("Priority identity populations", "Review administrator protection, account lifecycle and guest sponsorship.")
        a, b, c = st.columns(3)
        with a:
            with st.container(border=True):
                panel_title("Privileged identities", f"{len(privileged)} enabled administrators")
                for _, user in privileged.iterrows():
                    st.markdown(f'<div class="key"><span>{h(shown(user["upn"]))}<br><small>{h(user["Directory role"])}</small></span><span>{status_badge("Pass" if user["mfa_registered"] else "Action required")}</span></div>', unsafe_allow_html=True)
        with b:
            with st.container(border=True):
                panel_title("Inactive enabled identities", f"{len(inactive)} lifecycle decisions")
                for _, user in inactive.iterrows():
                    last_seen = user["last_activity"].strftime("%d %b %Y") if pd.notna(user["last_activity"]) else "Unknown"
                    st.markdown(f'<div class="key"><span>{h(shown(user["upn"]))}<br><small>{h(user["job_title"])}</small></span><span>{h(last_seen)}</span></div>', unsafe_allow_html=True)
        with c:
            with st.container(border=True):
                panel_title("External identities", f"{len(guests)} enabled guests")
                for _, user in guests.iterrows():
                    st.markdown(f'<div class="key"><span>{h(shown(user["upn"]))}<br><small>{h(user["job_title"])}</small></span><span>{h(user["Lifecycle"])}</span></div>', unsafe_allow_html=True)
        section("Device trust", "Entra registration and management context associated with the identity estate.")
        device_view = devices.copy(); device_view["Owner"] = device_view["owner_upn"].map(shown)
        st.dataframe(device_view[["display_name","Owner","operating_system","join_type","compliant","managed","last_checkin"]].rename(columns={"display_name":"Device","operating_system":"Operating system","join_type":"Join type","compliant":"Compliant","managed":"Managed","last_checkin":"Last check-in"}), width="stretch", hide_index=True)

    with directory_view_tab:
        f1, f2, f3, f4 = st.columns([1,1,1,1.3])
        lifecycle_options, type_options, department_options = sorted(users["Lifecycle"].unique()), sorted(users["account_type"].unique()), sorted(users["department"].unique())
        life_filter = f1.multiselect("Lifecycle", lifecycle_options, default=lifecycle_options, key="dir_life")
        type_filter = f2.multiselect("Identity type", type_options, default=type_options, key="dir_type")
        department_filter = f3.multiselect("Department", department_options, default=department_options, key="dir_dept")
        query = f4.text_input("Search directory", placeholder="Name, email, title or role", key="dir_search")
        visible = users[users["Lifecycle"].isin(life_filter) & users["account_type"].isin(type_filter) & users["department"].isin(department_filter)].copy()
        if query: visible = visible[visible.astype(str).apply(lambda row: row.str.contains(query,case=False,regex=False).any(),axis=1)]
        table_col, profile_col = st.columns([2.15,.9])
        with table_col:
            with st.container(border=True):
                panel_title("Directory inventory", f"{len(visible)} of {len(users)} identities")
                display = visible.copy(); display["Last activity"] = display["last_activity"].dt.strftime("%d %b %Y")
                display = display.rename(columns={"Shown name":"Display name","Shown UPN":"User principal name","job_title":"Job title","department":"Department","account_type":"Type"})
                columns = ["Display name","User principal name","Job title","Department","Type","Lifecycle","MFA","Directory role","Last activity"]
                event = st.dataframe(display[columns], width="stretch", hide_index=True, height=500, key="directory_selection", on_select="rerun", selection_mode="single-row")
                st.caption("Select a row to inspect the identity profile.")
                st.download_button("Export filtered directory", display[columns].to_csv(index=False).encode("utf-8"), "M365_Assurance_Directory.csv", "text/csv", width="stretch")
        with profile_col:
            choices = visible["upn"].tolist() or users["upn"].tolist(); selected_upn = choices[0]
            if event.selection.rows and not visible.empty: selected_upn = visible.iloc[event.selection.rows[0]]["upn"]
            selected_upn = st.selectbox("Identity profile", choices, index=choices.index(selected_upn), format_func=shown, key="identity_profile")
            selected = users[users["upn"] == selected_upn].iloc[0]; selected_name = shown(selected_upn)
            initials = "".join(part[0] for part in selected_name.split()[:2]).upper()
            profile_values = [("User principal name",shown(selected["upn"])),("Identity type",selected["account_type"]),("Lifecycle",selected["Lifecycle"]),("MFA",selected["MFA"]),("Hierarchy",selected["hierarchy_level"]),("Directory role",selected["Directory role"])]
            rows = "".join(f'<div class="key"><span>{h(label)}</span><span>{h(value)}</span></div>' for label, value in profile_values)
            st.markdown(f'<div class="profile"><div class="profile-hero"><div class="avatar">{h(initials)}</div><div class="profile-name">{h(selected_name)}</div><div class="profile-role">{h(selected["job_title"])} · {h(selected["department"])}</div></div><div class="profile-body">{rows}</div></div>', unsafe_allow_html=True)
            with st.container(border=True):
                manager = users[users["upn"] == selected["manager_upn"]]; reports = users[users["manager_upn"] == selected["upn"]]
                panel_title("Access context", "Ownership and reporting relationships")
                context_rows = [("Manager / sponsor",shown(manager.iloc[0]["upn"]) if not manager.empty else "Board / owner"),("Direct reports",len(reports)),("Owned groups",int((groups["owner_upn"] == selected["upn"]).sum())),("Registered devices",int((devices["owner_upn"] == selected["upn"]).sum()))]
                for label, value in context_rows: st.markdown(f'<div class="key"><span>{h(label)}</span><span>{h(value)}</span></div>', unsafe_allow_html=True)

    with signin_view_tab:
        outcome_options, risk_options, app_options = sorted(signins["status"].unique()), sorted(signins["risk_level"].unique()), sorted(signins["application"].unique())
        c1, c2, c3, c4 = st.columns([1,1,1.2,1.4])
        outcome = c1.multiselect("Outcome", outcome_options, default=outcome_options, key="signin_outcome")
        risk = c2.multiselect("Risk", risk_options, default=risk_options, key="signin_risk")
        apps = c3.multiselect("Application", app_options, default=app_options, key="signin_apps")
        signin_query = c4.text_input("Search sign-ins", placeholder="User, IP or location", key="signin_search")
        signin_view = recent_signins[recent_signins["status"].isin(outcome) & recent_signins["risk_level"].isin(risk) & recent_signins["application"].isin(apps)].copy()
        if signin_query: signin_view = signin_view[signin_view.astype(str).apply(lambda row: row.str.contains(signin_query,case=False,regex=False).any(),axis=1)]
        signin_view["User"] = signin_view["upn"].map(shown)
        success_rate = round((signin_view["status"] == "Success").mean() * 100) if len(signin_view) else 0
        risky_count = int(signin_view["risk_level"].isin(["medium","high"]).sum())
        cols = st.columns(4)
        for col, value in zip(cols, [("Sign-ins",len(signin_view),f"Last {reporting_days} days",""),("Success rate",f"{success_rate}%","Selected evidence","good"),("Failed",int((signin_view["status"] == "Failure").sum()),"Authentication failures","warn"),("Medium / high risk",risky_count,"Requires context and review","risk")]):
            with col: metric(*value)
        chart_col, risk_col = st.columns([1.45,1])
        with chart_col:
            with st.container(border=True):
                panel_title("Sign-in outcomes", "Events by application and result")
                grouped = signin_view.groupby(["application","status"],as_index=False).size().rename(columns={"size":"Events"})
                fig = px.bar(grouped, x="application", y="Events", color="status", barmode="group", color_discrete_map={"Success":"#107c10","Failure":"#c50f1f"})
                fig.update_xaxes(title=None,tickangle=-18); fig.update_yaxes(title="Events",dtick=1)
                st.plotly_chart(chart_style(fig,285), width="stretch", config={"displayModeBar":False})
        with risk_col:
            with st.container(border=True):
                panel_title("Risk distribution", "Entra sign-in risk context")
                risk_counts = signin_view["risk_level"].value_counts().rename_axis("Risk").reset_index(name="Events")
                fig = px.pie(risk_counts, names="Risk", values="Events", hole=.65, color="Risk", color_discrete_map={"none":"#98a2b3","low":"#0f6cbd","medium":"#ca5010","high":"#c50f1f"})
                st.plotly_chart(chart_style(fig,285,False), width="stretch", config={"displayModeBar":False})
        signin_table = signin_view.sort_values("timestamp",ascending=False).copy(); signin_table["Timestamp"] = signin_table["timestamp"].dt.strftime("%d %b %Y %H:%M UTC")
        signin_table = signin_table.rename(columns={"application":"Application","location":"Location","ip_address":"IP address","device":"Device","authentication":"Authentication","status":"Outcome","risk_level":"Risk","risk_state":"Risk state"})
        st.dataframe(signin_table[["Timestamp","User","Application","Outcome","Risk","Risk state","Location","IP address","Device","Authentication"]], width="stretch", hide_index=True)
        st.link_button("Microsoft Entra sign-in log guidance", ENTRA_SIGNIN_URL)

    with user_360_tab:
        section("User 360", "A connected view of identity, authentication, licences, devices, groups, activity and recommendations.")
        selected_360 = st.selectbox("Select identity", users["upn"].tolist(), format_func=shown, key="user_360_identity")
        user_360 = TenantDataService.user_360(assessment, selected_360, results)
        identity = user_360["identity"]; auth = user_360["authentication"]; usage_360 = user_360["usage"]
        cols = st.columns(5)
        user_values = [
            ("Identity",shown(selected_360),identity.get("job_title",""),"violet"),
            ("Authentication",auth.get("default_method","Not recorded"),f'{len(auth.get("methods",[]))} method(s)',"good" if auth.get("phishing_resistant") else "warn"),
            ("Licences",len(user_360["licenses"]),", ".join(item.get("sku","") for item in user_360["licenses"]) or "None",""),
            ("Access groups",len(user_360["groups"]),f'{len(user_360["owned_groups"])} owned',""),
            ("Open recommendations",len(user_360["findings"]),"Directly associated findings","risk" if user_360["findings"] else "good"),
        ]
        for column, value in zip(cols, user_values):
            with column: metric(*value)
        left, middle, right = st.columns(3)
        with left:
            with st.container(border=True):
                panel_title("Identity", "Hierarchy and lifecycle")
                manager = shown(user_360["manager"]["upn"]) if user_360["manager"] else "Board / sponsor"
                for label, value in [("Department",identity.get("department")),("Hierarchy",identity.get("hierarchy_level")),("Manager",manager),("Account type",identity.get("account_type")),("Enabled",identity.get("account_enabled")),("Roles",", ".join(identity.get("roles",[])) or "Standard user")]:
                    st.markdown(f'<div class="key"><span>{h(label)}</span><span>{h(value)}</span></div>', unsafe_allow_html=True)
        with middle:
            with st.container(border=True):
                panel_title("Access", "Authentication and governed resources")
                for label, value in [("MFA registered",identity.get("mfa_registered")),("Phishing resistant",auth.get("phishing_resistant",False)),("Devices",len(user_360["devices"])),("Groups",len(user_360["groups"])),("Direct reports",len(user_360["direct_reports"])),("Forwarding",user_360["mailbox"].get("external_forwarding_enabled",False))]:
                    st.markdown(f'<div class="key"><span>{h(label)}</span><span>{h(value)}</span></div>', unsafe_allow_html=True)
        with right:
            with st.container(border=True):
                panel_title("Activity", "Current usage evidence")
                for label, value in [("Teams messages",usage_360.get("teams_messages",0)),("Teams meetings",usage_360.get("teams_meetings",0)),("Call minutes",usage_360.get("teams_calls_minutes",0)),("Emails sent",usage_360.get("emails_sent",0)),("OneDrive GB",usage_360.get("onedrive_storage_gb",0)),("SharePoint actions",usage_360.get("sharepoint_actions",0))]:
                    st.markdown(f'<div class="key"><span>{h(label)}</span><span>{h(value)}</span></div>', unsafe_allow_html=True)
        activity_left, activity_right = st.columns(2)
        with activity_left:
            panel_title("Recent sign-ins", "Identity-specific Entra evidence")
            if user_360["signins"]: st.dataframe(pd.DataFrame(user_360["signins"])[["timestamp","application","status","risk_level","location"]], width="stretch", hide_index=True)
            else: st.info("No sign-in evidence is available for this identity.")
        with activity_right:
            panel_title("Audit activity", "Operations performed by or targeting this identity")
            if user_360["audit_events"]: st.dataframe(pd.DataFrame(user_360["audit_events"])[["timestamp","workload","operation","result","risk"]], width="stretch", hide_index=True)
            else: st.info("No related audit evidence is available for this identity.")

with audit_tab:
    tab_intro("Audit explorer")
    quick_view = st.segmented_control("Quick view", ["All activity","Admin changes","External sharing","High priority"], default="All activity")
    workloads = sorted(recent_audit["workload"].unique()); categories = sorted(recent_audit["category"].unique())
    results_options, risk_values = sorted(recent_audit["result"].unique()), sorted(recent_audit["risk"].unique())
    a1, a2, a3, a4, a5 = st.columns([1.2,1,.9,.9,1.4])
    workload_filter = a1.multiselect("Workload", workloads, default=workloads, key="audit_workload")
    category_filter = a2.multiselect("Activity type", categories, default=categories, key="audit_category")
    result_filter = a3.multiselect("Result", results_options, default=results_options, key="audit_result")
    audit_risk_filter = a4.multiselect("Review state", risk_values, default=risk_values, key="audit_risk")
    audit_query = a5.text_input("Keyword search", placeholder="Operation, user, target or IP", key="audit_query")
    audit_view = recent_audit[recent_audit["workload"].isin(workload_filter) & recent_audit["category"].isin(category_filter) & recent_audit["result"].isin(result_filter) & recent_audit["risk"].isin(audit_risk_filter)].copy()
    if audit_query: audit_view = audit_view[audit_view.astype(str).apply(lambda row: row.str.contains(audit_query,case=False,regex=False).any(),axis=1)]
    if quick_view == "Admin changes": audit_view = audit_view[audit_view["category"] == "Administration"]
    elif quick_view == "External sharing": audit_view = audit_view[audit_view["category"] == "Sharing"]
    elif quick_view == "High priority": audit_view = audit_view[audit_view["risk"].isin(["Review","High"])]
    audit_view["Actor"] = audit_view["actor_upn"].map(shown); audit_view["Target"] = audit_view["target"].map(shown)
    admin_count = int((audit_view["category"] == "Administration").sum()); sharing_count = int((audit_view["category"] == "Sharing").sum()); review_count = int(audit_view["risk"].isin(["Review","High"]).sum())
    cols = st.columns(4)
    for col, value in zip(cols, [("Audit events",len(audit_view),f"Last {reporting_days} days",""),("Admin changes",admin_count,"Configuration and role operations","violet"),("Sharing events",sharing_count,"External and anonymous sharing","warn"),("Needs review",review_count,"Review or high-risk context","risk")]):
        with col: metric(*value)
    timeline_col, operation_col = st.columns([1.4,1])
    with timeline_col:
        with st.container(border=True):
            panel_title("Activity timeline", "Events by date and workload")
            timeline = audit_view.copy(); timeline["Date"] = timeline["timestamp"].dt.floor("D")
            timeline = timeline.groupby(["Date","workload"],as_index=False).size().rename(columns={"size":"Events"})
            fig = px.bar(timeline, x="Date", y="Events", color="workload", color_discrete_sequence=px.colors.qualitative.Safe)
            fig.update_xaxes(title=None); fig.update_yaxes(title="Events",dtick=1)
            st.plotly_chart(chart_style(fig,300), width="stretch", config={"displayModeBar":False})
    with operation_col:
        with st.container(border=True):
            panel_title("Top operations", "Most frequent operations in the filtered view")
            operations = audit_view["operation"].value_counts().head(8).rename_axis("Operation").reset_index(name="Events")
            fig = px.bar(operations.sort_values("Events"), y="Operation", x="Events", orientation="h", text="Events", color_discrete_sequence=["#0f6cbd"])
            fig.update_yaxes(title=None); fig.update_xaxes(title="Events",dtick=1); fig.update_traces(textposition="outside")
            st.plotly_chart(chart_style(fig,300,False), width="stretch", config={"displayModeBar":False})
    audit_table = audit_view.sort_values("timestamp",ascending=False).copy(); audit_table["Timestamp"] = audit_table["timestamp"].dt.strftime("%d %b %Y %H:%M UTC")
    audit_table = audit_table.rename(columns={"workload":"Workload","operation":"Operation","category":"Activity type","result":"Result","ip_address":"IP address","risk":"Review state","details":"Details"})
    columns = ["Timestamp","Actor","Workload","Operation","Activity type","Target","Result","Review state","IP address"]
    event = st.dataframe(audit_table[columns], width="stretch", hide_index=True, height=420, key="audit_selection", on_select="rerun", selection_mode="single-row")
    if event.selection.rows:
        selected_event = audit_table.iloc[event.selection.rows[0]]
        callout_style = "risk" if selected_event["Review state"] == "High" else "warn" if selected_event["Review state"] == "Review" else "neutral"
        st.markdown(f'<div class="callout {callout_style}"><strong>{h(selected_event["Operation"])} · {h(selected_event["Actor"])}</strong>{h(selected_event["Details"])}<br>Target: {h(selected_event["Target"])} · IP: {h(selected_event["IP address"])}</div>', unsafe_allow_html=True)
        bookmark_note = st.text_input("Bookmark note", placeholder="Why this evidence requires follow-up", key="audit_bookmark_note")
        if st.button("Bookmark selected event"):
            store.bookmark_event(selected_event["event_id"],bookmark_note,assessor); st.success("Event bookmarked for assessment review.")
    export_columns = columns + ["Details"]
    st.download_button("Export filtered audit results", audit_table[export_columns].to_csv(index=False).encode("utf-8"), "M365_Assurance_Audit.csv", "text/csv")
    save_left, save_right = st.columns([1,2])
    search_name = save_left.text_input("Saved search name",placeholder="e.g. Weekly admin review",key="saved_search_name")
    if save_left.button("Save current search"):
        try:
            store.save_audit_search(search_name,{"workloads":workload_filter,"categories":category_filter,"results":result_filter,"risk":audit_risk_filter,"query":audit_query,"quick_view":quick_view},assessor); st.success("Audit search saved.")
        except ValueError as error: st.warning(str(error))
    with save_right:
        saved_searches, bookmarks = store.saved_audit_searches(), store.audit_bookmarks()
        panel_title("Assessment evidence workspace", "Reusable searches and preserved suspicious-event evidence")
        st.write(f"**{len(saved_searches)}** saved searches · **{len(bookmarks)}** bookmarks")
    if correlated_stories:
        with st.expander("Correlated assessment evidence"):
            story_rows = [{"Identity":shown(item["upn"]),"Risk":item["risk"],"Summary":item["summary"],"Related events":len(item["related_events"])} for item in correlated_stories]
            st.dataframe(pd.DataFrame(story_rows),width="stretch",hide_index=True)
    with st.expander("How this maps to Microsoft Purview Audit"):
        st.markdown("The explorer demonstrates filters commonly used in Purview: date/time, user, operation, workload, result, target and keyword. Production access requires appropriate Audit roles; retention and available records depend on licensing and workload.")
        st.link_button("Open official audit search guidance", PURVIEW_AUDIT_URL)


with governance_tab:
    tab_intro("Access governance")
    hierarchy = pd.DataFrame([{"Tenant":"M365 Assurance","Department":row.department,"Person":shown(row.upn),"Job title":row.job_title,"Hierarchy":row.hierarchy_level} for row in users[users["account_enabled"]].itertuples()])
    tree = px.sunburst(hierarchy, path=["Tenant","Department","Person"], color="Department", hover_data=["Job title","Hierarchy"], color_discrete_sequence=["#0f6cbd","#6b4eff","#107c10","#ca5010","#0891b2","#475467"])
    privileged = users[users["roles"].apply(lambda roles: bool(AssessmentEngine.PRIVILEGED_ROLES.intersection(roles)))]
    left, right = st.columns([1.45,1])
    with left:
        with st.container(border=True):
            panel_title("Business hierarchy", "Explore reporting structure and identity classification")
            st.plotly_chart(chart_style(tree,455,False), width="stretch", config={"displayModeBar":False})
    with right:
        with st.container(border=True):
            panel_title("Privileged access register", "Administrative roles and MFA protection")
            for _, user in privileged.iterrows():
                mfa = "Pass" if user["mfa_registered"] else "Action required"
                st.markdown(f'<div class="priority {"High" if user["mfa_registered"] else "Critical"}"><span class="priority-dot"></span><div><div class="priority-name">{h(shown(user["upn"]))}</div><div class="priority-meta">{h(user["Directory role"])} · {h(user["job_title"])}</div></div><div>{status_badge(mfa)}</div></div>', unsafe_allow_html=True)
            st.markdown('<div class="callout"><strong>Governance principle</strong>Business seniority does not automatically justify tenant privilege. Review role need, MFA and emergency access separately.</div>', unsafe_allow_html=True)
    section("Group governance", "Ownership, guest membership, sensitivity and access-review status.")
    group_view = groups.copy(); group_view["Owner"] = group_view["owner_upn"].map(shown)
    group_view = group_view.rename(columns={"display_name":"Group","group_type":"Type","member_count":"Members","guest_count":"Guests","sensitivity":"Sensitivity","last_review":"Last review","review_status":"Review status"})
    st.dataframe(group_view[["Group","Type","Owner","Members","Guests","Sensitivity","Last review","Review status"]], width="stretch", hide_index=True)
    selected_group = st.selectbox("Inspect group", group_view["Group"].tolist(), key="group_inspector")
    group_row = group_view[group_view["Group"] == selected_group].iloc[0]
    cols = st.columns(4)
    group_values = [("Owner",group_row["Owner"],"Accountable identity",""),("Membership",f'{group_row["Members"]} / {group_row["Guests"]}',"Members / guests",""),("Sensitivity",group_row["Sensitivity"],"Information classification","violet"),("Review status",group_row["Review status"],str(group_row["Last review"]),"warn" if group_row["Review status"] == "Overdue" else "good")]
    for col, value in zip(cols, group_values):
        with col: metric(*value)
    section("Enterprise applications", "Consent risk, assignment and review ownership.")
    st.dataframe(applications.rename(columns={"display_name":"Application","publisher":"Publisher","assignment":"Assignment","owner":"Owner","consent_risk":"Consent risk","last_review":"Last review"})[["Application","Publisher","Assignment","Owner","Consent risk","Last review"]], width="stretch", hide_index=True)
    governance_left, governance_right = st.columns(2)
    with governance_left:
        with st.expander("Conditional Access policies"):
            ca_view = conditional_access.rename(columns={"display_name":"Policy","state":"State","coverage":"Coverage","grant_controls":"Grant controls","last_review":"Last review"})
            st.dataframe(ca_view[["Policy","State","Coverage","Grant controls","Last review"]],width="stretch",hide_index=True)
    with governance_right:
        with st.expander("External sharing links"):
            share_view = sharing_links.copy(); share_view["Owner"] = share_view["owner_upn"].map(shown)
            share_view = share_view.rename(columns={"resource":"Resource","link_type":"Link type","external":"External","expires_at":"Expires","status":"Status"})
            st.dataframe(share_view[["Resource","Link type","External","Owner","Expires","Status"]],width="stretch",hide_index=True)

with posture_tab:
    tab_intro("Security posture")
    cols = st.columns(5)
    values = [("Posture score",f"{summary['posture_score']}/100",summary["maturity"],"violet"),("Pass",summary["controls_passed"],"Control requirements met","good"),("Action required",summary["controls_action_required"],"Confirmed gaps","risk"),("Review",summary["controls_review"],"Needs business context","warn"),("Not assessed",summary["controls_not_assessed"],"Evidence unavailable","")]
    for col, value in zip(cols, values):
        with col: metric(*value)
    f1, f2, f3 = st.columns([1,1,1.3])
    control_categories = sorted({item["category"] for item in results}); severities = ["Critical","High","Medium","Low"]
    selected_categories = f1.multiselect("Category", control_categories, default=control_categories, key="control_category")
    selected_severities = f2.multiselect("Severity", severities, default=severities, key="control_severity")
    control_query = f3.text_input("Search controls", placeholder="Control, finding or recommendation", key="control_search")
    visible_results = [item for item in results if item["category"] in selected_categories and item["severity"] in selected_severities and (show_passed or item["status"] != "Pass")]
    if control_query: visible_results = [item for item in visible_results if control_query.lower() in " ".join(str(value) for value in item.values()).lower()]
    section("Control assessment", f"Showing {len(visible_results)} of {len(results)} controls.")
    for item in visible_results:
        st.markdown(f'<div class="control-card"><div class="control-top"><div><div class="control-id">{h(item["control_id"])} · {h(item["category"])}</div><div class="control-name">{h(item["control_name"])}</div></div>{status_badge(item["status"])}</div><div class="control-finding">{h(item["finding"])}</div><div class="control-footer"><div><div class="mini-label">Business impact</div><div class="mini-value">{h(item["business_impact"])}</div></div><div><div class="mini-label">Risk / affected</div><div class="mini-value">{h(item["severity"])} · {item["affected_count"]}</div></div><div><div class="mini-label">Target</div><div class="mini-value">{h(item["target_timeframe"])}</div></div></div></div>', unsafe_allow_html=True)
        with st.expander(f"Evidence and recommendation · {item['control_id']}"):
            e1, e2 = st.columns(2)
            with e1:
                st.markdown("**Observed evidence**"); st.json(item["evidence"])
                if item["affected_entities"]: st.write("Affected:", [shown(entity) for entity in item["affected_entities"]])
            with e2:
                st.markdown("**Recommended action**"); st.write(item["recommendation"])
                st.write(f"**Owner:** {item['remediation_owner']}  "); st.write(f"**Target:** {item['target_timeframe']}")
                st.write(f"**Expected effort:** {item['expected_effort']}")
                st.markdown("**Implementation steps**")
                for step in item["implementation_steps"]: st.write(f"- {step}")
                st.markdown("**Validation steps**")
                for step in item["validation_steps"]: st.write(f"- {step}")
                if item["licensing_note"]: st.caption(item["licensing_note"])
                st.link_button("Open Microsoft guidance", item["source_url"])
    with st.expander("How the score works"):
        st.markdown("Pass receives the full control weight, Review receives half, and Action required receives zero. Not-assessed controls are excluded. The score is a prioritisation aid, not Microsoft Secure Score and not a certification.")


with actions_tab:
    tab_intro("Actions & reports")
    plan_view, report_view, history_view = st.tabs(["Improvement plan","Client report","History & notes"])
    with plan_view:
        cols = st.columns(4)
        action_values = [("Open actions",len(open_results),"Control gaps and reviews","risk"),("Completed",completed_actions,"Recorded in the action register","good"),("Delivery progress",f"{remediation_progress}%","Completion does not alter evidence","violet"),("Unassigned",sum(not action_map.get(item["control_id"],{}).get("owner") for item in open_results),"Default owners shown below","warn")]
        for col, value in zip(cols, action_values):
            with col: metric(*value)
        st.markdown('<div class="callout neutral"><strong>Delivery rule</strong>Marking an action completed records project progress. The posture score changes only when the underlying tenant evidence is reassessed.</div>', unsafe_allow_html=True)
        section("Remediation register", "Select an action, assign an accountable owner and record a target date and decision note.")
        if open_results:
            labels = {f'{item["control_id"]} · {item["control_name"]}':item for item in open_results}
            chosen_label = st.selectbox("Assessment action", list(labels), key="action_control"); chosen = labels[chosen_label]
            existing = action_map.get(chosen["control_id"],{})
            f1, f2, f3 = st.columns([1,1.3,1])
            statuses = ["Not started","Planned","In progress","Blocked","Completed","Accepted exception"]
            current_status = existing.get("status","Not started")
            action_status = f1.selectbox("Delivery status", statuses, index=statuses.index(current_status), key=f'status_{chosen["control_id"]}')
            owner = f2.text_input("Accountable owner", value=existing.get("owner",chosen["remediation_owner"]), key=f'owner_{chosen["control_id"]}')
            default_due = pd.to_datetime(existing.get("due_date"),errors="coerce")
            default_due_value = date.today() + timedelta(days=30) if pd.isna(default_due) else default_due.date()
            due = f3.date_input("Target date", value=default_due_value, key=f'due_{chosen["control_id"]}')
            note = st.text_area("Decision / implementation note", value=existing.get("note",""), placeholder="Record scope, dependency, exception or next evidence required.", key=f'note_{chosen["control_id"]}')
            st.markdown(f'<div class="callout"><strong>{h(chosen["finding"])}</strong>{h(chosen["recommendation"])}</div>', unsafe_allow_html=True)
            if st.button("Save action", type="primary"):
                try:
                    store.save_remediation_action(chosen["control_id"],chosen["control_name"],action_status,owner,due,note); st.success("Remediation action saved. Refresh or select another action to continue.")
                except ValueError as error: st.warning(str(error))
        refreshed_actions = store.remediation_actions()
        if refreshed_actions:
            action_df = pd.DataFrame(refreshed_actions).rename(columns={"control_id":"Control","control_name":"Action","status":"Status","owner":"Owner","due_date":"Target date","note":"Decision / note","updated_at":"Updated (UTC)"})
            st.dataframe(action_df[["Control","Action","Status","Owner","Target date","Decision / note","Updated (UTC)"]], width="stretch", hide_index=True)

    with report_view:
        section("Client deliverables", "Export a self-contained report or the current evidence tables.")
        a, b, c = st.columns(3)
        with a:
            with st.container(border=True):
                panel_title("Assessment report", "Executive summary, priorities, usage context and full controls")
                st.download_button("Download HTML report", report_html.encode("utf-8"), "M365_Assurance_Report.html", "text/html", width="stretch", type="primary")
        with b:
            with st.container(border=True):
                panel_title("Control register", "Complete control outcomes and recommendations")
                control_export = pd.DataFrame(report_assessment["results"])
                st.download_button("Download control CSV", control_export.to_csv(index=False).encode("utf-8"), "M365_Assurance_Controls.csv", "text/csv", width="stretch")
        with c:
            with st.container(border=True):
                panel_title("Audit evidence", "Current filtered audit view")
                st.download_button("Download audit CSV", audit_table[export_columns].to_csv(index=False).encode("utf-8"), "M365_Assurance_Audit.csv", "text/csv", width="stretch")
        section("Save assessment snapshot", "Preserve a point-in-time score and its control evidence in SQLite.")
        snapshot = st.columns([1.4,1])
        with snapshot[0]:
            with st.container(border=True):
                for label, value in [("Primary domain",tenant["primary_domain"]),("Scenario",scenario),("Posture score",f"{summary['posture_score']}/100"),("Prepared by",assessor),("Privacy","Concealed" if conceal_names else "Identifiable synthetic names")]:
                    st.markdown(f'<div class="key"><span>{h(label)}</span><span>{h(value)}</span></div>', unsafe_allow_html=True)
        with snapshot[1]:
            st.markdown("Save only when the assessment context is correct. A snapshot preserves the control result history; it does not collect live Microsoft 365 data.")
            if st.button("Save assessment snapshot", type="primary", width="stretch"):
                run_id = store.save_assessment(report_assessment,assessor=assessor); st.success(f"Assessment snapshot #{run_id} saved.")
        st.markdown('<div class="callout"><strong>Client delivery boundary</strong>This demonstration uses synthetic evidence. A live engagement requires written authorisation, approved read-only collection, least-privilege access and tenant-specific validation.</div>', unsafe_allow_html=True)

    with history_view:
        history = store.assessment_history()
        section("Assessment history", "Repeated snapshots demonstrate posture movement without changing source evidence silently.")
        if history:
            history_df = pd.DataFrame(history).rename(columns={"id":"Run","scenario":"Scenario","assessed_at":"Assessed (UTC)","posture_score":"Score","controls_passed":"Passed","controls_action_required":"Action required","controls_review":"Review","assessor":"Assessor"})
            st.dataframe(history_df[["Run","Scenario","Assessed (UTC)","Score","Passed","Action required","Review","Assessor"]], width="stretch", hide_index=True)
            trend = history_df.copy(); trend["Assessed (UTC)"] = pd.to_datetime(trend["Assessed (UTC)"],utc=True,errors="coerce"); trend = trend.dropna(subset=["Assessed (UTC)"]).sort_values("Assessed (UTC)")
            if len(trend) > 1:
                fig = px.line(trend, x="Assessed (UTC)", y="Score", color="Scenario", markers=True, range_y=[0,100])
                st.plotly_chart(chart_style(fig,270), width="stretch", config={"displayModeBar":False})
        else: st.info("No assessment snapshots have been saved yet.")
        section("Review note", "Record an accepted risk, decision, exception or follow-up.")
        n1, n2 = st.columns([1,2])
        reviewer = n1.text_input("Reviewer", value=assessor, key="reviewer")
        review_note = n2.text_area("Decision / note", placeholder="Record the decision, accountable person and next review point.", key="review_note")
        if st.button("Save review note"):
            try:
                store.add_note(review_note,author=reviewer); st.success("Review note saved.")
            except ValueError as error: st.warning(str(error))
        notes = store.notes()
        if notes:
            note_df = pd.DataFrame(notes).rename(columns={"created_at":"Created (UTC)","author":"Reviewer","note":"Decision / note"})
            st.dataframe(note_df[["Created (UTC)","Reviewer","Decision / note"]], width="stretch", hide_index=True)

st.markdown(f'<div class="footer-note">M365 Assurance {h(APP_VERSION)} · Synthetic Microsoft 365, Purview and Entra evidence · Assessment and management reporting product; not a SOC, penetration test, Microsoft certification or guarantee of security.</div>', unsafe_allow_html=True)
