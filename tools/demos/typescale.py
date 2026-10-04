"""Improvement demo: modular type scale (I-53).

Full behavior: every font size comes from one ratio-based scale
(BASE 16, ratio 1.25) -- :root --fs-* variables plus element rules
that reference only those variables. Chrome proves the computed
h1 size on a live page plus the shipped variables; the terminal
proves the lookup (unknown steps fail closed to body) and the CSS.
"""
from __future__ import annotations

SCENARIO = {
    "id": "typescale",
    "kind": "improvement",
    "batch": 9,
    "item": "I-53",
    "title": "Type scale",
    "blurb": "One ratio-based scale for every font size -- no scattered literals.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Improvement I-53",
         "title": "Type scale",
         "subtitle": "Display to code -- every size from one ratio."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-typescale",
         "caption": "Status documents the scale: ratio-derived steps, one token each.",
         "assert_js": "() => !!document.querySelector('#status-b9-typescale')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: ratio-derived sizes, unknown steps fall back to body.",
         "commands": [
             ["python3", "-c",
              "from groundwork import typescale as m; "
              "print('h1:', m.px_for('h1'), 'body:', m.px_for('body'), 'small:', m.px_for('small')); "
              "print('unknown step:', m.px_for('nonsense'))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/status",
         "caption": "Live computed proof: the h1 renders at exactly 39.06px from the variable.",
         "assert_js": "() => { const h = document.querySelector('h1'); "
                      "return !!h && getComputedStyle(h).fontSize === '39.06px' && "
                      "getComputedStyle(document.documentElement).getPropertyValue('--fs-h1').trim() === '39.06px'; }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "The CSS: :root variables, element rules referencing only the variables.",
         "commands": [
             ["python3", "-c",
              "from groundwork import typescale as m; "
              "print(m.scale_css()[:220])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "One scale, every size.",
         "subtitle": "typescale.py single-sources sizes -- ratio 1.25 on a 16px base."},
    ],
}
