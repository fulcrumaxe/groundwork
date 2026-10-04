"""Feature demo: changelog entry (F-20, type 43).

Full behavior: write a keep-a-changelog entry -- right section,
6+-word impact line, concept named. seed_db plants a static
type-43 card (generate() bytes) as the sole due card; terminal
runs accept + wrong-section reject, /due submits the single-line
passing shape (the Due input holds one line) and polls the 3/3
verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-changelog-43"

SCENARIO = {
    "id": "changelog",
    "kind": "feature",
    "batch": 8,
    "item": "F-20",
    "title": "Changelog entry",
    "blurb": ("Write a keep-a-changelog entry: pick the Added/Changed/Fixed "
              "section and state the user-visible impact."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Feature F-20",
         "title": "Changelog entry",
         "subtitle": "Header plus impact: what can a user now do differently?"},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-changelog",
         "caption": ("Status homes the type: right section, impact line, "
                     "concept named."),
         "assert_js": "() => !!document.querySelector('#status-b8-changelog')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: section + 6-word impact line + "
                     "the concept name."),
         "commands": [
             ["python3", "-c",
              "from groundwork import changelog as m; "
              "from types import SimpleNamespace; c = SimpleNamespace(node_id='f', "
              "name='fetch_user', kind='function', file='users.py', line=1); "
              "e = m.generate('x', c, ['def fetch_user(user_id):', '    return {}'], {}); "
              "print(m.grade(e, '- `fetch_user` now lets you look up any user by id, added here.')['feedback']); "
              "print(m.grade(e, '### Fixed\\n- `fetch_user` now lets you look up any user by id.')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The changelog card: keep-a-changelog rules on the front.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('changelog'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": ("Section, impact, concept named -- the verdict accepts "
                     "the entry."),
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Entry accepted",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('3/3 rubric points')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Users read this.",
         "subtitle": "changelog.py grades the entry -- section, impact, name."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-43 card (generate() bytes) as the sole due card."""
    front = ("Write a keep-a-changelog entry for `fetch_user` (function in "
             "users.py).\n1. Put it under the section header `### Added`.\n2. Add "
             "one user-impact line: what can a user now do differently because of "
             "`fetch_user`? Name `fetch_user` explicitly.\nReply with the header "
             "line plus your one-line entry.")
    back = ("### Added\n- `fetch_user` now lets users do more with function "
            "in users.py (model entry \u2014 any line under `### Added` that states the "
            "user-visible change and names `fetch_user` counts).")
    payload = {"section": "Added", "keyword": "fetch_user", "grounded": True}
    answer = ("- `fetch_user` now lets you look up any user by id, "
              "added in this release.")
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
            " VALUES(?, ?, '43', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], front, back, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(answer))[1:-1]}
    finally:
        con.close()
