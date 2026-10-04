"""Feature demo: module sharing (Batch 1).

Full functionality: export-module writes a module (concepts, cards,
lessons) to JSON; import-module loads it into another database while
reviews stay private and scheduling restarts fresh; re-imports skip as
duplicates instead of merging. seed_db picks the module with the most
cards and plants a review on it so the source-vs-imported contrast is
real.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "module-sharing",
    "kind": "feature",
    "batch": 1,
    "title": "Module sharing",
    "blurb": "Export a module to JSON, import it into any Groundwork DB. Reviews stay private.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Feature module-sharing",
         "title": "Module sharing",
         "subtitle": "Export a module to JSON, import it anywhere. Reviews stay private."},
        {"type": "chrome", "duration": 8,
         "url_path": "/status#status-share",
         "focus": "#status-share",
         "caption": "Status documents the share loop: export-module out, import-module in.",
         "assert_js": "() => !!document.querySelector('#status-share') && "
                      "document.body.innerText.includes('export-module')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 13,
         "caption": "Round trip: export to JSON, import into a scratch DB, re-import skips.",
         "commands": [
             ["bash", "-lc",
              "rm -f /tmp/demo-share.json /tmp/demo-share-dest.db && "
              "python3 -m groundwork --db \"$DEMO_DB\" export-module --module {seed_mid} --out /tmp/demo-share.json && "
              "python3 -m groundwork --db /tmp/demo-share-dest.db import-module --in /tmp/demo-share.json && "
              "python3 -m groundwork --db /tmp/demo-share-dest.db import-module --in /tmp/demo-share.json"],
             ["python3", "-c",
              "import os, sqlite3; "
              "s = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "d = sqlite3.connect('/tmp/demo-share-dest.db'); "
              "src = s.execute(\"SELECT COUNT(*) FROM reviews JOIN cards ON cards.id = reviews.card_id "
              "JOIN concepts ON concepts.id = cards.concept_id "
              "WHERE concepts.module_id = '{seed_mid}'\").fetchone()[0]; "
              "print('source reviews:', src, '-> imported:', d.execute('SELECT COUNT(*) FROM reviews').fetchone()[0])"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/modules/{seed_mid}",
         "caption": "The shared module: concepts and cards travel, reviews stay behind.",
         "assert_js": "() => location.pathname.includes('{seed_mid}') && "
                      "!!document.querySelector(\"a[href='/modules']\")",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Teaching travels; progress stays.",
         "subtitle": "share.py exports content only -- duplicates skip, never merge."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pick the module with the most cards; plant a review on it.

    The richest module makes the round trip worth filming. The planted
    review proves the privacy half: the source has reviews, the
    freshly imported copy has none.
    """
    con = sqlite3.connect(db_path)
    try:
        m = con.execute(
            "SELECT concepts.module_id FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " GROUP BY concepts.module_id"
            " ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
        if not m:
            m = con.execute(
                "SELECT id FROM modules LIMIT 1").fetchone()
        if not m:
            return {"seeded": False, "reason": "no modules"}
        mid = m[0]
        card = con.execute(
            "SELECT cards.id FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=? LIMIT 1", (mid,)).fetchone()
        if card:
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, 4, 3, 'share seed')", (card[0],))
        con.commit()
        n_concepts = con.execute(
            "SELECT COUNT(*) FROM concepts WHERE module_id=?",
            (mid,)).fetchone()[0]
        n_cards = con.execute(
            "SELECT COUNT(*) FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=?", (mid,)).fetchone()[0]
        return {"seeded": True, "mid": mid,
                "concepts": n_concepts, "cards": n_cards}
    finally:
        con.close()
