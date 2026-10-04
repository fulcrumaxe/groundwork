"""Improvement demo: footer sitemap (I-10).

Full behavior: every page ends in a grouped site map -- Due,
Modules, History, About -- plus the tagline and a Status link, so no
page is a dead end. Beats show the Status home, the pure check()
contract, and the live footer on two different pages.
"""
from __future__ import annotations

SCENARIO = {
    "id": "footnav",
    "kind": "improvement",
    "batch": 6,
    "item": "I-10",
    "title": "Footer sitemap",
    "blurb": "Every page ends in a grouped site map -- no dead ends.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Improvement I-10",
         "title": "Footer sitemap",
         "subtitle": "Due, Modules, History, About -- grouped at the foot of every page."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-footnav",
         "caption": "Status names the promise: tagline, four groups, a Status link.",
         "assert_js": "() => !!document.querySelector('#status-b6-footnav')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: every footer href must name a known route.",
         "commands": [
             ["python3", "-c",
              "from groundwork import footnav as m; "
              "print('orphans:', m.check()); "
              "print('groups:', [g for g, _ in m.sections()])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/",
         "focus": "#site-footer",
         "caption": "The live footer on the front door -- grouped, labelled, current-marked.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"footer#site-footer nav[aria-label='Site map']\"); "
                      "return !!f && f.textContent.includes('History'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#site-footer",
         "caption": "Same footer in the queue -- the map follows you everywhere.",
         "assert_js": "() => { const f = document.querySelector("
                      "'footer#site-footer'); "
                      "return !!f && !!f.querySelector(\"a[href='/status']\"); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "No dead ends.",
         "subtitle": "footnav.py renders groups -- check() keeps hrefs honest."},
    ],
}
