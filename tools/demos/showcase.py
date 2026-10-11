"""Feature demo: private badge showcase gallery (F-114).

Full behavior: every owned concept renders its sealed tile (the
owned seal plus the emblem) on History; locked concepts stay plain
names — no tiers, no rarity, no public route. seed_db prunes to
one owned plus one locked concept.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-showcase-114"
OWNED_NODE = "demo/gallery.py:framed"
LOCKED_NODE = "demo/gallery.py:pending"
OWNED_CID = f"{MODULE_ID}:{OWNED_NODE}"
LOCKED_CID = f"{MODULE_ID}:{LOCKED_NODE}"

SCENARIO = {
    "id": "showcase",
    "kind": "feature",
    "batch": 23,
    "item": "F-114",
    "title": "Badge showcase",
    "blurb": "Your earned badges in one private gallery -- proof, not pressure.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 23 - Feature F-114",
         "title": "Badge showcase",
         "subtitle": "Earned badges, tiled -- locked ones stay plain names."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b23-showcase",
         "caption": "Status documents the gallery: private, sealed tiles, no public route.",
         "assert_js": "() => !!document.querySelector('#status-b23-showcase')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The gallery reads ownership straight off existing tables.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import showcase as m; "
              "rows = m.badges(os.environ['DEMO_DB']); "
              "print([(r['concept'], r['owned']) for r in rows])"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/reviews",
         "focus": "#showcase",
         "caption": "History tiles the owned concept with seal and emblem beside the locked name.",
         "assert_js": "() => !!document.querySelector('.showcase-tile .cbadge') "
                      "&& !!document.querySelector('.showcase-locked')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 23",
         "title": "Proof on the wall.",
         "subtitle": "showcase.py tiles seals plus emblems -- private to you."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Prune to one owned plus one locked concept."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for table in ("reviews", "cards", "diffvote_votes",
                      "clarity_ratings", "confusing_flags", "known_skips",
                      "concepts", "modules"):
            con.execute(f"DELETE FROM {table}")
        lessons = [
            {"concept_id": OWNED_NODE, "name": "framed",
             "kind": "function", "file": "demo/gallery.py", "line": 1,
             "summary": "framed is owned and hangs in the gallery.",
             "docstring": "Sealed and tiled.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def framed():\n    return tile()\n",
             "complexity": 1,
             "how": ["Own it.", "Frame it."]},
            {"concept_id": LOCKED_NODE, "name": "pending",
             "kind": "function", "file": "demo/gallery.py", "line": 9,
             "summary": "pending is still a plain name on the wall.",
             "docstring": "Not yet.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def pending():\n    return later()\n",
             "complexity": 1,
             "how": ["Practice.", "Unlock."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Showcase module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (OWNED_CID, MODULE_ID, "framed", "function",
             "demo/gallery.py", 1, 0.9))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (LOCKED_CID, MODULE_ID, "pending", "function",
             "demo/gallery.py", 9, 0.0))
        owned_card = f"{MODULE_ID}:ex001"
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '27', ?)", (owned_card, OWNED_CID, now))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '1', ?)", (f"{MODULE_ID}:ex002", LOCKED_CID, now))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " submission) VALUES(?, 5, 4, ?, 'showcase seed')",
                (owned_card, now))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
