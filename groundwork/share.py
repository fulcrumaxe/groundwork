"""Module sharing: export a module to JSON, import it into any Groundwork DB.

A shared file carries the teaching content (module row, concepts, cards,
lessons) but never personal progress: reviews stay behind, and imported
cards restart with fresh scheduling.
"""
from __future__ import annotations

import json

from . import db as dbmod
from . import sched as schedmod

FORMAT = "groundwork-module/1"
SEED_FORMAT = "groundwork-seed/1"
SEED_REPO = "groundwork"


def export_module(db_path: str, mid: str) -> dict:
    """Module + concepts + cards as a JSON-serializable share document."""
    con = dbmod.connect(db_path)
    try:
        m = con.execute("SELECT * FROM modules WHERE id=?", (mid,)).fetchone()
        if m is None:
            raise KeyError(f"unknown module: {mid}")
        concepts = [dict(r) for r in con.execute(
            "SELECT * FROM concepts WHERE module_id=?", (mid,)).fetchall()]
        cards = [dict(r) for r in con.execute(
            "SELECT cards.* FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=?", (mid,)).fetchall()]
    finally:
        con.close()
    for c in cards:
        # Scheduling is personal progress: restart fresh on import.
        for k in ("stability", "difficulty", "retrievability",
                  "due", "stale", "lapses"):
            c.pop(k, None)
    return {"format": FORMAT, "module": dict(m),
            "concepts": concepts, "cards": cards}


def import_module(db_path: str, doc: dict) -> dict:
    """Load a share document; existing module ids are skipped, never merged."""
    if not isinstance(doc, dict) or doc.get("format") != FORMAT:
        raise ValueError("not a groundwork module file")
    dbmod.init_db(db_path)
    con = dbmod.connect(db_path)
    try:
        mid = doc["module"]["id"]
        if con.execute("SELECT 1 FROM modules WHERE id=?",
                       (mid,)).fetchone():
            return {"module_id": mid, "status": "skipped-duplicate",
                    "concepts": 0, "cards": 0}
        m = doc["module"]
        con.execute(
            "INSERT INTO modules(id, repo, commit_range, task_summary,"
            " learner_level, created_at, source_markdown, lessons, purpose)"
            " VALUES(?,?,?,?,?,?,?,?,?)",
            (m["id"], m.get("repo", ""), m.get("commit_range", ""),
             m.get("task_summary", ""), m.get("learner_level", "intermediate"),
             m.get("created_at", schedmod.iso(schedmod.utcnow())),
             m.get("source_markdown", ""), m.get("lessons", "[]"),
             m.get("purpose", "")))
        n_concepts = 0
        for c in doc.get("concepts", []):
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file, line,"
                " file_hash, bloom, mastery) VALUES(?,?,?,?,?,?,?,?,?)",
                (c["id"], mid, c.get("name", ""), c.get("kind", "function"),
                 c.get("file", ""), c.get("line", 0), c.get("file_hash", ""),
                 c.get("bloom", "recall"), 0.0))
            n_concepts += 1
        n_cards = 0
        for c in doc.get("cards", []):
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type, front, back,"
                " payload) VALUES(?,?,?,?,?,?)",
                (c["id"], c["concept_id"], c.get("exercise_type", "1"),
                 c.get("front", ""), c.get("back", ""),
                 c.get("payload", "{}") if isinstance(
                     c.get("payload", "{}"), str)
                 else json.dumps(c.get("payload", {}))))
            n_cards += 1
        con.commit()
    finally:
        con.close()
    return {"module_id": mid, "status": "imported",
            "concepts": n_concepts, "cards": n_cards}


def export_seed(db_path: str, repo_prefix: str) -> dict:
    """Every module under one repo, relabeled to a portable seed name."""
    prefix = repo_prefix.rstrip("/")
    con = dbmod.connect(db_path)
    try:
        rows = con.execute("SELECT id, repo FROM modules").fetchall()
    finally:
        con.close()
    mids = [r[0] for r in rows if (r[1] or "") == prefix
            or (r[1] or "").startswith(prefix + "/")]
    docs = []
    for mid in mids:
        doc = export_module(db_path, mid)
        doc["module"]["repo"] = SEED_REPO
        docs.append(doc)
    return {"format": SEED_FORMAT, "repo": SEED_REPO, "modules": docs}


def import_seed(db_path: str, doc: dict, relabel_repo: str = "") -> list[dict]:
    """Load a seed file (or a single module doc); duplicates skip cleanly."""
    if not isinstance(doc, dict):
        raise ValueError("not a groundwork module file")
    if doc.get("format") == FORMAT:
        docs = [doc]
    elif doc.get("format") == SEED_FORMAT:
        docs = doc.get("modules", [])
    else:
        raise ValueError("not a groundwork module file")
    out = []
    for d in docs:
        if relabel_repo:
            d = {**d, "module": {**d["module"], "repo": relabel_repo}}
        out.append(import_module(db_path, d))
    return out
