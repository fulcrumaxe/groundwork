"""Improvement demo: consistent disclosure carets (I-60).

Full behavior: every hint and grading details/summary disclosure
shares one CSS-drawn chevron (native marker suppressed,
summary::before draws it, details[open] rotates it down) -- pure
CSS, so keyboard and screen-reader semantics stay native. seed_db
plants one due card with real hints; /due shows the disclosures.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-carets-57"

SCENARIO = {
    "id": "carets",
    "kind": "improvement",
    "batch": 10,
    "item": "I-60",
    "title": "Disclosure carets",
    "blurb": "Every hint disclosure shares one CSS chevron -- semantics stay native.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Improvement I-60",
         "title": "Disclosure carets",
         "subtitle": "One chevron everywhere -- drawn by CSS, behaved by the browser."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-carets",
         "caption": "Status documents the caret: marker suppressed, chevron drawn, open rotates.",
         "assert_js": "() => !!document.querySelector('#status-b10-carets')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: the audit passes on the shipped CSS, fails on nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import carets as m; "
              "print(m.carets_css()[:150]); "
              "print('audit:', m.has_caret_rules(m.carets_css()), m.has_caret_rules(''))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} details.hint-nudge",
         "caption": "Hint disclosures wear the shared chevron -- the rule ships in the head.",
         "assert_js": "() => !!document.querySelector('details.hint-nudge summary') && "
                      "Array.from(document.querySelectorAll('head style')).some("
                      "s => s.textContent.includes('summary::before'))",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "One chevron, native soul.",
         "subtitle": "carets.py draws the marker -- the browser keeps the behavior."},
    ],
}

FRONT = 'Study this --help output. It contains exactly ONE usability flaw. Reply with the flaw category (id or label).\nCategories:\n- inconsistent-flag-naming (Inconsistent flag naming)\n- missing-required-marking (Missing required-argument marking)\n- destructive-default (Destructive default without confirmation)\n- cryptic-error (Cryptic error message)\n- no-examples (No examples section)\n```text\nusage: deploy [--mode MODE] [--confirm] [--output DIR]\n\noptions:\n  --mode MODE   what to do: deploy or wipe (default: wipe)\n  --confirm     ask before applying changes\n  --output DIR  write the report to DIR (default: ./out)\n\nrequired: none. all options are optional.\n\nexamples:\n  deploy --mode deploy\n  deploy --mode wipe --confirm\n```'
BACK = 'Flaw: Destructive default without confirmation (destructive-default). The default mode wipes and confirmation is opt-in, so a bare run destroys data.'
PAYLOAD = {'help': 'usage: deploy [--mode MODE] [--confirm] [--output DIR]\n\noptions:\n  --mode MODE   what to do: deploy or wipe (default: wipe)\n  --confirm     ask before applying changes\n  --output DIR  write the report to DIR (default: ./out)\n\nrequired: none. all options are optional.\n\nexamples:\n  deploy --mode deploy\n  deploy --mode wipe --confirm', 'flaw': 'destructive-default', 'label': 'Destructive default without confirmation', 'mode': 'found', 'grounded': True}
HINTS = [
    "Check five things: flag spelling, required marking, defaults, "
    "error text, examples \u2014 four are clean, one is not.",
    "Look at deploy.py:3: the flaw is one category judgment, not a typo hunt.",
    "Worked step: the five categories are inconsistent-flag-naming "
    "(Inconsistent flag naming); missing-required-marking (Missing "
    "required-argument marking); destructive-default (Destructive "
    "default without confirmation); cryptic-error (Cryptic error "
    "message); no-examples (No examples section). Reply with the ONE "
    "that fits.",
]


def seed_db(db_path: str) -> dict:
    """Plant one hinted card as the sole due card."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        payload = dict(PAYLOAD)
        payload["hints"] = HINTS
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '57', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(payload)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
