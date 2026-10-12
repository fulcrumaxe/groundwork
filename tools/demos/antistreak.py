"""Feature demo: anti-streak pledge on History (F-124).

Full behavior: a standing pledge after the month review -- missed
days cost nothing, memory runs on intervals, proof counts. Static
copy, no DB read, identical with zero reviews. No fixture needed.
"""
from __future__ import annotations

SCENARIO = {
    "id": "antistreak",
    "kind": "feature",
    "batch": 24,
    "item": "F-124",
    "title": "Anti-streak pledge",
    "blurb": "Why Groundwork never counts streaks -- ever.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Feature F-124",
         "title": "Anti-streak pledge",
         "subtitle": "Chains are never counted -- memory runs on intervals."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-antistreak",
         "caption": "Status states the principle with its anchor.",
         "assert_js": "() => !!document.querySelector("
                      "'#status-b24-antistreak')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "One pledge line, three reasons, static copy.",
         "commands": [
             ["python3", "-c",
              "from groundwork import antistreak as m; "
              "print(m.pledge()); "
              "print('reasons:', len(m.reasons())); "
              "print(m.pledge_html()[:140])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "focus": "#antistreak",
         "caption": "History carries the standing pledge after the month review.",
         "assert_js": "() => !!document.querySelector('#antistreak') "
                      "&& document.body.innerText.includes("
                      "'We never count streaks')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "No chains, ever.",
         "subtitle": "antistreak.py pledges -- gaps break nothing."},
    ],
}


def seed_db(db_path: str) -> dict:
    """No fixture needed: static pledge renders with zero reviews."""
    return {"seeded": True, "note": "static copy, no fixture"}
