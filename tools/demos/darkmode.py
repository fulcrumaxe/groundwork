"""Improvement demo: dark mode via prefers-color-scheme (I-52).

Full behavior: one @media block re-assigns only the :root palette
tokens, so every component follows the OS preference with no
selector duplication -- and all 8 AA body-text pairs pass >= 4.5.
Chrome proves the block ships in every page head plus the live
weakest-pair line; the terminal proves the contrast math.
"""
from __future__ import annotations

SCENARIO = {
    "id": "darkmode",
    "kind": "improvement",
    "batch": 9,
    "item": "I-52",
    "title": "Dark mode",
    "blurb": "Dark palette follows the OS -- one media block, all pairs AA.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Improvement I-52",
         "title": "Dark mode",
         "subtitle": "One media block -- the OS preference flips the palette."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-darkmode",
         "caption": "Status documents the block: :root tokens only, weakest pair named.",
         "assert_js": "() => !!document.querySelector('#status-b9-darkmode')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: every AA pair passes -- zero failures or it ships nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import darkmode as m; "
              "print('AA failures:', m.check_contrast()); "
              "print('ink on paper:', round(m.contrast_ratio(m.DARK_OVERRIDES['--ink'], m.DARK_OVERRIDES['--paper']), 2)); "
              "print(m.dark_css()[:150])"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/status",
         "focus": "#status-b9-darkmode",
         "caption": "Every page ships the dark block -- all 8 pairs pass AA in it.",
         "assert_js": "() => Array.from(document.querySelectorAll('head style')).some("
                      "s => s.textContent.includes('prefers-color-scheme: dark')) && "
                      "document.body.innerText.includes('AA body-text pairs pass')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Dark, by preference.",
         "subtitle": "darkmode.py re-assigns tokens -- components follow for free."},
    ],
}
