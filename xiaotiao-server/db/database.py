import os
import re
import sqlite3
from fastapi import HTTPException, Request

from db.auth_db import get_user_by_token

# Default path from .env or fallback (legacy shared DB)
DB_PATH = os.getenv("DB_PATH", "./db/xiaotiao.db")
USER_DB_ROOT = os.getenv("USER_DB_ROOT", "./db/users")

for path in [os.path.dirname(DB_PATH), USER_DB_ROOT]:
    if path and not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def get_user_db_path(user_id: str) -> str:
    safe_id = user_id.replace("/", "").replace("..", "")
    return os.path.join(USER_DB_ROOT, f"{safe_id}.db")


def _resolve_db_path(db_path: str = None) -> str:
    return db_path or DB_PATH


def init_db(db_path: str = None):
    """Run init.sql to ensure all tables and seed data exist."""
    path = _resolve_db_path(db_path)
    init_sql_path = os.path.join(os.path.dirname(__file__), "init.sql")
    if os.path.exists(init_sql_path):
        conn = sqlite3.connect(path, check_same_thread=False)
        with open(init_sql_path, "r", encoding="utf-8") as f:
            script = f.read()
            conn.executescript(script)
        conn.commit()
        conn.close()


def run_migrations(db_path: str = None):
    """Execute all SQL migration scripts in db/migrations (idempotent)."""
    migrations_dir = os.path.join(os.path.dirname(__file__), "migrations")
    if not os.path.isdir(migrations_dir):
        return
    sql_files = sorted(
        name for name in os.listdir(migrations_dir)
        if name.endswith(".sql")
    )
    if not sql_files:
        return
    path = _resolve_db_path(db_path)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    for filename in sql_files:
        path_sql = os.path.join(migrations_dir, filename)
        with open(path_sql, "r", encoding="utf-8") as f:
            script = f.read()
        statements = [s.strip() for s in script.split(";") if s.strip()]
        for stmt in statements:
            # Idempotent handling for ALTER TABLE ADD COLUMN
            alter_match = re.match(
                r"ALTER\s+TABLE\s+([^\s]+)\s+ADD\s+COLUMN\s+([^\s]+)",
                stmt,
                flags=re.IGNORECASE,
            )
            if alter_match:
                table = alter_match.group(1).strip('"`[]')
                column = alter_match.group(2).strip('"`[]')
                cols = conn.execute(f"PRAGMA table_info({table})").fetchall()
                if any(col["name"] == column for col in cols):
                    continue
            try:
                conn.execute(stmt)
            except sqlite3.OperationalError as exc:
                msg = str(exc).lower()
                if "duplicate column" in msg or "already exists" in msg:
                    continue
                raise
    conn.commit()
    conn.close()


from services.auth_service import extract_token as _extract_token


def get_db(request: Request):
    token = _extract_token(request)
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="未登录或登录已失效。")
    db_path = get_user_db_path(user["id"])
    init_db(db_path)
    run_migrations(db_path)
    db = sqlite3.connect(db_path, check_same_thread=False)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()
