"""Improvement demo: per-tier Bloom chip colors (I-56).

Full behavior: every Bloom tier gets its own chip color, shared by
Due card headers, the History list, and the coach table through one
hook (<span class='chip bloom-<tier>'). seed_db plants a type-57
(evaluate) card as the sole due card; /due wears the evaluate chip.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-bloomchips-57"

SCENARIO = {
    "id": "bloomchips",
    "kind": "improvement",
    "batch": 10,
    "item": "I-56",
    "title": "Bloom chip colors",
    "blurb": "Each Bloom tier has its own chip color in cards, History, and coach.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Improvement I-56",
         "title": "Bloom chip colors",
         "subtitle": "Eight tiers, eight colors -- weak skills read at a glance."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-bloomchips",
         "caption": "Status shows all eight tier chips -- one color per skill.",
         "assert_js": "() => !!document.querySelector('#status-b10-bloomchips') && "
                      "document.querySelectorAll('.chip[class*=\"bloom-\"]').length >= 8",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: known tiers color, unknown tiers fail closed to plain.",
         "commands": [
             ["python3", "-c",
              "from groundwork import bloomchips as m; "
              "print(m.chip_html('evaluate')); "
              "print(m.chip_class('bogus')); "
              "print(sorted(m.color_for('recall')))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "Due cards wear their tier -- this evaluate card reads at a glance.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!document.querySelector('.chip.bloom-evaluate'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "Skills, color-coded.",
         "subtitle": "bloomchips.py paints the hook -- cards, History, coach follow."},
    ],
}

FRONT = 'Study this --help output. It contains exactly ONE usability flaw. Reply with the flaw category (id or label).\nCategories:\n- inconsistent-flag-naming (Inconsistent flag naming)\n- missing-required-marking (Missing required-argument marking)\n- destructive-default (Destructive default without confirmation)\n- cryptic-error (Cryptic error message)\n- no-examples (No examples section)\n```text\nusage: deploy [--mode MODE] [--confirm] [--output DIR]\n\noptions:\n  --mode MODE   what to do: deploy or wipe (default: wipe)\n  --confirm     ask before applying changes\n  --output DIR  write the report to DIR (default: ./out)\n\nrequired: none. all options are optional.\n\nexamples:\n  deploy --mode deploy\n  deploy --mode wipe --confirm\n```'
BACK = 'Flaw: Destructive default without confirmation (destructive-default). The default mode wipes and confirmation is opt-in, so a bare run destroys data.'
PAYLOAD = {'help': 'usage: deploy [--mode MODE] [--confirm] [--output DIR]\n\noptions:\n  --mode MODE   what to do: deploy or wipe (default: wipe)\n  --confirm     ask before applying changes\n  --output DIR  write the report to DIR (default: ./out)\n\nrequired: none. all options are optional.\n\nexamples:\n  deploy --mode deploy\n  deploy --mode wipe --confirm', 'flaw': 'destructive-default', 'label': 'Destructive default without confirmation', 'mode': 'found', 'grounded': True}


def seed_db(db_path: str) -> dict:
    """Plant one type-57 (evaluate) card as the sole due card."""
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
