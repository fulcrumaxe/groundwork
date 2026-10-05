"""Feature demo: desirable-difficulty dial (F-55).

Full behavior: the 1-5 dial floors the Due queue on sched
retrievability and caps new cards -- the live Due control re-filters
the real queue, and the terminal re-runs the pure filter on a
crafted mix (forgotten review, fresh review, five new cards).
"""
from __future__ import annotations

SCENARIO = {
    "id": "diffdial",
    "kind": "feature",
    "batch": 12,
    "item": "F-55",
    "title": "Difficulty dial",
    "blurb": "Challenge 1-5, gentle to spicy -- floors R, caps new cards.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Feature F-55",
         "title": "Difficulty dial",
         "subtitle": "Challenge 1 to 5, gentle to spicy."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b12-diffdial",
         "caption": "Status tables the dial: floor, new-card cap, Bloom lean.",
         "assert_js": "() => { const el = document.querySelector("
                      "\"#status-b12-diffdial\"); return !!el && "
                      "document.body.innerText.includes('dial_params'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 10,
         "caption": "The rule in one line: gentle keeps two, spicy keeps seven.",
         "commands": [
             ["python3", "-c",
              "from datetime import datetime, timedelta, timezone; "
              "from groundwork import minisession as m; "
              "now = datetime.now(timezone.utc); "
              "iso = lambda d: (now - timedelta(days=d)).strftime("
              "'%Y-%m-%dT%H:%M:%SZ'); "
              "due = [{'id': 'mid', 'stability': 10.0, 'due': iso(12)}, "
              "{'id': 'fresh', 'stability': 10.0, 'due': iso(0)}] + "
              "[{'id': f'n{i}', 'stability': 1.0, 'due': iso(0)} "
              "for i in range(5)]; "
              "tries = {'mid': 3, 'fresh': 2}; "
              "print('L1:', [c['id'] for c in m.apply_dial(due, 1, tries)]); "
              "print('L5:', [c['id'] for c in m.apply_dial(due, 5, tries)])"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/due?dial=1",
         "focus": "#dial",
         "caption": "Gentle dialed on Due: the queue obeys, the line explains.",
         "assert_js": "() => { const el = document.querySelector('#dial');"
                      " return !!el && el.innerText.includes('Gentle')"
                      " && el.innerHTML.includes('(dialed)') ; }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Dial your struggle.",
         "subtitle": "diffdial.py floors R and caps new cards."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Db-free filter over the live queue; no fixture needed."""
    return {"seeded": True, "note": "live queue, no fixture"}
