"""Improvement demo: border-radius scale (I-67).

Full behavior: cards take --r-card (12px), controls --r-control (8px),
chips --r-chip (999px) -- one :root token source replaces hardcoded
literals across the page CSS, so corner rhythm cannot drift. Pure
tokens in the head wire -- no seed data.
"""
from __future__ import annotations

SCENARIO = {
    "id": "radius",
    "kind": "improvement",
    "batch": 11,
    "item": "I-67",
    "title": "Corner radii",
    "blurb": "Cards 12, controls 8, chips pill -- one token source.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Improvement I-67",
         "title": "Corner radii",
         "subtitle": "Three radii, one :root block, zero magic literals."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-radius",
         "caption": "Status homes the scale: card, control, chip -- hairlines stay literal.",
         "assert_js": "() => !!document.querySelector('#status-b11-radius')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: legacy literals map to tokens, off-scale maps to none.",
         "commands": [
             ["python3", "-c",
              "from groundwork import radius as m; "
              "print(m.radius_css()); "
              "print('10px ->', m.token_for('10px')); "
              "print('4px ->', repr(m.token_for('4px')))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The live Due page carries the scale -- every corner cites a token.",
         "assert_js": "() => Array.from(document.querySelectorAll('head style')).some("
                      "s => s.textContent.includes('--r-card:12px'))",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Corners in step.",
         "subtitle": "radius.py tokens the curve -- migration is mechanical."},
    ],
}
