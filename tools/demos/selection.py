"""Improvement demo: selection accent (I-85).

Full behavior: selected text renders the page accent (--accent-due,
ink text) on every page via the head wire, while forced-colors users
keep native selection. The /status beat select-alls <main> so the
screenshot films real highlighted text, not a swatch.
"""
from __future__ import annotations

SCENARIO = {
    "id": "selection",
    "kind": "improvement",
    "batch": 13,
    "item": "I-85",
    "title": "Selection accent",
    "blurb": "Selected text wears the page accent -- forced-colors keeps native.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Improvement I-85",
         "title": "Selection accent",
         "subtitle": "Selected text wears the page accent -- not browser blue."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-selection",
         "caption": "Status documents the one ::selection rule on the real accent token.",
         "assert_js": "() => !!document.querySelector('#status-b13-selection')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: accent ground, ink text, high-contrast escape.",
         "commands": [
             ["python3", "-c",
              "from groundwork import selection as m; css = m.selection_css(); "
              "print('rule:', '::selection' in css, '| token:', '--accent-due' in css); "
              "print('escape:', 'forced-colors' in css and 'Highlight' in css)"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/status",
         "caption": "Drag-select, filmed: every word highlights in the page accent.",
         "js": ["() => { const m = document.querySelector('main'); "
                "if (!m) return 'no-main'; "
                "window.getSelection().selectAllChildren(m); "
                "return 'selected:' + window.getSelection().toString().length; }"],
         "assert_js": "() => { const css = [...document.querySelectorAll('style')]"
                      ".map(s => s.textContent).join('\\n'); "
                      "return css.includes('::selection') && "
                      "window.getSelection().toString().length > 100; }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Select in palette.",
         "subtitle": "selection.py -- one rule in the head wire, on every page."},
    ],
}
