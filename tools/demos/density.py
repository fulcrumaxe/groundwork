"""Improvement demo: compact density (I-89).

Full behavior: the header button on every page toggles a
data-density='compact' override (tighter gaps, smaller type, tap
floors untouched) persisted in localStorage with no server round
trip. The home-page beat clicks the real button and asserts the
attribute plus the stored choice.
"""
from __future__ import annotations

SCENARIO = {
    "id": "density",
    "kind": "improvement",
    "batch": 13,
    "item": "I-89",
    "title": "Compact density",
    "blurb": "One header button densifies small screens -- tap targets stay full-size.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Improvement I-89",
         "title": "Compact density",
         "subtitle": "One header button shrinks gaps and type -- tap targets stay full-size."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-density",
         "caption": "Status documents the override, the localStorage switch, and the button.",
         "assert_js": "() => !!document.querySelector('#status-b13-density')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: real scale tokens shrink, tap floors never do.",
         "commands": [
             ["python3", "-c",
              "from groundwork import density as m; css = m.density_css(); js = m.toggle_js(); "
              "print('override:', 'data-density' in css and '--sp-section' in css and '--fs-small' in css); "
              "print('tap floor kept:', 'tap-min' not in css and 'min-height' not in css); "
              "print('stored:', 'localStorage' in js and 'fetch' not in js)"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/",
         "caption": "One click: compact gaps and type, persisted -- click again to go home.",
         "js": ["() => { const b = document.querySelector('#gw-density-toggle'); "
                "if (!b) return 'no-button'; b.click(); return 'clicked'; }"],
         "assert_js": "() => document.documentElement.getAttribute('data-density') === 'compact' && "
                      "document.querySelector('#gw-density-toggle').textContent === 'Comfortable'",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Small screens, denser page.",
         "subtitle": "density.py -- header button and script on every page, no round trip."},
    ],
}
