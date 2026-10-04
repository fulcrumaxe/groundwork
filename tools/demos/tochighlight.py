"""Improvement demo: sticky TOC highlight (I-6).

Full behavior: the sticky module TOC marks the section in view --
IntersectionObserver with a scroll fallback, reduced-motion safe.
Beats show the Status home, the pure active_for() mirror, the live
TOC on a module page, and a real scroll that lights up a link.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "tochighlight",
    "kind": "improvement",
    "batch": 6,
    "item": "I-6",
    "title": "Sticky TOC highlight",
    "blurb": "The sticky module TOC marks the section you are reading.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 6 - Improvement I-6",
         "title": "Sticky TOC highlight",
         "subtitle": "Scroll a module page -- the current lesson lights up."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b6-tochighlight",
         "caption": "Status names the mechanism: observer first, scroll fallback.",
         "assert_js": "() => !!document.querySelector('#status-b6-tochighlight')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: the last section at/above the line wins.",
         "commands": [
             ["python3", "-c",
              "from groundwork import tochighlight as m; "
              "off = [('a', 0), ('b', 400), ('c', 900)]; "
              "print(m.active_for(450, off)); print(m.active_for(-5, off))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/modules/{seed_mid}",
         "focus": "#readtime",
         "caption": "The live TOC: every lesson linked, wired for observation.",
         "assert_js": "() => document.querySelectorAll("
                      "'p.toc#readtime[data-toc] a[data-toc-link]').length > 1",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/modules/{seed_mid}",
         "focus": "#readtime",
         "caption": "Scroll deep -- the in-view lesson takes the highlight.",
         "js": ["() => { const els = document.querySelectorAll('[id^=\"lesson-\"]'); "
                "if (!els.length) return 'no-sections'; "
                "const last = els[els.length - 1]; "
                "if (last.scrollIntoView) last.scrollIntoView({block: 'center'}); "
                "else last.scrollIntoView(); return 'scrolled'; }"],
         "poll_js": "() => { const a = document.querySelector("
                    "'p.toc#readtime a.active'); "
                    "return a ? a.getAttribute('data-toc-link') : 'none'; }",
         "poll_want": "lesson-",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('p.toc#readtime a.active')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 6",
         "title": "Read with a map.",
         "subtitle": "tochighlight.py toggles a class -- no animated scrolling."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pick the module with the most concepts (needs 2+ TOC entries)."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT module_id FROM concepts GROUP BY module_id"
            " ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
        if not row:
            row = con.execute("SELECT id FROM modules LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no modules"}
        return {"seeded": True, "mid": row[0]}
    finally:
        con.close()
