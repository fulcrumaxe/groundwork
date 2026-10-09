"""Improvement demo: emoji-free icons (I-97).

Full behavior: an explicit allow/block codepoint policy scans the
whole tree (CI fails on new raw emoji-as-icon), while shipped markup
uses text PASS/FAIL stamps, SVG move buttons, and CSS shapes. The
enforcement path is the test gate, proven live below.
"""
from __future__ import annotations

SCENARIO = {
    "id": "emoji",
    "kind": "improvement",
    "batch": 18,
    "item": "I-97",
    "title": "Emoji-free icons",
    "blurb": "No raw emoji icons -- text words, SVG chevrons and CSS shapes, all readable with styles off.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Improvement I-97",
         "title": "Emoji-free icons",
         "subtitle": "A codepoint policy scans the tree; icons are text, SVG, and CSS shapes."},
        {"type": "terminal", "duration": 9,
         "caption": "The policy in one call: icon glyphs blocked, prose arrow allowed, violations located.",
         "commands": [
             ["python3", "-c",
              "from groundwork import emoji as m; "
              "print('check blocked:', m.is_blocked('\\u2705')); "
              "print('prose arrow allowed:', not m.is_blocked('\\u2192')); "
              "print(m.scan_text('Done \\U0001f389 ok'))"],
         ]},
        {"type": "terminal", "duration": 8,
         "caption": "The enforcement path: the gate scans the tree clean and trips on a planted glyph.",
         "commands": [
             ["python3", "-m", "unittest", "tests.test_emoji"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b18-emoji",
         "caption": "Status documents the vocabulary with a live back-to-top sample below.",
         "assert_js": "() => { const h = document.querySelector('#status-b18-emoji'); "
                      "return !!h && (h.nextElementSibling || {innerHTML: ''})"
                      ".innerHTML.includes('totop'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Readable with styles off.",
         "subtitle": "emoji.py scans the tree -- glyphs never ship as icons again."},
    ],
}
