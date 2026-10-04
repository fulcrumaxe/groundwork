"""Improvement demo: global header search (I-2).

Full behavior: every page carries the header box (#site-search, `/`
to focus); /search?q= ranks concepts, modules, and symbols with a
next-step empty state. The interaction beat types into the live box
and submits, polling the ranked results.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "search",
    "kind": "improvement",
    "batch": 6,
    "item": "I-2",
    "title": "Global header search",
    "blurb": "One box in the header searches concepts, modules, and symbols.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Improvement I-2",
         "title": "Global header search",
         "subtitle": "One box in the header -- concepts, modules, symbols. Press / anywhere."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-search",
         "caption": "Status documents the improvement: one box, three record kinds.",
         "assert_js": "() => !!document.querySelector('#status-b6-search')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: title hits weigh 3, blank queries stay quiet.",
         "commands": [
             ["python3", "-c",
              "from groundwork import search as m; "
              "recs = [{'kind': 'module', 'title': 'alpha', 'url': '/modules/a', 'detail': 'first'}, "
              "{'kind': 'concept', 'title': 'beta', 'url': '/modules/a', 'detail': 'fn'}]; "
              "print([r['title'] for r in m.search(recs, 'alpha')]); "
              "print(m.search(recs, '')); print(m.search(recs, 'zzz'))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/search?q=groundwork",
         "focus": "#search-results",
         "caption": "Ranked hits as chips and links -- the results list, framed.",
         "assert_js": "() => !!document.querySelector('#search-results')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/",
         "caption": "Type in the header box and submit -- the ranked list answers.",
         "js": ["() => { const box = document.getElementById('site-search'); "
                "if (!box) return 'no-box'; box.value = 'groundwork'; "
                "box.form.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "match(es) for",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('#search-results')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Ask from anywhere.",
         "subtitle": "search.py ranks in memory -- no DB, no cookies, just the box."},
    ],
}
