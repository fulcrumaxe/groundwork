"""Improvement demo: skip links (Batch 4, I-15).

Full functionality: every page opens with a "Skip to content" link
plus header/nav/main/footer landmarks, so keyboard and screen-reader
users jump straight to the content. No seed manipulation needed --
the chrome is on every page -- so seed_db just reports the served
page to film.
"""
from __future__ import annotations

SCENARIO = {
    "id": "skip-links",
    "kind": "improvement",
    "batch": 4,
    "item": "I-15",
    "title": "Skip links",
    "blurb": "Skip to content link plus header/nav/main/footer landmarks.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Improvement I-15",
         "title": "Skip links",
         "subtitle": "Skip to content link plus header/nav/main/footer landmarks."},
        {"type": "chrome", "duration": 8,
         "url_path": "/",
         "caption": "Every page opens with a Skip to content link and landmarks.",
         "assert_js": "() => { const a = document.querySelector(\"a.skip[href='#main']\"); "
                      "return (a ? a.textContent : 'missing') + '|' + "
                      "!!document.querySelector('header') + '|' + "
                      "!!document.querySelector('nav') + '|' + "
                      "!!document.querySelector('main') + '|' + "
                      "!!document.querySelector('footer'); }",
         "assert_want": "Skip to content|true|true|true|true"},
        {"type": "chrome", "duration": 7,
         "url_path": "/",
         "caption": "Activating it jumps straight to the main content.",
         "js": ["() => { const a = document.querySelector('a.skip'); "
                "if (!a) return 'no-skip'; a.click(); return 'clicked'; }"],
         "assert_js": "() => location.hash",
         "assert_want": "#main"},
        {"type": "terminal", "duration": 7,
         "caption": "The page shell carries the link and all four landmarks.",
         "commands": [
             ["python3", "-c",
              "from groundwork.web import page; "
              "h = page('T', '<p>x</p>').decode(); "
              "print('skip link:', 'Skip to content' in h); "
              "print('landmarks:', [t for t in ['<header', '<nav', \"<main\", '<footer'] if t in h])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Straight to the content.",
         "subtitle": "web.page opens every page with the skip link and landmarks."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Nothing to plant: the chrome ships on every page."""
    return {"seeded": True}
