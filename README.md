# M365 Assurance

**Microsoft 365 Assurance, Usage & Governance for SMEs**

M365 Assurance is a client-facing product that combines Microsoft 365 usage and adoption, Purview-style audit exploration, Entra ID identity and sign-in analysis, security posture assessment, access governance and remediation tracking. The supplied tenant evidence is synthetic.

This is an **assessment and advisory product**. It is not a SOC, SIEM, penetration test, managed detection service, Microsoft certification or guarantee of security.

This dashboard format while strengthening the product underneath it. Purposeful Review details controls now open polished in-app dialogs without reloading the page or changing the selected view. The release also includes schema-version-2 evidence validation, User 360, workload deep dives, saved audit searches, evidence bookmarks, correlated assessment evidence, Conditional Access and sharing-link registers, professional implementation/validation steps, and documented risk acceptance.

## Product experience

The interface is organized into seven visible, interactive client tabs:

1. **Executive overview** — posture, active users, adoption, licence efficiency, priorities and integrated evidence coverage.
2. **Usage & adoption** — reporting-period selection, workload adoption, weekly trends, storage, licence efficiency, privacy masking, search and CSV export.
3. **Identity & sign-ins** — MFA and lifecycle analysis, searchable directory profiles, devices, sign-in outcomes and risk context.
4. **Audit explorer** — Purview-style workload, activity, result, risk and keyword filters with event inspection and export.
5. **Access governance** — business hierarchy, administrator register, group inspection and enterprise application ownership.
6. **Security posture** — filterable Microsoft-aligned control matrix, evidence, business impact and recommendations.
7. **Actions & reports** — persisted action ownership, due dates, report export, snapshots, trend history and review notes.

## Demonstration data

- 17 named directory identities across seven internal departments.
- Executive, manager, staff, specialist, administrator, contractor and external-guest classifications.
- Business managers and Microsoft Entra administrator roles kept as separate concepts.
- Six Microsoft 365/security groups with ownership and review status.
- Three illustrative licence SKUs.
- Eight registered devices with compliance and management state.
- Four enterprise applications with owners and consent-risk context.
- Mailbox-forwarding and sign-in evidence.
- Sixteen per-user usage records, thirteen weekly adoption points and service-capacity evidence.
- Twenty-two cross-workload audit records for file, email, sharing, permission and administrative activity.
- Current, elevated-exposure and target-state scenarios.
- Thirteen Microsoft-aligned assessment controls.

## Project structure

```text
m365_assurance/
├── app.py                         Streamlit product interface
├── engine.py                      Assessment logic and weighted scoring
├── db.py                          SQLite history, notes and action tracking
├── reports.py                     Printable client HTML assurance report
├── config.py                      Paths and product settings
├── requirements.txt               Python dependencies
├── setup_windows.ps1              One-time Windows setup
├── run_windows.ps1                PowerShell launcher
├── start_windows.bat              Double-click launcher after setup
├── .vscode/                       VS Code run and test profiles
├── .streamlit/                    Microsoft-inspired application theme
├── data/
│   ├── synthetic_tenant.json      Usage, audit, identity, access and configuration evidence
│   └── assessment_controls.json   Assessment controls and Microsoft sources
├── services/
│   └── scenarios.py               Demonstration scenarios
├── database/                      Auto-created SQLite evidence store
└── tests/                         Automated validation
```

## Run in VS Code on Windows

### Prerequisites

- Windows 10 or 11
- Python 3.12 or newer
- Visual Studio Code
- Microsoft Python extension for VS Code

The setup script now works with either the Windows `py` launcher or the `python` command. Python 3.12 or 3.13 is preferred; Python 3.14 can work when compatible package builds are available.

### Recommended setup

Open the extracted project folder in VS Code. Then open **Terminal → New Terminal** and run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\setup_windows.ps1
.\run_windows.ps1
```

After the one-time setup, you can also double-click `start_windows.bat`.

### Manual setup without the `py` launcher

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

Open `http://localhost:8501` if the browser does not open automatically. Stop the application with `Ctrl+C` in the terminal.

Do not run `python engine.py` to start the product. `engine.py` contains assessment logic; `app.py` is the Streamlit entry point.

## Run from VS Code

Open **Run and Debug**, then select:

- `Run M365 Assurance`
- `Run automated tests`

You can also use **Terminal → Run Task**:

- `M365 Assurance: Setup`
- `M365 Assurance: Test`
- `M365 Assurance: Run`

## Host on Streamlit Community Cloud

The repository is prepared for Streamlit Community Cloud with pinned dependencies, root-level `app.py`, `.streamlit/config.toml`, secrets protection and a GitHub Actions quality workflow.

See [DEPLOY_STREAMLIT.md](DEPLOY_STREAMLIT.md) for the exact GitHub and Streamlit deployment procedure. Select Python 3.12, branch `main` and entrypoint `app.py`.

Community Cloud is appropriate for this synthetic demonstration. Its local filesystem is not a durable multi-user data store, so production client action/history data should use an authenticated managed database rather than the included SQLite demonstration store.

## Assessment method

Each control receives one outcome:

- **Pass** — supplied evidence meets the assessment criterion.
- **Action required** — supplied evidence shows a configuration gap.
- **Review** — analyst or business validation is required.
- **Not assessed** — the dataset does not contain sufficient evidence.

The weighted score gives full control weight to `Pass`, half weight to `Review`, and zero weight to `Action required`. `Not assessed` controls are excluded from the denominator. Category scores use the same transparent method.

The separate identity-health index combines MFA coverage, account activity and device compliance for executive presentation. It is not a Microsoft Secure Score calculation.

## Client delivery workflow

1. Confirm written authorization, stakeholders, scope and evidence-retention expectations.
2. Collect approved read-only evidence using least-privileged access.
3. Validate the imported evidence and record unavailable or excluded sources.
4. Run the assessment and have a qualified consultant review every open item.
5. Present the executive dashboard, detailed findings and phased remediation roadmap.
6. Export the client report and evidence pack.
7. Record decisions, approved exceptions and owners.
8. Reassess after remediation and compare point-in-time snapshots.

## Production boundary

Before adapting this demonstration for real clients:

- replace the synthetic JSON adapter with an authorized, read-only Microsoft Graph evidence collector;
- use delegated or application permissions that match the approved scope;
- never place client secrets in source code or JSON files;
- encrypt client data at rest and in transit;
- implement tenant isolation, authentication, authorization, audit trails and retention controls;
- validate licensing, emergency access and production dependencies before recommending changes; and
- obtain professional review before delivering findings.

The included Microsoft links are assessment references. Always verify current Microsoft documentation and licensing before a live engagement.
