"""Feature demo: skill-atom split (F-99).

Full behavior: two trailing fails split the concept into ordered sub-skills
(recall, discriminate, procedure, transfer) voted by the miss notes, so
reteach targets the failing part. seed_db plants a type-1 card with two
diagnostic fails; the /due beat submits a third and films the atoms block.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-atoms-99"
NODE = "demo/atoms.py:total"
CONCEPT_ID = f"{MODULE_ID}:{NODE}"
CARD_ID = "demo-atoms-hard"

SCENARIO = {
    "id": "skillatoms",
    "kind": "feature",
    "batch": 21,
    "item": "F-99",
    "title": "Skill-atom split",
    "blurb": "Two fails in a row split the concept into sub-skills to reteach.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Feature F-99",
         "title": "Skill-atom split",
         "subtitle": "Fail twice, and the concept splits -- reteach the failing part."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-skillatoms",
         "caption": "Status documents the four atoms with a live split sample.",
         "assert_js": "() => !!document.querySelector('#status-b21-skillatoms')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: miss notes vote atoms; two misses split.",
         "commands": [
             ["python3", "-c",
              "from groundwork import skillatoms as m; "
              "print('forgot the definition ->', m.classify_miss('forgot the definition')); "
              "print('wrong order of steps ->', m.classify_miss('wrong order of steps')); "
              "atts = [{'ok': False, 'note': 'forgot the definition'}, "
              "{'ok': False, 'note': 'wrong order of steps'}]; "
              "print('split:', m.needs_split(atts)); "
              "print([a['label'] for a in m.decompose('total', atts)])"],
         ]},
        {"type": "chrome", "duration": 16,
         "url_path": "/due",
         "focus": "#skill-atoms",
         "caption": "Fail the card again -- the verdict splits it into sub-skills.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const sel = f.querySelector(\"select[name='answer']\"); "
                "if (!sel) return 'no-select'; sel.value = '1'; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Sub-skills for",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { const s = document.querySelector('#skill-atoms'); "
                      "return !!s && s.innerText.includes('Recall the definition') && "
                      "s.innerText.includes('Apply the steps in order'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Split it, then fix it.",
         "subtitle": "skillatoms.py votes sub-skills -- passes never split."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a type-1 card with two diagnostic prior fails."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE id=?", (CONCEPT_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lesson = {"concept_id": NODE, "name": "total", "kind": "function",
                  "file": "demo/atoms.py", "line": 1,
                  "summary": "Sum rows into a running total."}
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/skillatoms", "Skill atoms module", now,
             json.dumps([lesson])))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CONCEPT_ID, MODULE_ID, "total", "function",
             "demo/atoms.py", 1, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '1', ?, ?, ?)",
            (CARD_ID, CONCEPT_ID, "What does total() return with no rows?",
             "0: the seed value.", "2000-01-01T00:00:00Z"))
        for note in ("forgot the definition", "wrong order of steps"):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, 1, 2, ?)", (CARD_ID, note))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
