"""Feature demo: RSS feed (Batch 1).

Full functionality: the latest learning modules as RSS 2.0 via
/feed.xml, linked from Modules. Chrome renders the feed as text, so
the beats film the raw items plus the Modules link while a terminal
beat counts items through the generator. seed_db prepends a marker to
the newest module summary so the first item is verifiably ours.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "rss-feed",
    "kind": "feature",
    "batch": 1,
    "item": "F-373",
    "title": "RSS feed",
    "blurb": "Learning modules as RSS 2.0 for external readers.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Feature rss-feed",
         "title": "RSS feed",
         "subtitle": "Learning modules as RSS 2.0 for external readers."},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules#exports",
         "focus": "#exports",
         "caption": "The RSS feed link lives beside the Anki export on Modules.",
         "assert_js": "() => !!document.querySelector('#exports') && "
                      "!!document.querySelector(\"a[href='/feed.xml']\")",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/feed.xml",
         "caption": "The live feed: {seed_items} latest sessions as RSS 2.0 items.",
         "assert_js": "() => document.body.innerText.includes(\"<rss version='2.0'>\") && "
                      "document.body.innerText.includes('{seed_marker}') && "
                      "document.body.innerText.split('<item>').length - 1 > 0",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Same feed, counted straight from the generator.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import exports as e; "
              "x = e.feed_xml(os.environ.get('DEMO_DB', 'groundwork.db'), 'http://x'); "
              "print('rss tag:', \"<rss version='2.0'>\" in x); "
              "print('items:', x.count('<item>')); "
              "print('seed marker:', '{seed_marker}' in x)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Sessions, subscribable.",
         "subtitle": "exports.py serves the latest modules as RSS 2.0 items."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Prepend a marker to the newest module summary (first feed item)."""
    con = sqlite3.connect(db_path)
    try:
        m = con.execute(
            "SELECT id FROM modules ORDER BY created_at DESC LIMIT 1").fetchone()
        if not m:
            return {"seeded": False, "reason": "no modules"}
        marker = "RSSSeed42"
        con.execute(
            "UPDATE modules SET task_summary = ? || ' ' || COALESCE(task_summary, id)"
            " WHERE id=?", (marker, m[0]))
        con.commit()
        n = con.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
        return {"seeded": True, "mid": m[0],
                "marker": marker, "items": min(50, n)}
    finally:
        con.close()
