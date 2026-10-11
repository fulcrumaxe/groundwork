"""Feature demo: effort-noticing mascot companion (F-117).

Full behavior: a small text companion on the Due page notices
attempts — warming up, in stride, deep in it — and never mentions
accuracy, streaks, or scores. Zero attempts gets a resting line
with no guilt. seed_db records exactly three attempts today.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-mascot-117"
NODE = "demo/momo.py:trying"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = f"{MODULE_ID}:ex001"

SCENARIO = {
    "id": "mascot",
    "kind": "feature",
    "batch": 23,
    "item": "F-117",
    "title": "Mascot companion",
    "blurb": "A small companion that notices attempts -- never wins, never streaks.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 23 - Feature F-117",
         "title": "Mascot companion",
         "subtitle": "Effort, noticed -- attempts only, never scores."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b23-mascot",
         "caption": "Status documents the promise: attempts only, never accuracy or streaks.",
         "assert_js": "() => !!document.querySelector('#status-b23-mascot')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Mood is today's attempt count only: resting, warming, stride, deep.",
         "commands": [
             ["python3", "-c",
              "from groundwork import mascot as m; "
              "print('0:', m.mood_for(0)['mood']); "
              "print('1:', m.mood_for(1)['mood']); "
              "print('3:', m.mood_for(3)['mood']); "
              "print('12:', m.mood_for(12)['mood'])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "#mascot",
         "caption": "Three attempts today, so Momo is in stride beside the Due queue.",
         "assert_js": "() => document.body.innerText.includes('Momo is in stride')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 23",
         "title": "Steady attempts, no rush.",
         "subtitle": "mascot.py reads today's count -- hostile input rests."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Record exactly three attempts today on a planted card."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM cards WHERE concept_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        con.execute("DELETE FROM reviews WHERE reviewed_at >= ?",
                    (now[:10] + "T00:00:00Z",))
        lessons = [
            {"concept_id": NODE, "name": "trying",
             "kind": "function", "file": "demo/momo.py", "line": 1,
             "summary": "trying collects today's three attempts for Momo.",
             "docstring": "Effort, noticed.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def trying():\n    return attempt()\n",
             "complexity": 1,
             "how": ["Attempt.", "Attempt again."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Mascot module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "trying", "function",
             "demo/momo.py", 1, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '1', ?)", (CARD_ID, CID, now))
        for _ in range(3):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " submission) VALUES(?, 4, 3, ?, 'mascot seed')",
                (CARD_ID, now))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID, "attempts": 3}
    finally:
        con.close()
