"""Feature demo: buddy matching by repo overlap (F-126).

Full behavior: the opt-in form (?buddymatch=1) ranks pasted buddy
profiles by shared repos and concept names, local only; opted out
or with no overlap it renders nothing. seed_db plants one module.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from urllib.parse import quote

MODULE_ID = "demo-buddymatch-126"
NODE = "demo/match.py:loops"
CID = f"{MODULE_ID}:{NODE}"
REPO = "calc"
CONCEPT = "loops"

SCENARIO = {
    "id": "buddymatch",
    "kind": "feature",
    "batch": 24,
    "item": "F-126",
    "title": "Buddy matching by overlap",
    "blurb": "Opt in to find overlapping repos -- local only.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Feature F-126",
         "title": "Buddy matching by overlap",
         "subtitle": "Shared repos surface study partners -- nothing stored."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-buddymatch",
         "caption": "Status scopes the match: opt-in, in memory, no directory.",
         "assert_js": "() => !!document.querySelector("
                      "'#status-b24-buddymatch')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Weighted Jaccard over repos and concepts ranks the pasted profiles.",
         "commands": [
             ["python3", "-c",
              "from groundwork import buddymatch as m; "
              "me = {'name': 'Ada', 'repos': ['calc'], 'concepts': ['loops']}; "
              "them = {'name': 'Grace', 'repos': ['calc'], 'concepts': ['loops']}; "
              "print('score:', m.overlap_score(me, them)); "
              "print('rank:', m.match_buddies(me, [them])); "
              "print(m.match_html(me, [them], opt_in=True)[:130])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": ("/modules/{seed_mid}?buddy=Ada&buddy=Grace"
                      "&buddymatch=1&bmatch_repos=calc&bmatch_concepts=loops"),
         "focus": ".buddy-match",
         "caption": "Opted in with an overlapping footprint, Grace ranks first.",
         "assert_js": "() => !!document.querySelector('.buddy-match') "
                      "&& document.body.innerText.includes("
                      "'Buddies by repo overlap')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Match, then study.",
         "subtitle": "buddymatch.py ranks overlap -- opted out means silent."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a one-lesson module with repo calc and concept loops."""
    _ = quote
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
            {"concept_id": NODE, "name": CONCEPT,
             "kind": "function", "file": "demo/match.py", "line": 1,
             "summary": "loops is the shared concept for matching.",
             "docstring": "Opt in, paste, match.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def loops(items):\n    return [x for x in items]\n",
             "complexity": 1,
             "how": ["Opt in.", "Paste the footprint."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, REPO, "Buddy-match module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, CONCEPT, "function",
             "demo/match.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
