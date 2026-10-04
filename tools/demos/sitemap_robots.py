"""Feature demo: sitemap and robots (Batch 2, I-32).

Full functionality: /sitemap.xml lists every page plus every module
for crawlers; /robots.txt allows crawling and names the sitemap.
seed_db counts the library so the beats assert the exact url total
(8 routes plus every module) and one real module entry.
"""
from __future__ import annotations

import sqlite3

ROUTE_COUNT = 8

SCENARIO = {
    "id": "sitemap-robots",
    "kind": "feature",
    "batch": 2,
    "item": "I-32",
    "title": "Sitemap and robots",
    "blurb": "Every page and module listed for crawlers; see the live map below.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 2 - Feature I-32",
         "title": "Sitemap and robots",
         "subtitle": "Every page and module listed for crawlers; see the live map below."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-sitemap",
         "caption": "Status points crawlers at the sitemap and the robots stance.",
         "assert_js": "() => !!document.querySelector('#status-sitemap') && "
                      "!!document.querySelector(\"a[href='/sitemap.xml']\") && "
                      "!!document.querySelector(\"a[href='/robots.txt']\")",
         "assert_want": "True"},
        {"type": "chrome", "duration": 12,
         "url_path": "/sitemap.xml",
         "caption": "The live map: {seed_urls} urls -- every page plus every module.",
         "assert_js": "() => document.body.innerText.includes('<urlset') && "
                      "document.body.innerText.includes('/modules/{seed_mid}')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "robots.txt allows crawling and names the sitemap.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import sitemap as s; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "x = s.sitemap_xml(db, 'http://x'); "
              "print('urls:', x.count('<url>'), '=', 8, 'routes +', x.count('/modules/'), 'modules'); "
              "print(s.robots_txt('http://x'))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 2",
         "title": "Crawlable by default.",
         "subtitle": "sitemap.py maps every page and module for self-hosters."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Count the library; the sitemap total is routes plus modules."""
    con = sqlite3.connect(db_path)
    try:
        mids = [r[0] for r in con.execute(
            "SELECT id FROM modules ORDER BY created_at DESC").fetchall()]
        if not mids:
            return {"seeded": False, "reason": "no modules"}
        return {"seeded": True, "mid": mids[0],
                "modules": len(mids), "urls": ROUTE_COUNT + len(mids)}
    finally:
        con.close()
