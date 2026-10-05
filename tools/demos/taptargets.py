"""Improvement demo: 44px minimum tap targets (I-66).

Full behavior: one --tap-min token (44px, WCAG 2.5.8) floors every
button and input via min-height, so the floor cannot drift across
selectors. A density-compact guard re-pins primary actions even when
compact mode squeezes everything else. Pure CSS -- no seed data.
"""
from __future__ import annotations

SCENARIO = {
    "id": "taptargets",
    "kind": "improvement",
    "batch": 11,
    "item": "I-66",
    "title": "Tap targets",
    "blurb": "Every button floors at 44px -- one token, zero drift.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Improvement I-66",
         "title": "Tap targets",
         "subtitle": "Thumbs welcome: 44px floors on every action."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-taptargets",
         "caption": "Status homes the floor: one token, min-height, compact guard.",
         "assert_js": "() => !!document.querySelector('#status-b11-taptargets')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: the token ships, the audit catches escapes.",
         "commands": [
             ["python3", "-c",
              "from groundwork import taptargets as m; "
              "print(m.target_css()[:140]); "
              "print('violation:', m.audit(\"<button style='min-height:20px'>x</button>\")); "
              "print('clean:', m.audit('<button>x</button>'))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The live Due page carries the floor -- every rule cites the token.",
         "assert_js": "() => Array.from(document.querySelectorAll('head style')).some("
                      "s => s.textContent.includes('--tap-min:44px'))",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Big enough to hit.",
         "subtitle": "taptargets.py floors the tap -- density cannot shrink it."},
    ],
}
