"""Improvement demo: empty-state illustrations (I-69).

Full behavior: every page that can run dry gets one static inline-SVG
illustration in currentColor -- dark-mode and print safe, no emoji,
no animation elements by construction. Copy stays single-sourced in
empty.py; this module only decorates. A bogus repo filter empties the
Modules library live; the art rides along.
"""
from __future__ import annotations

SCENARIO = {
    "id": "emptyart",
    "kind": "improvement",
    "batch": 11,
    "item": "I-69",
    "title": "Empty-state art",
    "blurb": "Dry pages get calm line art -- static SVG, zero motion.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Improvement I-69",
         "title": "Empty-state art",
         "subtitle": "Nothing here -- said kindly, drawn in currentColor."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-emptyart",
         "caption": "Status documents the set: one static SVG per dryable page.",
         "assert_js": "() => !!document.querySelector('#status-b11-emptyart')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: inline SVG per page key, animation-free by construction.",
         "commands": [
             ["python3", "-c",
              "from groundwork import emptyart as m; "
              "print(m.art_for('modules')[:140]); "
              "print('animate in due art:', '<animate>' in m.art_for('due')); "
              "print('unknown key falls back:', m.art_for('nope')[:60])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules?repo=demo-empty-nope",
         "caption": "A repo with no modules: the art shows, the next step stays.",
         "assert_js": "() => !!document.querySelector('svg.empty-art') && "
                      "document.body.innerText.includes('No modules for this project yet')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Empty, not bleak.",
         "subtitle": "emptyart.py decorates the dry -- empty.py keeps the words."},
    ],
}
