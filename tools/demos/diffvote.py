"""Improvement demo: per-lesson difficulty votes (I-145).

Full behavior: one tap under a lesson records too-easy, just-right,
or too-hard; the aggregate badge shows the plurality verdict with
full categorical counts (never a mean). seed_db plants a voteless
one-lesson module; the beats vote Too hard and film the badge.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-diffvote-145"
NODE = "demo/vote.py:rate_me"
CID = f"{MODULE_ID}:{NODE}"

SCENARIO = {
    "id": "diffvote",
    "kind": "improvement",
    "batch": 23,
    "item": "I-145",
    "title": "Vote lesson difficulty",
    "blurb": "Too easy, just right, or too hard -- one tap teaches the author.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 23 - Improvement I-145",
         "title": "Vote lesson difficulty",
         "subtitle": "Three buttons under every lesson -- tap once, teach the author."},
        {"type": "chrome", "duration": 6,
         "url_path": "/modules/{seed_mid}",
         "focus": "#diffvote",
         "caption": "Every lesson carries a three-way vote; this one has no votes yet.",
         "assert_js": "() => document.body.innerText.includes("
                      "'No difficulty votes yet')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Synonyms collapse to three buckets; the verdict is a plurality, never a mean.",
         "commands": [
             ["python3", "-c",
              "from groundwork import diffvote as m; "
              "print('too-easy ->', m.normalize_vote('too-easy')); "
              "print('bogus ->', repr(m.normalize_vote('bogus'))); "
              "print('verdict:', m.verdict({'easy': 1, 'just': 0, 'hard': 3}))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}",
         "caption": "One tap on Too hard records the vote.",
         "js": ["() => { const f = document.querySelector("
                "\"form[action='/concepts/{seed_cid}/diffvote']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const b = f.querySelector('button[value=hard]'); "
                "if (!b) return 'no-button'; b.click(); return 'clicked'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Difficulty vote recorded",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes("
                      "'Difficulty vote recorded')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "focus": "#diffvote",
         "caption": "Back on the lesson, the badge shows the verdict with full counts.",
         "assert_js": "() => document.body.innerText.includes('Too hard 1')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 23",
         "title": "One tap, counted.",
         "subtitle": "diffvote.py keeps the full distribution -- I-146 steers practice off it."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a voteless one-lesson module with exact-form targeting."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM diffvote_votes WHERE concept_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM reviews WHERE card_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM cards WHERE concept_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "rate_me",
             "kind": "function", "file": "demo/vote.py", "line": 1,
             "summary": "rate_me is waiting for its first difficulty vote.",
             "docstring": "Three buttons, one tap.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def rate_me():\n    return vote()\n",
             "complexity": 1,
             "how": ["Read the lesson.", "Tap its difficulty."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Difficulty-vote module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "rate_me", "function",
             "demo/vote.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID, "cid": CID}
    finally:
        con.close()
