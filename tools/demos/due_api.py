"""Feature demo: read-only due-queue API (Batch 2, F-451 second slice).

Full functionality: /api/due.json serves the live due queue -- the
same cards as the Due page -- as JSON. Chrome's JSON viewer clips
injected captions, so the beats film the Status link plus the Due
card it mirrors while a terminal beat calls the generator directly.
seed_db clears the queue to exactly one card, so the page card and
the JSON entry must name the same id.
"""
from __future__ import annotations

import re
import sqlite3

_ANCHOR_OK = re.compile(r"[A-Za-z0-9_-]+")


def _slug(text: str) -> str:
    """Mirror scrollpos.card_anchor: keep [A-Za-z0-9_-], cap at 48."""
    return "".join(_ANCHOR_OK.findall((text or "").strip()))[:48] or "unknown"


SCENARIO = {
    "id": "due-api",
    "kind": "feature",
    "batch": 2,
    "item": "F-451",
    "title": "Read-only due-queue API",
    "blurb": "The live due queue as JSON \u2014 same order as the Due page.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 2 - Feature F-451",
         "title": "Read-only due-queue API",
         "subtitle": "The live due queue as JSON -- same order as the Due page."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-api-due",
         "caption": "Status documents the due-queue slice beside the modules API.",
         "assert_js": "() => !!document.querySelector("
                      "\"#status-api-due a[href='/api/due.json']\")",
         "assert_want": "True"},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "focus": "#card-{seed_a}",
         "caption": "The Due page shows the same card the API serves.",
         "assert_js": "() => { const a = document.querySelector('#card-{seed_a}'); "
                      "return a ? a.textContent : 'missing'; }",
         "assert_want": "{seed_concept}"},
        {"type": "terminal", "duration": 11,
         "caption": "The generator: the queued card, same order, as JSON.",
         "commands": [
             ["python3", "-c",
              "import json, os; from groundwork import api as a; "
              "d = json.loads(a.due_json(os.environ.get('DEMO_DB', 'groundwork.db'))); "
              "print(json.dumps(d['due'][0], indent=1)); "
              "print('count:', d['count'], '| lead:', d['due'][0]['id'])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 2",
         "title": "The queue, everywhere.",
         "subtitle": "api.py serves the live due queue in page order."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One due card, no reviews anywhere (a single-card queue).

    Wiping reviews also suppresses probe cards, so due_json holds
    exactly this card and the page-vs-API comparison is airtight.
    """
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT cards.id, concepts.name FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " ORDER BY cards.due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid = card[0]
        con.execute("DELETE FROM reviews")
        con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z'"
                    " WHERE id=?", (cid,))
        con.commit()
        return {"seeded": True, "cid": cid, "a": _slug(cid),
                "concept": card[1]}
    finally:
        con.close()
