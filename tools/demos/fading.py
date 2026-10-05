"""Feature demo: worked-example fading (F-57).

Full behavior: a lesson with one attempt renders the partial fade
(last step hidden, recall-before-peeking note) on its module page;
the terminal re-runs the pure three-stage sequencer.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-fading-57"
NODE = "demo/fade.py:trace"
CONCEPT_ID = f"{MODULE_ID}:{NODE}"
CARD_ID = "demo-fading-57"
HOW = [
    "Seed the total at zero before the loop.",
    "Add each row exactly once, in order.",
    "Clamp the total so late rows cannot overflow it.",
    "Return the total with its row count attached.",
]

SCENARIO = {
    "id": "fading",
    "kind": "feature",
    "batch": 12,
    "item": "F-57",
    "title": "Worked-example fading",
    "blurb": "Full trace, then the last step hides, then only the first shows.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Feature F-57",
         "title": "Worked-example fading",
         "subtitle": "Full trace, then last step hides, then first only."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b12-fading",
         "caption": "Status homes the fader: three stages, hint-tier names.",
         "assert_js": "() => { const el = document.querySelector("
                      "\"#status-b12-fading\"); return !!el && "
                      "document.body.innerText.includes('fade_sequence'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: 3 shown, then 2, then 1.",
         "commands": [
             ["python3", "-c",
              "from groundwork import fading as m; "
              "seq = m.fade_sequence(['seed', 'add', 'clamp']); "
              "print([(s['stage'], len(s['shown']), len(s['hidden'])) "
              "for s in seq]); "
              "print('tiers:', [m.stage_tier(s) for s in "
              "('full', 'partial', 'solo', 'bogus')])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#fading",
         "caption": "One attempt in: partial fades, last step hidden.",
         "js": ["() => { document.querySelectorAll('#fading details')"
                ".forEach(d => { d.open = true; }); return 'opened'; }"],
         "assert_js": "() => { const el = document.querySelector('#fading');"
                      " return !!el && el.innerText.includes("
                      "'hide the last step') && el.innerText.includes("
                      "'recall before peeking'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Support shrinks.",
         "subtitle": "fading.py fades traces -- recall grows."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a lesson with worked steps and a single attempt on it."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE id=?", (CONCEPT_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lesson = {"concept_id": NODE, "name": "Trace walk",
                  "kind": "function", "file": "demo/fade.py", "line": 1,
                  "summary": "Walk a worked trace that fades with practice.",
                  "docstring": "Trace walk, fading edition.",
                  "how": HOW}
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/fading", "Fading trace module", now,
             json.dumps([lesson])))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CONCEPT_ID, MODULE_ID, "Trace walk", "function",
             "demo/fade.py", 1, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES(?, ?, '1', ?, ?)",
            (CARD_ID, CONCEPT_ID,
             "What clamps the running total?",
             "The clamp step after each add."))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
            " VALUES(?, 3, 3, ?)", (CARD_ID, now))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID}
    finally:
        con.close()
