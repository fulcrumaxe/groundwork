"""Improvement demo: tiny Python/TS syntax highlighter (I-62).

Full behavior: a single-pass tokenizer plus escape-first renderer
colors Python and TypeScript snippets with no dependencies --
comments, strings, numbers, keywords, builtins -- while unknown
languages fail closed to plain text and raw markup can never leak.
Chrome proves the live demo block; the terminal proves the tokens.
"""
from __future__ import annotations

SCENARIO = {
    "id": "highlight",
    "kind": "improvement",
    "batch": 10,
    "item": "I-62",
    "title": "Tiny syntax highlight",
    "blurb": "Python/TS snippets color with no dependencies -- unknown langs stay plain.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Improvement I-62",
         "title": "Tiny syntax highlight",
         "subtitle": "Tokens, colored -- one pass, zero dependencies."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-highlight",
         "caption": "Status documents the scanner: single pass, escape-first, fail-closed.",
         "assert_js": "() => !!document.querySelector('#status-b10-highlight')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: known words tokenize, unknown languages stay plain.",
         "commands": [
             ["python3", "-c",
              "from groundwork import highlight as m; "
              "print(m.tokenize('def f(x): return x + 1')); "
              "print(m.highlight_html('x = 1  # set', 'python')[:130]); "
              "print(m.tokenize('x', 'cobol'))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/status",
         "focus": "#status-b10-highlight",
         "caption": "The live demo block colors keywords, strings, comments -- tokens ship in the head.",
         "assert_js": "() => !!document.querySelector('.hl .tok-keyword') && "
                      "!!document.querySelector('.hl .tok-comment') && "
                      "Array.from(document.querySelectorAll('head style')).some("
                      "s => s.textContent.includes('.tok-keyword'))",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "Color, no baggage.",
         "subtitle": "highlight.py scans once -- escape-first, markup never leaks."},
    ],
}
