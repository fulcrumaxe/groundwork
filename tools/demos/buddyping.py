"""Feature demo: study-buddy pings without leaderboards (F-125).

Full behavior: two distinct ?buddy= names on a module page render
one local nudge (welcome, encouragement, celebration); solo visits
render exactly as before. seed_db plants a one-lesson module.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-buddyping-125"
NODE = "demo/ping.py:study_pair"
CID = f"{MODULE_ID}:{NODE}"

SCENARIO = {
    "id": "buddyping",
    "kind": "feature",
    "batch": 24,
    "item": "F-125",
    "title": "Study-buddy pings",
    "blurb": "A gentle nudge for your study pair -- no leaderboards.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Feature F-125",
         "title": "Study-buddy pings",
         "subtitle": "Accountability for two -- no rankings, no network."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-buddyping",
         "caption": "Status scopes the nudge: local pair, three moods.",
         "assert_js": "() => !!document.querySelector("
                      "'#status-b24-buddyping')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Pairs ping, solos stay silent; counts pick the mood.",
         "commands": [
             ["python3", "-c",
              "from groundwork import buddyping as m; "
              "print('pair:', m.pair_names(['Ada', 'Grace'])); "
              "print('pick:', m.pick_ping(0, 5), m.pick_ping(2, 5), m.pick_ping(5, 5)); "
              "print(m.ping_text('welcome', ['Ada', 'Grace']))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}?buddy=Ada&buddy=Grace",
         "focus": ".buddy-ping",
         "caption": "Two names on the module page render one welcome nudge.",
         "assert_js": "() => !!document.querySelector('.buddy-ping') "
                      "&& document.body.innerText.includes('Ada and Grace')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Nudge, don't rank.",
         "subtitle": "buddyping.py cheers the pair -- solo pages never change."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a one-lesson module for the pair nudge."""
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
            {"concept_id": NODE, "name": "study_pair",
             "kind": "function", "file": "demo/ping.py", "line": 1,
             "summary": "study_pair learns better with a named friend.",
             "docstring": "One nudge, two learners.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def study_pair(lesson, friends):\n    return nudge\n",
             "complexity": 1,
             "how": ["Name two friends.", "Read the nudge."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Buddy-ping module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "study_pair", "function",
             "demo/ping.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
