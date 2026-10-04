"""Feature demo: component gallery (Batch 3, I-96).

Full functionality: /styleguide renders real UI fragments (chips,
buttons, bars, widgets, tables) beside their CSS class names so
contributors reuse before adding. No seed manipulation needed beyond
picking nothing -- the page is static -- but seed_db reports the
section count the asserts pin.
"""
from __future__ import annotations

SCENARIO = {
    "id": "style-guide",
    "kind": "feature",
    "batch": 3,
    "item": "I-96",
    "title": "Component gallery",
    "blurb": "Every UI building block on one dev page, with class names.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 3 - Feature I-96",
         "title": "Component gallery",
         "subtitle": "Every UI building block on one dev page, with class names."},
        {"type": "chrome", "duration": 8,
         "url_path": "/styleguide",
         "caption": "One dev page renders every building block beside its class name.",
         "assert_js": "() => !!document.querySelector('#styleguide') + '|' + "
                      "document.querySelectorAll('#styleguide h2').length",
         "assert_want": "true|10"},
        {"type": "chrome", "duration": 8,
         "url_path": "/styleguide",
         "focus": "article",
         "caption": "Real fragments, not mockups: the live answer widget renders inline.",
         "assert_js": "() => !!document.querySelector("
                      "'article input, article button')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Ten sections, each pairing markup with the selector to reuse.",
         "commands": [
             ["python3", "-c",
              "from groundwork import styleguide as m; "
              "import html as h, re; "
              "b = m.page(); "
              "print(len(re.findall('<h2>', b)), 'sections:'); "
              "[print(' -', h.unescape(t)) for t in re.findall(r'<h2>(.*?)</h2>', b)]"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/styleguide",
         "focus": "table.log",
         "caption": "Log tables sit beside the selector to copy.",
         "assert_js": "() => !!document.querySelector('table.log')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 3",
         "title": "Reuse before adding.",
         "subtitle": "styleguide.py renders real fragments -- never linked from nav."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Static dev page: nothing to manipulate, report readiness."""
    return {"seeded": True}
