from pathlib import Path

APP_NAME = "M365 Assurance"
APP_SUBTITLE = "Microsoft 365 Assurance, Usage & Governance"
APP_VERSION = "4.2.0"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = BASE_DIR / "database"
CONTROLS_PATH = DATA_DIR / "assessment_controls.json"
TENANT_PATH = DATA_DIR / "synthetic_tenant.json"
DB_PATH = DATABASE_DIR / "assessment_history.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

STALE_ACCOUNT_DAYS = 90
STATUS_ORDER = {"Action required": 0, "Review": 1, "Pass": 2, "Not assessed": 3}
SEVERITY_POINTS = {"Critical": 5, "High": 4, "Medium": 2, "Low": 1}
