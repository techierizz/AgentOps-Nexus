"""
AgentOps Nexus — Persistent State Layer

SQLite-backed storage for runs, agent outputs, and execution logs.
Replaces in-memory-only state management with durable persistence.
"""
import sqlite3
import json
import os
import datetime
import threading
from typing import Dict, Any, Optional, List


class PersistenceLayer:
    """
    Thread-safe SQLite persistence for execution runs.
    Each run gets a row with its full agent state stored as JSON.
    Agent outputs and logs are stored in separate tables for queryability.
    """

    def __init__(self, db_path: str):
        self._db_path = db_path
        self._local = threading.local()
        self._init_schema()

    def _get_conn(self) -> sqlite3.Connection:
        """Thread-local connection — SQLite connections are NOT thread-safe."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
            self._local.conn = sqlite3.connect(self._db_path)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def _init_schema(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                issue_id TEXT NOT NULL,
                issue_title TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'init',
                current_state TEXT NOT NULL DEFAULT 'init',
                state_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS agent_outputs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                input_snapshot TEXT,
                output_snapshot TEXT,
                duration_ms REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );

            CREATE TABLE IF NOT EXISTS execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                agent TEXT NOT NULL,
                message TEXT NOT NULL,
                log_type TEXT NOT NULL DEFAULT 'info',
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );

            CREATE TABLE IF NOT EXISTS state_transitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                from_state TEXT NOT NULL,
                to_state TEXT NOT NULL,
                condition TEXT,
                timestamp TEXT NOT NULL,
                duration_ms REAL,
                error TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            );

            CREATE INDEX IF NOT EXISTS idx_agent_outputs_run ON agent_outputs(run_id);
            CREATE INDEX IF NOT EXISTS idx_execution_logs_run ON execution_logs(run_id);
            CREATE INDEX IF NOT EXISTS idx_state_transitions_run ON state_transitions(run_id);
        """)
        conn.commit()

    # ── Run CRUD ──────────────────────────────────────────────

    def create_run(self, run_id: str, issue_id: str, issue_title: str, initial_state: Dict[str, Any]) -> None:
        now = datetime.datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute(
            "INSERT OR REPLACE INTO runs (run_id, issue_id, issue_title, status, current_state, state_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (run_id, issue_id, issue_title, "init", "init", json.dumps(initial_state, default=str), now, now)
        )
        conn.commit()

    def update_run_state(self, run_id: str, state: Dict[str, Any], current_sm_state: str) -> None:
        now = datetime.datetime.now().isoformat()
        status = state.get("status", "running")
        conn = self._get_conn()
        completed_at = now if status in ("completed", "failed") else None
        conn.execute(
            "UPDATE runs SET state_json=?, status=?, current_state=?, updated_at=?, completed_at=COALESCE(?, completed_at) WHERE run_id=?",
            (json.dumps(state, default=str), status, current_sm_state, now, completed_at, run_id)
        )
        conn.commit()

    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row:
            result = dict(row)
            result["state_json"] = json.loads(result["state_json"])
            return result
        return None

    def get_all_runs(self) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute("SELECT run_id, issue_id, issue_title, status, current_state, created_at, updated_at, completed_at FROM runs ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    # ── Agent Outputs ─────────────────────────────────────────

    def record_agent_output(
        self, run_id: str, agent_name: str,
        input_snapshot: Optional[Dict] = None,
        output_snapshot: Optional[Dict] = None,
        duration_ms: Optional[float] = None
    ) -> None:
        now = datetime.datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO agent_outputs (run_id, agent_name, input_snapshot, output_snapshot, duration_ms, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                run_id, agent_name,
                json.dumps(input_snapshot, default=str) if input_snapshot else None,
                json.dumps(output_snapshot, default=str) if output_snapshot else None,
                duration_ms, now
            )
        )
        conn.commit()

    def get_agent_outputs(self, run_id: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM agent_outputs WHERE run_id=? ORDER BY id", (run_id,)).fetchall()
        return [dict(r) for r in rows]

    # ── Execution Logs ────────────────────────────────────────

    def record_log(self, run_id: str, timestamp: str, agent: str, message: str, log_type: str = "info") -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO execution_logs (run_id, timestamp, agent, message, log_type) VALUES (?, ?, ?, ?, ?)",
            (run_id, timestamp, agent, message, log_type)
        )
        conn.commit()

    def get_logs(self, run_id: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM execution_logs WHERE run_id=? ORDER BY id", (run_id,)).fetchall()
        return [dict(r) for r in rows]

    # ── State Transitions ─────────────────────────────────────

    def record_transition(
        self, run_id: str, from_state: str, to_state: str,
        condition: Optional[str] = None, duration_ms: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        now = datetime.datetime.now().isoformat()
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO state_transitions (run_id, from_state, to_state, condition, timestamp, duration_ms, error) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (run_id, from_state, to_state, condition, now, duration_ms, error)
        )
        conn.commit()

    def get_transitions(self, run_id: str) -> List[Dict[str, Any]]:
        conn = self._get_conn()
        rows = conn.execute("SELECT * FROM state_transitions WHERE run_id=? ORDER BY id", (run_id,)).fetchall()
        return [dict(r) for r in rows]
