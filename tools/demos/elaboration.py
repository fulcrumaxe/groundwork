"""Feature demo: elaboration drills (F-59).

Full behavior: the new lesson in a three-concept module renders a
drill bridging it to its two mastered siblings -- shared tokens pick
the partners, and the terminal re-runs the pure picker.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-elab-59"
NEW_NODE = "demo/elab.py:deadline"
NEW_SLUG = "demo-elab-py-deadline"
LESSONS = [
    ("demo/elab.py:retries", "Retry budget",
     "Spend a retry budget across flaky calls.", 0.9),
    ("demo/elab.py:backoff", "Backoff clock",
     "Back off the clock between slow calls.", 0.9),
    (NEW_NODE, "Deadline guard",
     "Guard each slow call with a shared deadline clock"
     " and retry budget.", 0.0),
]

SCENARIO = {
    "id": "elaboration",
    "kind": "feature",
    "batch": 12,
    "item": "F-59",
    "title": "Elaboration drills",
    "blurb": "Connect the new to two you own -- shared tokens pick the partners.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Feature F-59",
         "title": "Elaboration drills",
         "subtitle": "Connect the new to two you own."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b12-elaboration",
         "caption": "Status homes the drill: closest two owned, like and unlike.",
         "assert_js": "() => { const el = document.querySelector("
                      "\"#status-b12-elaboration\"); return !!el && "
                      "document.body.innerText.includes('elaboration_drill'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: shared tokens pair, one owned waits.",
         "commands": [
             ["python3", "-c",
              "from groundwork import elaboration as m; "
              "new = {'name': 'Deadline guard', 'summary': 'slow call "
              "deadline clock retry budget'}; "
              "owned = [{'name': 'Retry budget', 'summary': 'retry budget "
              "flaky calls'}, {'name': 'Backoff clock', 'summary': 'clock "
              "slow calls'}]; "
              "d = m.elaboration_drill(new, owned); "
              "print('partners:', d['partners']); "
              "print('bridge:', d['bridge']); "
              "print('lonely:', m.elaboration_drill(new, owned[:1])"
              "['partners'])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#seed-drill",
         "caption": "The new lesson drills: bridge it via Retry budget and Backoff clock.",
         "js": ["() => { const h = [...document.querySelectorAll('h4')]"
                ".find(e => e.innerText.includes('elaboration drill')); "
                "if (h && h.parentElement) "
                "{ h.parentElement.id = 'seed-drill'; return 'tagged'; } "
                "return 'missing'; }"],
         "assert_js": "() => { const el = document.querySelector("
                      "'#seed-drill'); return !!el && "
                      "el.innerText.includes('elaboration drill') && "
                      "el.innerText.includes('Retry budget'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Bridge it.",
         "subtitle": "elaboration.py pairs partners -- tokens choose."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant two mastered siblings and one new lesson to bridge."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        cids = [f"{MODULE_ID}:{node}" for node, _n, _s, _m in LESSONS]
        for cid in cids:
            con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
            con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": node, "name": name, "kind": "function",
             "file": "demo/elab.py", "line": 1, "summary": summary,
             "docstring": f"{name}, elaboration edition."}
            for node, name, summary, _m in LESSONS
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/elaboration", "Elaboration drill module",
             now, json.dumps(lessons)))
        for (node, name, _s, mastery), cid in zip(LESSONS, cids):
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, name, "function", "demo/elab.py", 1,
                 mastery))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "slug": NEW_SLUG}
    finally:
        con.close()
