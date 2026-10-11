"""Feature demo: milestone theme unlocks (F-115).

Full behavior: new palettes unlock as proof accumulates — moss at
the first owned concept, dusk at five, canopy with the first
teaching certificate. Clicking a swatch applies it via :root
variables (choice kept in localStorage); purely cosmetic. seed_db
prunes to one owned concept so moss unlocks and dusk stays locked.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-themeunlock-115"
NODE = "demo/theme.py:mossy"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = f"{MODULE_ID}:ex001"

SCENARIO = {
    "id": "themeunlock",
    "kind": "feature",
    "batch": 23,
    "item": "F-115",
    "title": "Theme unlocks",
    "blurb": "Milestones earn palettes -- cosmetic only, kept in your browser.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 23 - Feature F-115",
         "title": "Theme unlocks",
         "subtitle": "Proof earns palettes -- moss, dusk, canopy."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b23-themeunlock",
         "caption": "Status documents the milestones: moss at one owned, dusk at five.",
         "assert_js": "() => !!document.querySelector('#status-b23-themeunlock')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "focus": "#theme-unlocks",
         "caption": "One owned concept unlocks Moss; clicking the swatch applies it.",
         "js": ["() => { const b = document.querySelector("
                "\"button[data-theme=moss]\"); "
                "if (!b) return 'moss-missing'; b.click(); return 'applied'; }"],
         "assert_js": "() => document.documentElement.style.getPropertyValue("
                      "'--paper').includes('f2f6ec')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Unlocks derive from owned counts plus certificates -- dusk waits for five.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import themeunlock as m; "
              "db = os.environ['DEMO_DB']; "
              "print('progress:', m.progress(db)); "
              "print([(p['name'], p['locked']) for p in m.unlocked(db)])"],
         ]},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 23",
         "title": "Wear your proof.",
         "subtitle": "themeunlock.py is cosmetic only -- the engine never sees it."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Prune to one owned concept: moss unlocked, dusk locked."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for table in ("reviews", "cards", "diffvote_votes",
                      "clarity_ratings", "confusing_flags", "known_skips",
                      "concepts", "modules"):
            con.execute(f"DELETE FROM {table}")
        lessons = [
            {"concept_id": NODE, "name": "mossy",
             "kind": "function", "file": "demo/theme.py", "line": 1,
             "summary": "mossy is owned, unlocking the moss palette.",
             "docstring": "First owned, first palette.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def mossy():\n    return theme()\n",
             "complexity": 1,
             "how": ["Own one concept.", "Paint it moss."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Theme-unlock module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "mossy", "function",
             "demo/theme.py", 1, 0.9))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '27', ?)", (CARD_ID, CID, now))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " submission) VALUES(?, 5, 4, ?, 'themeunlock seed')",
                (CARD_ID, now))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
