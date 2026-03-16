import sqlite3
import os

# Default path from .env or fallback
DB_PATH = os.getenv("DB_PATH", "./db/xiaotiao.db")
DB_DIR = os.path.dirname(DB_PATH)

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

def init_db():
    """Run init.sql to ensure all tables and seed data exist"""
    init_sql_path = os.path.join(os.path.dirname(__file__), "init.sql")
    if os.path.exists(init_sql_path):
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        with open(init_sql_path, "r", encoding="utf-8") as f:
            script = f.read()
            conn.executescript(script)
        conn.commit()
        conn.close()

def run_migrations():
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
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    for filename in sql_files:
        path = os.path.join(migrations_dir, filename)
        with open(path, "r", encoding="utf-8") as f:
            conn.executescript(f.read())
    conn.commit()
    conn.close()

def get_db():
    db = sqlite3.connect(DB_PATH, check_same_thread=False)
    db.row_factory = sqlite3.Row
    try:
        yield db
    finally:
        db.close()
