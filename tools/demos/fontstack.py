"""Improvement demo: offline-safe font pairing (I-54).

Full behavior: headings speak serif, body sans, code mono -- every
face ships with the OS, no webfonts, each stack ending in its
generic family. Font-family only (sizes stay with typescale).
Chrome proves the computed stacks on a live page; the terminal
proves the role lookup (unknown roles fail closed to body).
"""
from __future__ import annotations

SCENARIO = {
    "id": "fontstack",
    "kind": "improvement",
    "batch": 9,
    "item": "I-54",
    "title": "Font pairing",
    "blurb": "Serif headings, sans body, mono code -- every face ships with the OS.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Improvement I-54",
         "title": "Font pairing",
         "subtitle": "Three OS-native stacks -- no webfonts, no downloads."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-fontstack",
         "caption": "Status documents the pairing: serif headings, sans body, mono code.",
         "assert_js": "() => !!document.querySelector('#status-b9-fontstack')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: named OS stacks, unknown roles fall back to body.",
         "commands": [
             ["python3", "-c",
              "from groundwork import fontstack as m; "
              "print('heading:', m.stack_font('heading')); "
              "print('body:', m.stack_font('body')); "
              "print('unknown role falls back:', m.stack_for('nonsense') == m.BODY_STACK)"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/status",
         "caption": "Live computed proof: Georgia-led headings, DejaVu Sans body, generic terminators.",
         "assert_js": "() => getComputedStyle(document.body).fontFamily.includes('DejaVu Sans') && "
                      "getComputedStyle(document.querySelector('h1')).fontFamily.includes('Georgia')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "The CSS: :root --font-* variables plus font-family rules only.",
         "commands": [
             ["python3", "-c",
              "from groundwork import fontstack as m; "
              "print(m.stack_css()[:220])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Native faces only.",
         "subtitle": "fontstack.py pairs OS fonts -- generic families terminate every stack."},
    ],
}
