"""Improvement demo: Due card entrance stagger, CSS only (I-59).

Full behavior: Due cards fade up one after another in 35ms steps via
a load-played keyframe plus nth-child animation-delay offsets, capped
at 245ms -- pure CSS, no framework, no script, with a
prefers-reduced-motion override. seed_db plants one due card so the
queue exists; Chrome proves the queue and the shipped keyframe.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-stagger-57"

SCENARIO = {
    "id": "stagger",
    "kind": "improvement",
    "batch": 10,
    "item": "I-59",
    "title": "Due card stagger",
    "blurb": "Due cards fade up in 35ms steps -- pure CSS, no framework.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Improvement I-59",
         "title": "Due card stagger",
         "subtitle": "Cards arrive one after another -- 35ms apart."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-stagger",
         "caption": "Status documents the cascade: keyframe plus per-card delays, capped.",
         "assert_js": "() => !!document.querySelector('#status-b10-stagger')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: 35ms a card, capped at 245ms, bad input delays zero.",
         "commands": [
             ["python3", "-c",
              "from groundwork import stagger as m; "
              "print([m.delay_for(i) for i in (1, 2, 8, 99, 'x')]); "
              "print('cap:', m.max_delay_ms())"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The queue plays the entrance -- each card fades up in turn.",
         "assert_js": "() => !!document.getElementById('card-{seed_card_id}') && "
                      "Array.from(document.querySelectorAll('head style')).some("
                      "s => s.textContent.includes('gw-card-in'))",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "Arrive, don't pop.",
         "subtitle": "stagger.py cascades the queue -- CSS only, motion-safe."},
    ],
}

FRONT = 'Study this --help output. It contains exactly ONE usability flaw. Reply with the flaw category (id or label).\nCategories:\n- inconsistent-flag-naming (Inconsistent flag naming)\n- missing-required-marking (Missing required-argument marking)\n- destructive-default (Destructive default without confirmation)\n- cryptic-error (Cryptic error message)\n- no-examples (No examples section)\n```text\nusage: deploy [--mode MODE] [--confirm] [--output DIR]\n\noptions:\n  --mode MODE   what to do: deploy or wipe (default: wipe)\n  --confirm     ask before applying changes\n  --output DIR  write the report to DIR (default: ./out)\n\nrequired: none. all options are optional.\n\nexamples:\n  deploy --mode deploy\n  deploy --mode wipe --confirm\n```'
BACK = 'Flaw: Destructive default without confirmation (destructive-default). The default mode wipes and confirmation is opt-in, so a bare run destroys data.'
PAYLOAD = {'help': 'usage: deploy [--mode MODE] [--confirm] [--output DIR]\n\noptions:\n  --mode MODE   what to do: deploy or wipe (default: wipe)\n  --confirm     ask before applying changes\n  --output DIR  write the report to DIR (default: ./out)\n\nrequired: none. all options are optional.\n\nexamples:\n  deploy --mode deploy\n  deploy --mode wipe --confirm', 'flaw': 'destructive-default', 'label': 'Destructive default without confirmation', 'mode': 'found', 'grounded': True}


def seed_db(db_path: str) -> dict:
    """Plant one card as the sole due card so the queue exists."""
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
