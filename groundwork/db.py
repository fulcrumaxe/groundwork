"""SQLite connection + schema init. Stdlib only."""
from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_PATH = Path(__file__).with_name("schema.sql")
DEFAULT_DB = Path("groundwork.db")


def connect(db_path: str | Path = DEFAULT_DB) -> sqlite3.Connection:
    db_path = Path(db_path)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    return con


def init_db(db_path: str | Path = DEFAULT_DB) -> Path:
    db_path = Path(db_path)
    con = connect(db_path)
    try:
        with open(SCHEMA_PATH, encoding="utf-8") as f:
            con.executescript(f.read())
        # Lightweight migrations for DBs created before a column existed.
        cols = [r[1] for r in con.execute("PRAGMA table_info(modules)").fetchall()]
        for col in ("lessons", "purpose"):
            if col not in cols:
                default = "'[]'" if col == "lessons" else "''"
                con.execute(f"ALTER TABLE modules ADD COLUMN {col} TEXT NOT NULL DEFAULT {default}")
        rcols = [r[1] for r in con.execute("PRAGMA table_info(reviews)").fetchall()]
        if "submission" not in rcols:
            con.execute("ALTER TABLE reviews ADD COLUMN submission TEXT NOT NULL DEFAULT ''")
        for col, typ in (("prev_stability", "REAL NOT NULL DEFAULT 0"),
                         ("prev_difficulty", "REAL NOT NULL DEFAULT 0"),
                         ("prev_retrievability", "REAL NOT NULL DEFAULT 0"),
                         ("prev_due", "TEXT NOT NULL DEFAULT ''"),
                         ("prev_lapses", "INTEGER NOT NULL DEFAULT 0"),
                         ("prev_mastery", "REAL NOT NULL DEFAULT 0")):
            if col not in rcols:
                con.execute(f"ALTER TABLE reviews ADD COLUMN {col} {typ}")
        # Batch 15 migration (nullable, additive only): banked
        # calibration points per review; last probe timestamp per card.
        # Downgrade: ALTER TABLE <t> DROP COLUMN <col> (SQLite 3.35+)
        # or restore the pre-batch15 backup.
        if "points" not in rcols:
            con.execute("ALTER TABLE reviews ADD COLUMN points INTEGER")
        ccols = [r[1] for r in con.execute("PRAGMA table_info(cards)").fetchall()]
        if "last_probe" not in ccols:
            con.execute("ALTER TABLE cards ADD COLUMN last_probe TEXT")
        con.execute(
            "CREATE TABLE IF NOT EXISTS disputes ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " card_id TEXT NOT NULL REFERENCES cards(id) ON DELETE CASCADE,"
            " reason TEXT NOT NULL DEFAULT '',"
            " status TEXT NOT NULL DEFAULT 'open',"
            " created_at TEXT NOT NULL DEFAULT"
            " (strftime('%Y-%m-%dT%H:%M:%SZ','now')))")
        # Batch 21 migration (new nullable table only): per-section
        # confusing flags. Downgrade: DROP TABLE confusing_flags
        # or restore the pre-batch21 backup.
        con.execute(
            "CREATE TABLE IF NOT EXISTS confusing_flags ("
            " section_id TEXT PRIMARY KEY,"
            " flagged_at TEXT NOT NULL DEFAULT"
            " (strftime('%Y-%m-%dT%H:%M:%SZ','now')))")
        con.commit()
    finally:
        con.close()
    return db_path
