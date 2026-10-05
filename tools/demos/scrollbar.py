"""Improvement demo: palette scrollbars (I-86).

Full behavior: every page ships thin scrollbars on the muted
--stale/--paper pair (Firefox + WebKit), while coarse-pointer touch
devices keep full-size scrolling and forced-colors users keep native
bars. The History beat films a long scrolling page under the live rule.
"""
from __future__ import annotations

SCENARIO = {
    "id": "scrollbar",
    "kind": "improvement",
    "batch": 13,
    "item": "I-86",
    "title": "Palette scrollbars",
    "blurb": "Thin muted scrollbars -- touch and forced-colors keep natives.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Improvement I-86",
         "title": "Palette scrollbars",
         "subtitle": "Thin, muted, palette-matched -- touch and forced-colors keep natives."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-scrollbar",
         "caption": "Status documents the muted pair and both platform opt-outs.",
         "assert_js": "() => !!document.querySelector('#status-b13-scrollbar')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: thin muted pair, no shouting accent, two escapes.",
         "commands": [
             ["python3", "-c",
              "from groundwork import scrollbar as m; css = m.scrollbar_css(); "
              "print('thin:', 'scrollbar-width:thin' in css.replace(' ', '')); "
              "print('pair:', 'var(--stale)' in css and 'var(--paper)' in css); "
              "print('webkit:', '::-webkit-scrollbar-thumb' in css); "
              "print('escapes:', 'pointer:coarse' in css and 'forced-colors' in css)"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/reviews",
         "caption": "History, a long scrolling page, renders under the thin-bar rule.",
         "assert_js": "() => { const css = [...document.querySelectorAll('style')]"
                      ".map(s => s.textContent).join('\\n'); "
                      "return css.includes('scrollbar-width') && "
                      "css.includes('scrollbar-color'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Scroll in palette.",
         "subtitle": "scrollbar.py -- muted bars in the head wire, on every page."},
    ],
}
