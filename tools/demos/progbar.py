"""Improvement demo: animated progress bars, reduced-motion safe (I-57).

Full behavior: a width-only transition on the existing progress
selectors (.bar i, #readprogress span) eases fills over 200ms, with
a prefers-reduced-motion override that jumps instantly. No markup
or JS edits -- the selectors already carry inline widths. Chrome
proves the bars and the shipped rule; the terminal proves the CSS
and the clamp.
"""
from __future__ import annotations

SCENARIO = {
    "id": "progbar",
    "kind": "improvement",
    "batch": 10,
    "item": "I-57",
    "title": "Progress bar motion",
    "blurb": "Progress fills ease over 200ms -- instant for reduced motion.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Improvement I-57",
         "title": "Progress bar motion",
         "subtitle": "Fills ease to their width -- 200ms, then still."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-progbar",
         "caption": "Status documents the motion: transition:width, reduced-motion off-ramp.",
         "assert_js": "() => !!document.querySelector('#status-b10-progbar')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: 200ms ease on both selectors, over-budget fails closed.",
         "commands": [
             ["python3", "-c",
              "from groundwork import progbar as m; "
              "print(m.progbar_css()[:160]); "
              "print('clamp:', m.transition_ms(9999), m.transition_ms(-3))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules",
         "caption": "Module progress bars ease -- the transition rides in the head wire.",
         "assert_js": "() => !!document.querySelector('.bar i') && "
                      "Array.from(document.querySelectorAll('head style')).some("
                      "s => s.textContent.includes('transition:width 200ms'))",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "Motion with an off-ramp.",
         "subtitle": "progbar.py eases the fill -- reduced motion jumps instantly."},
    ],
}
