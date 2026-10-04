"""Feature demo: Anki export (Batch 1).

Full functionality: every card as one tab-separated row (front, back,
tags) via /export/anki.tsv, linked from Modules and counted on Status.
Chrome downloads TSV instead of rendering it, so the beats film the
link plus the live counts while a terminal beat calls the generator
directly. seed_db tags one card front with a marker the export must
carry through.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "anki-export",
    "kind": "feature",
    "batch": 1,
    "title": "Anki export",
    "blurb": "All cards as tab-separated import: front, back, tags.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Feature anki-export",
         "title": "Anki export",
         "subtitle": "All cards as tab-separated import: front, back, tags."},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules#exports",
         "focus": "#exports",
         "caption": "Modules carries the export links: Anki TSV beside the RSS feed.",
         "assert_js": "() => !!document.querySelector('#exports') && "
                      "!!document.querySelector(\"a[href='/export/anki.tsv']\")",
         "assert_want": "True"},
        {"type": "terminal", "duration": 11,
         "caption": "The generator, called directly: one tab-separated row per card.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import exports as e; "
              "t = e.anki_tsv(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "ls = [l for l in t.splitlines() if l.strip()]; "
              "print('rows:', len(ls)); "
              "print('fields in row 1:', len(ls[0].split(chr(9))) if ls else 0); "
              "print('seed marker present:', '{seed_marker}' in t)"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/status#status-exports",
         "focus": "#status-exports",
         "caption": "Status shows the live counts behind the export: cards in modules.",
         "assert_js": "() => !!document.querySelector('#status-exports') && "
                      "document.body.innerText.includes('Anki TSV')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Cards, portable.",
         "subtitle": "exports.py renders every card as front, back, tags."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Tag one card front with a marker the TSV must carry through."""
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id FROM cards ORDER BY id LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        marker = "AnkiSeed42"
        con.execute(
            "UPDATE cards SET front = COALESCE(front, '') || ' ' || ?"
            " WHERE id=?", (marker, card[0]))
        con.commit()
        n = con.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        return {"seeded": True, "card_id": card[0],
                "marker": marker, "cards": n}
    finally:
        con.close()
