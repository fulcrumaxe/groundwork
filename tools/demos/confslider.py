"""Improvement demo: segmented confidence control (I-64).

Full behavior: Due cards used to render five bare name='confidence'
radios -- now a tappable segmented 1-5 control (Unsure..Sure) with the
same POST contract, native arrow-key behavior, and zero JS. seed_db
plants one card as the sole due card; /due shows the segments.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-confslider-57"

SCENARIO = {
    "id": "confslider",
    "kind": "improvement",
    "batch": 11,
    "item": "I-64",
    "title": "Confidence slider",
    "blurb": "A tappable 1-5 segmented control -- same POST, zero JS.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Improvement I-64",
         "title": "Confidence slider",
         "subtitle": "Five bare radios become one tappable control."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-confslider",
         "caption": "Status homes the control: same field, same values, better surface.",
         "assert_js": "() => !!document.querySelector('#status-b11-confslider')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: garbage clamps to 3, the renderer keeps the contract.",
         "commands": [
             ["python3", "-c",
              "from groundwork import confslider as m; "
              "print('normalize:', m.normalize('bogus'), m.normalize(9), m.normalize(2)); "
              "print(m.slider_html(4)[:160])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#confidence",
         "caption": "The lead card wears the segments -- five tappable stops, one field.",
         "assert_js": "() => document.querySelectorAll("
                      "\"#confidence input[name='confidence']\").length === 5",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "How sure? Tap it.",
         "subtitle": "confslider.py segments the guess -- grading never notices."},
    ],
}

FRONT = 'Study this --help output. It contains exactly ONE usability flaw. Reply with the flaw category (id or label).\nCategories:\n- inconsistent-flag-naming (Inconsistent flag naming)\n- missing-required-marking (Missing required-argument marking)\n- destructive-default (Destructive default without confirmation)\n- cryptic-error (Cryptic error message)\n- no-examples (No examples section)\n```text\nusage: deploy [--mode MODE] [--confirm] [--output DIR]\n\noptions:\n  --mode MODE   what to do: deploy or wipe (default: wipe)\n  --confirm     ask before applying changes\n  --output DIR  write the report to DIR (default: ./out)\n\nrequired: none. all options are optional.\n\nexamples:\n  deploy --mode deploy\n  deploy --mode wipe --confirm\n```'
BACK = 'Flaw: Destructive default without confirmation (destructive-default). The default mode wipes and confirmation is opt-in, so a bare run destroys data.'
PAYLOAD = {'help': 'usage: deploy [--mode MODE] [--confirm] [--output DIR]\n\noptions:\n  --mode MODE   what to do: deploy or wipe (default: wipe)\n  --confirm     ask before applying changes\n  --output DIR  write the report to DIR (default: ./out)\n\nrequired: none. all options are optional.\n\nexamples:\n  deploy --mode deploy\n  deploy --mode wipe --confirm', 'flaw': 'destructive-default', 'label': 'Destructive default without confirmation', 'mode': 'found', 'grounded': True}


def seed_db(db_path: str) -> dict:
    """Plant one card as the sole due card."""
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
            " VALUES(?, ?, '57', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
