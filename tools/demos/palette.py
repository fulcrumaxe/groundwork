"""Improvement demo: palette CSS variables (I-51).

Full functionality: one :root token source (ink, paper, three page
accents, pass/fail/stale) emitted by palette.palette_css() and wired
into every page's stylesheet. seed_db changes no rows (tokens are
static); the chrome beats read the LIVE computed values off real pages
and render a swatch row from them, so the frame shows the tokens, not
a description of them.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "palette",
    "kind": "improvement",
    "batch": 5,
    "item": "I-51",
    "title": "Palette CSS variables",
    "blurb": "One :root token source for ink, paper, accents, pass/fail/stale.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-51",
         "title": "Palette CSS variables",
         "subtitle": "One :root token source for ink, paper, accents, pass/fail/stale."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-palette",
         "caption": "Status documents the improvement with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-palette')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The emitter in one line: a :root block with all eight tokens.",
         "commands": [
             ["python3", "-c",
              "from groundwork import palette as m; "
              "print(m.palette_css())"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "caption": "Every page inherits the tokens -- these swatches read the live :root values.",
         "js": ["() => { const root = getComputedStyle(document.documentElement); "
                "const names = ['--ink','--paper','--accent-due','--accent-modules',"
                "'--accent-history','--pass','--fail','--stale']; "
                "const d = document.createElement('div'); d.id = 'token-readout'; "
                "d.setAttribute('style', 'display:flex;flex-wrap:wrap;gap:8px;"
                "margin:12px 0 16px 0'); "
                "names.forEach(n => { const v = root.getPropertyValue(n).trim(); "
                "const s = document.createElement('span'); "
                "s.setAttribute('style', 'border:1px solid #999;background:#fff;"
                "padding:6px 10px;font-size:14px'); "
                "s.textContent = n + ' ' + v; "
                "const dot = document.createElement('i'); "
                "dot.setAttribute('style', 'display:inline-block;width:1em;height:1em;"
                "margin-right:6px;vertical-align:-2px;background:' + v + ';border:1px solid #666'); "
                "s.prepend(dot); d.appendChild(s); }); "
                "document.querySelector('main').prepend(d); return 'ok'; }"],
         "assert_js": "() => getComputedStyle(document.documentElement)"
                      ".getPropertyValue('--ink').trim()",
         "assert_want": "#1a1a1a"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules",
         "caption": "The shipped stylesheet carries the :root block -- tokens, not scattered hex.",
         "assert_js": "() => document.querySelector('style').textContent"
                      ".includes('--accent-modules:#8a5a00')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "One source for color.",
         "subtitle": "palette.py emits the :root block -- ink, paper, accents, pass/fail/stale."},
    ],
}


def seed_db(db_path: str) -> dict:
    """No fixture rows change: tokens are static per deploy.

    Touches the fixture copy read-only (counts modules to prove the
    served library is intact); the beats read live computed styles,
    which need no manipulated data.
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT COUNT(*) FROM modules").fetchone()
        return {"seeded": True, "modules": row[0] if row else 0}
    finally:
        con.close()
