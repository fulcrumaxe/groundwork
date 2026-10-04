"""Improvement demo: whole-card module links (I-16).

Full behavior: every module card on /modules is one clickable
target -- a single stretched link covers the card (nested anchors
flattened, never nested) with a visible :focus-visible ring. The
click-through beat opens the first card and polls the module page.
"""
from __future__ import annotations

SCENARIO = {
    "id": "clickcards",
    "kind": "improvement",
    "batch": 7,
    "item": "I-16",
    "title": "Whole-card module links",
    "blurb": "Every module card is one big target with a visible keyboard focus ring.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Improvement I-16",
         "title": "Whole-card module links",
         "subtitle": "One card, one link -- click anywhere, tab with a visible ring."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-clickcards",
         "caption": "Status documents the improvement: one stretched link, nested anchors flattened.",
         "assert_js": "() => !!document.querySelector('#status-b7-clickcards')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: exactly one <a> per card, and off-site hrefs fail closed.",
         "commands": [
             ["python3", "-c",
              "from groundwork import clickcards as m; "
              "print(m.wrap_card('<b>T</b><a href=\"/x\">R</a>', '/modules/abc', 'Open m')[:80]); "
              "print(m.safe_href('https://evil.example/'))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/modules",
         "caption": "The library: every card carries exactly one stretched link.",
         "assert_js": "() => { const c = document.querySelectorAll('.modcard--clickable'); "
                      "const links = document.querySelectorAll('.modcard--clickable a'); "
                      "return c.length > 0 && links.length === c.length; }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/modules",
         "caption": "Click anywhere on the card -- the module page answers.",
         "js": ["() => { const a = document.querySelector('.modcard--clickable a'); "
                "if (!a) return 'no-card-link'; a.click(); return 'clicked'; }"],
         "poll_js": "() => location.pathname",
         "poll_want": "/modules/",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => location.pathname.startsWith('/modules/') && "
                      "!!document.querySelector(\"section[id^='lesson-']\")",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "The card is the link.",
         "subtitle": "clickcards.py stretches one anchor -- no nested interactive HTML."},
    ],
}
