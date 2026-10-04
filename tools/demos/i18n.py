"""Feature demo: i18n extraction (F-30, type 53).

Full behavior: read a function, list every hardcoded user-facing
string for translation -- Save changes here -- graded by exact set
match against the AST string set. seed_db plants a static type-53
card (generate() bytes) as the sole due card; terminal runs accept
+ extra-string reject, /due submits the string and polls the
1/1 verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-i18n-53"

SCENARIO = {
    "id": "i18n",
    "kind": "feature",
    "batch": 9,
    "item": "F-30",
    "title": "i18n extraction",
    "blurb": "List the hardcoded UI strings to extract for translation -- exact set match.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Feature F-30",
         "title": "i18n extraction",
         "subtitle": "Every user-facing string -- nothing missing, nothing extra."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-i18n",
         "caption": "Status homes the type: AST string set, exact match.",
         "assert_js": "() => !!document.querySelector('#status-b9-i18n')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: exact set -- a missing string or one extra fails.",
         "commands": [
             ["python3", "-c",
              "from types import SimpleNamespace; "
              "from groundwork import i18n as m; "
              "c = SimpleNamespace(node_id='n-save', "
              "name='save', kind='function', file='svc.py', line=1); "
              "e = m.generate('demo-i18n-53', c, ['def save():', '    print(\"Save changes\")'], {}); "
              "print(m.grade(e, 'Save changes')['feedback']); "
              "print(m.grade(e, 'Save changes\\nExtra string')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The extraction card: the function on the front, your strings below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('extracted for translation'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Save changes, exactly -- the verdict takes the extraction.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Complete extraction (1/1 strings).",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Complete extraction (1/1 strings).')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Strings, extracted.",
         "subtitle": "i18n.py grades the exact AST string set -- nothing missing, nothing extra."},
    ],
}

FRONT = 'Read `save` below. List every hardcoded user-facing string that should be extracted for translation (1 in total) \u2014 one string per line, exact text. F-string static text uses `{...}` for each dynamic hole; skip docstrings.\n\n```python\ndef save():\n    print("Save changes")\n```'
BACK = 'Save changes'
PAYLOAD = {'code': 'def save():\n    print("Save changes")', 'strings': ['Save changes'], 'count': 1, 'grounded': True}
ANSWER = 'Save changes'


def seed_db(db_path: str) -> dict:
    """Plant one type-53 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '53', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
