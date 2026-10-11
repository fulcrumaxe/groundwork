"""Improvement demo: retired-lesson archive with reason (I-150).

Full behavior: lessons that retire — a source file deleted on
disk, or a concept whose cards did not survive regeneration — are
named with their reason in one module-page section instead of
vanishing silently. seed_db plants a module with one live and one
cardless concept.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-archiveless-150"
LIVE_NODE = "demo/gone.py:staying"
GHOST_NODE = "demo/gone.py:vanished"
LIVE_CID = f"{MODULE_ID}:{LIVE_NODE}"
GHOST_CID = f"{MODULE_ID}:{GHOST_NODE}"

SCENARIO = {
    "id": "archiveless",
    "kind": "improvement",
    "batch": 23,
    "item": "I-150",
    "title": "Retired lessons",
    "blurb": "Lessons that retire say why -- deleted file or regenerated cards.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 23 - Improvement I-150",
         "title": "Retired lessons",
         "subtitle": "Gone lessons say why -- never silent again."},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules/{seed_mid}",
         "focus": ".archive",
         "caption": "The cardless concept is archived with its reason; the live one is untouched.",
         "assert_js": "() => document.body.innerText.includes("
                      "'no cards \\u2014 retired by regeneration')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Reasons derive from current state: disk plus card counts, never history.",
         "commands": [
             ["python3", "-c",
              "from groundwork import archiveless as m; "
              "print('no cards:', m.reason_for('g', 'g.py', '/repo', False)); "
              "print('deleted file:', m.reason_for('g', 'g.py', '/nonexistent', True)); "
              "print('live:', repr(m.reason_for('g', '', '', True)))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b23-archiveless",
         "caption": "Status documents both reasons: deleted file, or regeneration.",
         "assert_js": "() => !!document.querySelector('#status-b23-archiveless')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 23",
         "title": "Retired, with reason.",
         "subtitle": "archiveless.py probes disk plus cards -- live modules never change."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a module with one live and one cardless concept."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM cards WHERE concept_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": LIVE_NODE, "name": "staying",
             "kind": "function", "file": "demo/gone.py", "line": 1,
             "summary": "staying keeps its cards and stays live.",
             "docstring": "Live and well.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def staying():\n    return here()\n",
             "complexity": 1,
             "how": ["Keep your cards."]},
            {"concept_id": GHOST_NODE, "name": "vanished",
             "kind": "function", "file": "demo/gone.py", "line": 9,
             "summary": "vanished lost its cards to regeneration.",
             "docstring": "Gone but named.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def vanished():\n    return gone()\n",
             "complexity": 1,
             "how": ["Lose your cards."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Archiveless module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (LIVE_CID, MODULE_ID, "staying", "function",
             "demo/gone.py", 1, 0.0))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (GHOST_CID, MODULE_ID, "vanished", "function",
             "demo/gone.py", 9, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '1', ?)", (f"{MODULE_ID}:ex001", LIVE_CID, now))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
