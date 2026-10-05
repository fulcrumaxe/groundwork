"""Improvement demo: visually differentiated hint tiers (I-63).

Full behavior: card hints build [nudge, pointer, worked] but used to
render identically -- now each tier gets its own class and label so
cheap help reads apart from a full worked step. seed_db plants one
hinted card with two prior attempts, unlocking all three tiers; /due
shows nudge, pointer, and worked disclosures side by side.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-hinttiers-57"

SCENARIO = {
    "id": "hinttiers",
    "kind": "improvement",
    "batch": 11,
    "item": "I-63",
    "title": "Hint tiers",
    "blurb": "Nudge, pointer, worked step -- each hint tier reads distinct.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Improvement I-63",
         "title": "Hint tiers",
         "subtitle": "Cheap help and worked steps finally look different."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-hinttiers",
         "caption": "Status documents the three tiers: nudge, pointer, worked step.",
         "assert_js": "() => !!document.querySelector('#status-b11-hinttiers')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: position maps to tier, tier maps to class and label.",
         "commands": [
             ["python3", "-c",
              "from groundwork import hinttiers as m; "
              "print([m.tier_of(i) for i in range(3)]); "
              "print(m.tier_class(1), '|', m.tier_label(2)); "
              "print(m.hint_html('try smaller', 1, 3)[:120]); "
              "print('rules ship:', m.has_hinttier_rules(m.hinttiers_css()))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id} details.hint-nudge",
         "caption": "Two attempts in, all three tiers show -- nudge, pointer, worked.",
         "assert_js": "() => document.querySelectorAll("
                      "\"details.hint-nudge,details.hint-pointer,"
                      "details.hint-worked\").length >= 3",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Help, honestly labeled.",
         "subtitle": "hinttiers.py tiers the reveal -- learners pace their own help."},
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
    """Plant one hinted card with two attempts as the sole due card."""
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
        for grade in (2, 2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES(?, ?, 3)",
                (CARD_ID, grade))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
