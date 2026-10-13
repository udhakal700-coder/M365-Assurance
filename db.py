import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from config import DB_PATH


class AssessmentStore:
    """Versioned SQLite repository for assessment workflow and review state."""

    WORKFLOW_STAGES = (
        "Draft",
        "Evidence collected",
        "Assessed",
        "Client review",
        "Remediation",
        "Reassessment",
        "Closed",
    )

    def __init__(self, db_path=None):
        self.db_path = Path(db_path or DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialise()

    def connect(self):
        connection = sqlite3.connect(self.db_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @staticmethod
    def now():
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _initialise(self):
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS assessment_cases (
                    case_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    scope TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS assessment_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_name TEXT NOT NULL,
                    tenant_domain TEXT NOT NULL,
                    scenario TEXT NOT NULL,
                    assessed_at TEXT NOT NULL,
                    posture_score INTEGER NOT NULL CHECK(posture_score BETWEEN 0 AND 100),
                    controls_passed INTEGER NOT NULL,
                    controls_action_required INTEGER NOT NULL,
                    controls_review INTEGER NOT NULL,
                    summary_json TEXT NOT NULL,
                    assessor TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS control_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    control_id TEXT NOT NULL,
                    control_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    affected_count INTEGER NOT NULL,
                    evidence_json TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES assessment_runs(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS review_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER,
                    created_at TEXT NOT NULL,
                    author TEXT NOT NULL,
                    note TEXT NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES assessment_runs(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS remediation_actions (
                    control_id TEXT PRIMARY KEY,
                    control_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    due_date TEXT,
                    note TEXT,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS saved_audit_searches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    filters_json TEXT NOT NULL,
                    created_by TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_bookmarks (
                    event_id TEXT PRIMARY KEY,
                    note TEXT,
                    bookmarked_by TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS evidence_imports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_name TEXT NOT NULL,
                    schema_version INTEGER,
                    record_count INTEGER NOT NULL,
                    validation_status TEXT NOT NULL,
                    validation_json TEXT NOT NULL,
                    imported_by TEXT NOT NULL,
                    imported_at TEXT NOT NULL
                );
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                (2, self.now()),
            )

    def database_health(self):
        with self.connect() as connection:
            integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
            tables = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
            version = connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0]
        return {
            "status": "Healthy" if integrity == "ok" else "Review",
            "integrity": integrity,
            "schema_version": version or 1,
            "tables": [row[0] for row in tables],
            "database_path": str(self.db_path),
        }

    def save_case(self, case_id, name, stage, owner, scope=""):
        if stage not in self.WORKFLOW_STAGES:
            raise ValueError("Unsupported assessment stage")
        clean_id = str(case_id).strip()
        clean_name = str(name).strip()
        clean_owner = str(owner).strip()
        if not clean_id or not clean_name or not clean_owner:
            raise ValueError("Case ID, name and owner are required")
        now = self.now()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO assessment_cases(case_id, name, stage, owner, scope, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(case_id) DO UPDATE SET
                    name=excluded.name, stage=excluded.stage, owner=excluded.owner,
                    scope=excluded.scope, updated_at=excluded.updated_at
                """,
                (clean_id, clean_name, stage, clean_owner, str(scope).strip(), now, now),
            )
        return clean_id

    def assessment_cases(self):
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM assessment_cases ORDER BY datetime(updated_at) DESC, case_id"
            ).fetchall()
        return [dict(row) for row in rows]

    def save_audit_search(self, name, filters, created_by="M365 Assurance Consultant"):
        clean_name = str(name).strip()
        if not clean_name:
            raise ValueError("Search name is required")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO saved_audit_searches(name, filters_json, created_by, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    filters_json=excluded.filters_json,
                    created_by=excluded.created_by,
                    created_at=excluded.created_at
                """,
                (clean_name, json.dumps(filters, sort_keys=True), str(created_by).strip(), self.now()),
            )

    def saved_audit_searches(self):
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM saved_audit_searches ORDER BY name").fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item["filters"] = json.loads(item.pop("filters_json"))
            results.append(item)
        return results

    def bookmark_event(self, event_id, note="", bookmarked_by="M365 Assurance Consultant"):
        clean_id = str(event_id).strip()
        if not clean_id:
            raise ValueError("Event ID is required")
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_bookmarks(event_id, note, bookmarked_by, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(event_id) DO UPDATE SET
                    note=excluded.note, bookmarked_by=excluded.bookmarked_by,
                    created_at=excluded.created_at
                """,
                (clean_id, str(note).strip(), str(bookmarked_by).strip(), self.now()),
            )

    def remove_bookmark(self, event_id):
        with self.connect() as connection:
            connection.execute("DELETE FROM audit_bookmarks WHERE event_id=?", (str(event_id),))

    def audit_bookmarks(self):
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM audit_bookmarks ORDER BY datetime(created_at) DESC").fetchall()
        return [dict(row) for row in rows]

    def record_evidence_import(self, source_name, schema_version, record_count, validation_status, validation, imported_by):
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO evidence_imports(
                    source_name, schema_version, record_count, validation_status,
                    validation_json, imported_by, imported_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(source_name), int(schema_version), int(record_count), str(validation_status),
                    json.dumps(validation, sort_keys=True), str(imported_by).strip(), self.now(),
                ),
            )
        return cursor.lastrowid

    def evidence_imports(self, limit=50):
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM evidence_imports ORDER BY datetime(imported_at) DESC LIMIT ?", (int(limit),)
            ).fetchall()
        return [dict(row) for row in rows]

    def save_assessment(self, assessment, assessor="M365 Assurance Consultant"):
        summary = assessment["summary"]
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO assessment_runs (
                    tenant_name, tenant_domain, scenario, assessed_at, posture_score,
                    controls_passed, controls_action_required, controls_review,
                    summary_json, assessor
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    assessment["tenant"].get("primary_domain", "M365 Assurance"),
                    assessment["tenant"]["primary_domain"],
                    assessment["scenario"],
                    self.now(),
                    summary["posture_score"],
                    summary["controls_passed"],
                    summary["controls_action_required"],
                    summary["controls_review"],
                    json.dumps(summary),
                    assessor.strip() or "M365 Assurance Consultant",
                ),
            )
            run_id = cursor.lastrowid
            connection.executemany(
                """
                INSERT INTO control_results (
                    run_id, control_id, control_name, category, status, severity,
                    affected_count, evidence_json, recommendation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id, result["control_id"], result["control_name"],
                        result["category"], result["status"], result["severity"],
                        result["affected_count"], json.dumps(result["evidence"]),
                        result["recommendation"],
                    )
                    for result in assessment["results"]
                ],
            )
        return run_id

    def assessment_history(self, limit=50):
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM assessment_runs ORDER BY datetime(assessed_at) DESC LIMIT ?",
                (int(limit),),
            ).fetchall()
        return [dict(row) for row in rows]

    def control_results(self, run_id):
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM control_results WHERE run_id=? ORDER BY id", (int(run_id),)
            ).fetchall()
        return [dict(row) for row in rows]

    def add_note(self, note, author="Client reviewer", run_id=None):
        clean_note = str(note).strip()
        if not clean_note:
            raise ValueError("Review note cannot be empty")
        with self.connect() as connection:
            connection.execute(
                "INSERT INTO review_notes(run_id, created_at, author, note) VALUES (?, ?, ?, ?)",
                (run_id, self.now(), str(author).strip() or "Client reviewer", clean_note),
            )

    def notes(self, limit=100):
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM review_notes ORDER BY datetime(created_at) DESC LIMIT ?", (int(limit),)
            ).fetchall()
        return [dict(row) for row in rows]

    def remediation_actions(self):
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM remediation_actions
                ORDER BY
                    CASE status
                        WHEN 'Blocked' THEN 1
                        WHEN 'In progress' THEN 2
                        WHEN 'Planned' THEN 3
                        WHEN 'Not started' THEN 4
                        WHEN 'Completed' THEN 5
                        ELSE 6
                    END,
                    control_id
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def save_remediation_action(
        self,
        control_id,
        control_name,
        status,
        owner,
        due_date=None,
        note="",
    ):
        allowed_statuses = {
            "Not started",
            "Planned",
            "In progress",
            "Blocked",
            "Completed",
            "Accepted exception",
        }
        if status not in allowed_statuses:
            raise ValueError("Unsupported remediation status")
        clean_owner = str(owner).strip()
        if not clean_owner:
            raise ValueError("Remediation owner is required")

        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO remediation_actions (
                    control_id, control_name, status, owner,
                    due_date, note, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(control_id) DO UPDATE SET
                    control_name = excluded.control_name,
                    status = excluded.status,
                    owner = excluded.owner,
                    due_date = excluded.due_date,
                    note = excluded.note,
                    updated_at = excluded.updated_at
                """,
                (
                    str(control_id),
                    str(control_name),
                    status,
                    clean_owner,
                    str(due_date) if due_date else None,
                    str(note).strip(),
                    self.now(),
                ),
            )
