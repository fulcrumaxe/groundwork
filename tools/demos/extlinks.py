"""Improvement demo: external vs internal link distinction (I-31).

Full behavior: extlinks.classify()/decorate() mark externals with a
corner marker + screen-reader note while internal routes, repo paths,
and skip shapes pass through. seed_db touches no tables (returns a
module id for the live-page negative beat); Status shows the shipped
sample, a real module page proves zero markers, terminal beats run
the truth table + hostile passthrough + idempotence.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "extlinks",
    "kind": "improvement",
    "batch": 8,
    "item": "I-31",
    "title": "Spot external links at a glance",
    "blurb": ("External links now show a marker plus screen-reader note "
              "while internal routes and repo paths stay plain."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Improvement I-31",
         "title": "Spot external links at a glance",
         "subtitle": ("External links get a marker and a screen-reader "
                      "note -- internal routes stay plain.")},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-extlinks",
         "caption": "Status documents the rule: externals marked, internals untouched.",
         "assert_js": "() => !!document.querySelector('#status-b8-extlinks')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: externals decorate, "
                     "everything else passes through."),
         "commands": [
             ["python3", "-c",
              "from groundwork import extlinks as m; "
              "print(m.classify('https://example.com/x'), m.classify('/status'), "
              "m.classify('groundwork/extlinks.py'), m.classify('#frag')); "
              "print(m.decorate(\"<a href='https://example.com/x'>Docs</a>\"))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "caption": ("A real module page: links everywhere, zero external "
                     "markers -- internal stays plain."),
         "assert_js": "() => !!document.querySelector('#sitenav a[href]') && "
                      "!document.querySelector('.ext-marker')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": ("Hostile input passes through untouched -- and "
                     "decoration never doubles."),
         "commands": [
             ["python3", "-c",
              "from groundwork import extlinks as m; "
              "print(m.decorate(\"<a href=https://example.com/>U</a>\") == "
              "\"<a href=https://example.com/>U</a>\"); "
              "once = m.decorate(\"<a href='https://example.com/'>E</a>\"); "
              "print(m.decorate(once) == once)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Glanceable, and safe.",
         "subtitle": ("extlinks.py decorates externals only -- hostile "
                      "hrefs pass through.")},
    ],
}


def seed_db(db_path: str) -> dict:
    """Db-free module: return a live module id, write nothing."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT id FROM modules LIMIT 1").fetchone()
    finally:
        con.close()
    if not row:
        return {"seeded": False, "reason": "no modules"}
    return {"seeded": True, "mid": row[0]}
