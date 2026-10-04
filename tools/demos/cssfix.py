"""Feature demo: CSS layout fix (F-33, type 56).

Full behavior: repair the broken .card block to the wireframe --
flex, centered both ways -- graded by static declaration-set
comparison with whitespace/case tolerance. seed_db plants a static
type-56 card (generate() bytes) as the sole due card; terminal runs
accept + wrong-value reject, /due submits the block and polls the
3/3 verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-cssfix-56"

SCENARIO = {
    "id": "cssfix",
    "kind": "feature",
    "batch": 9,
    "item": "F-33",
    "title": "CSS layout fix",
    "blurb": "Fix a broken CSS block to match the wireframe -- static tolerant grading.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Feature F-33",
         "title": "CSS layout fix",
         "subtitle": "Every spec property, matching value -- extras capped at two."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-cssfix",
         "caption": "Status homes the type: declaration sets compared, no browser.",
         "assert_js": "() => !!document.querySelector('#status-b9-cssfix')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: every property present and matching, folded.",
         "commands": [
             ["python3", "-c",
              "from types import SimpleNamespace; "
              "from groundwork import cssfix as m; "
              "c = SimpleNamespace(node_id='n-layout', "
              "name='layout', kind='function', file='svc.py', line=1); "
              "e = m.generate('demo-cssfix-56', c, [], {}); "
              "print(m.grade(e, 'display: flex; justify-content: center; align-items: center')['feedback']); "
              "print(m.grade(e, 'display: block')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The CSS card: the wireframe and broken block on the front.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('CSS layout fix'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Flex, centered both ways -- the verdict takes the block.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Wireframe matched (3/3 spec properties.)",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Wireframe matched (3/3 spec properties.)')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Wireframes, matched.",
         "subtitle": "cssfix.py compares declaration sets -- folded, extras capped."},
    ],
}

FRONT = 'CSS layout fix for `layout`: Wireframe: a card whose content is centered both ways.\nRepair this declaration block so it carries every required property (display, justify-content, align-items). Submit the fixed block.\n```css\n.card {\n  display: block;\n  justify-content: center;\n}\n```'
BACK = '.card {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n}'
PAYLOAD = {'selector': '.card', 'layout': 'centered-card', 'goal': 'Wireframe: a card whose content is centered both ways.', 'spec': {'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}, 'required': ['display', 'justify-content', 'align-items'], 'max_extra': 2, 'broken': '.card {\n  display: block;\n  justify-content: center;\n}', 'fixed': '.card {\n  display: flex;\n  justify-content: center;\n  align-items: center;\n}', 'grounded': True}
ANSWER = 'display: flex; justify-content: center; align-items: center'


def seed_db(db_path: str) -> dict:
    """Plant one type-56 card (generate() bytes) as the sole due card."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '56', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
