"""Feature demo: accessibility audit (F-29, type 52).

Full behavior: read rendered HTML, list every access barrier --
the bare img misses alt here -- checklist-graded with tolerant
word matching, no sandbox. seed_db plants a static type-52 card
(generate() bytes) as the sole due card; terminal runs accept +
reject, /due submits plain words and polls the 1/1 verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-a11yaudit-52"

SCENARIO = {
    "id": "a11yaudit",
    "kind": "feature",
    "batch": 9,
    "item": "F-29",
    "title": "Accessibility audit",
    "blurb": "Name the access barriers in rendered HTML -- alt, labels, roles, lang.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Feature F-29",
         "title": "Accessibility audit",
         "subtitle": "List the violations -- plain words count."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-a11yaudit",
         "caption": "Status homes the type: six rules, tolerant word matching.",
         "assert_js": "() => !!document.querySelector('#status-b9-a11yaudit')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: every required rule named -- plain words accepted.",
         "commands": [
             ["python3", "-c",
              "from types import SimpleNamespace; "
              "from groundwork import a11yaudit as m; "
              "c = SimpleNamespace(node_id='n-avatar', "
              "name='avatar', kind='function', file='svc.py', line=1); "
              "e = m.generate('demo-a11yaudit-52', c, ['<img src=\"avatar.png\">'], {}); "
              "print(m.grade(e, 'missing alt text')['feedback']); "
              "print(m.grade(e, 'missing lang')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The audit card: the marked elements on the front, your rules below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('accessibility violation'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Missing alt text -- the verdict takes the audit.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "All 1 violations named.",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('All 1 violations named.')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Barriers, listed.",
         "subtitle": "a11yaudit.py audits rendered HTML -- six rules, plain words count."},
    ],
}

FRONT = 'List every accessibility violation as `id=rule` (plain words count, e.g. `0=missing alt text`).\nRule ids: img-missing-alt, input-missing-label, div-with-onclick-no-role, html-missing-lang, empty-link-text, h1-skip.\n```html\n<img src="avatar.png">\n```\nMarked elements:\n0: <img src="avatar.png"> (line 1)'
BACK = '0=img-missing-alt'
PAYLOAD = {'checklist': [{'id': 0, 'rule': 'img-missing-alt', 'element': '<img src="avatar.png">', 'line': 1, 'why': 'images need alt text (or alt="" when decorative)'}], 'rules': ['img-missing-alt', 'input-missing-label', 'div-with-onclick-no-role', 'html-missing-lang', 'empty-link-text', 'h1-skip'], 'grounded': True}
ANSWER = 'missing alt text'


def seed_db(db_path: str) -> dict:
    """Plant one type-52 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '52', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
