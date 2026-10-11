"""Improvement demo: dyslexia-friendly reading toggle (I-139).

Full behavior: one header button on every page switches to roomier
line-height, wider letter/word spacing, ragged-right text — persisted
in localStorage with no server round trip. No seed data: the toggle
is presentation-only.
"""
from __future__ import annotations

SCENARIO = {
    "id": "dyslexia",
    "kind": "improvement",
    "batch": 22,
    "item": "I-139",
    "title": "Dyslexia-friendly reading",
    "blurb": "One header button widens spacing and line-height — reading stays comfy.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Improvement I-139",
         "title": "Dyslexia-friendly reading",
         "subtitle": "Roomier type on demand -- one click, remembered."},
        {"type": "chrome", "duration": 10,
         "url_path": "/status",
         "focus": "#status-b22-dyslexia",
         "js": ["() => { document.getElementById('gw-dys-toggle').click(); return 'clicked'; }"],
         "caption": "One click flips the page to friendlier reading and persists it.",
         "assert_js": "() => document.documentElement.getAttribute('data-dys') === 'on' && document.getElementById('gw-dys-toggle').textContent === 'Default' ? 'readable' : 'default'",
         "assert_want": "readable"},
        {"type": "terminal", "duration": 8,
         "caption": "Three emitters: CSS override, localStorage switch, header button.",
         "commands": [
             ["python3", "-c",
              "from groundwork import dyslexia as m; "
              "print('css:', [l for l in m.dyslexia_css().split('}') if 'line-height' in l][0] + '}'); "
              "print('store key:', m.STORE_KEY, '| attr:', m.ATTR, '| id:', m.TOGGLE_ID); "
              "print('button:', m.toggle_html()); "
              "print('no fetch:', 'fetch' not in m.toggle_js(), '| persists:', 'localStorage' in m.toggle_js())"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/reviews",
         "caption": "The button rides the header on every page, not just Status.",
         "assert_js": "() => !!document.querySelector('#gw-dys-toggle')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Readable, remembered.",
         "subtitle": "dyslexia.py widens type -- local only, no round trip."},
    ],
}


def seed_db(db_path: str) -> dict:
    """No fixture data: the toggle is presentation-only."""
    return {"seeded": False, "reason": "presentation-only, no data"}
