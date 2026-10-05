"""Improvement demo: visible keyboard focus rings (I-65).

Full behavior: one comma-grouped :focus-visible rule covers every
interactive selector, so keyboard users always see a ring while mouse
users stay calm. The ring color reuses the palette token, so dark mode
flows through with no fork. Pure CSS in the head wire -- no seed data.
"""
from __future__ import annotations

SCENARIO = {
    "id": "focusrings",
    "kind": "improvement",
    "batch": 11,
    "item": "I-65",
    "title": "Focus rings",
    "blurb": "Every control shows a keyboard ring -- mouse users stay calm.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Improvement I-65",
         "title": "Focus rings",
         "subtitle": "Keyboard users always see where they are."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-focusrings",
         "caption": "Status documents the ring: one rule, every selector, palette token.",
         "assert_js": "() => !!document.querySelector('#status-b11-focusrings')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: nine selectors covered, zero missing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import focusrings as m; "
              "print(m.css()[:150]); "
              "cov = m.covered_selectors(m.css()); "
              "print('covered:', len(cov['covered']), 'missing:', cov['missing'][:3])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The live Due page carries the ring -- inspect any head style.",
         "assert_js": "() => Array.from(document.querySelectorAll('head style')).some("
                      "s => s.textContent.includes(':focus-visible') && "
                      "s.textContent.includes('--focus-ring'))",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Tab with confidence.",
         "subtitle": "focusrings.py draws the ring -- the palette picks the color."},
    ],
}
