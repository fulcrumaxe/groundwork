"""Feature demo: focus timer with queue auto-fill (F-119).

Full behavior: one click starts a 25-minute focus block whose card
list auto-fills from the head of today's Due queue (three minutes
a card, at least one); the countdown runs client-side with short
and long breaks. No persistence: refresh resets the clock, never
the queue. Live dues fill the block, so no fixture is needed.
"""
from __future__ import annotations

SCENARIO = {
    "id": "focustimer",
    "kind": "feature",
    "batch": 23,
    "item": "F-119",
    "title": "Focus timer",
    "blurb": "A 25-minute block auto-filled from your queue -- start, practice, break.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 23 - Feature F-119",
         "title": "Focus timer",
         "subtitle": "Twenty-five minutes, cards included."},
        {"type": "chrome", "duration": 7,
         "url_path": "/due",
         "focus": "#focus-timer",
         "caption": "Each block auto-fills from the head of today's Due queue.",
         "assert_js": "() => document.body.innerText.includes("
                      "'minute block covers')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Three minutes a card, at least one; an empty queue frees the block.",
         "commands": [
             ["python3", "-c",
              "from groundwork import focustimer as m; "
              "due = [{'id': 'c%d' % i} for i in range(10)]; "
              "print('10 due ->', len(m.mix_for(due)), 'cards'); "
              "print('2 due ->', m.mix_for(due[:2])); "
              "print('empty ->', m.mix_for([]))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "focus": "#focus-timer",
         "caption": "Start runs the countdown client-side -- the queue is never touched.",
         "js": ["() => { const b = document.querySelector('[data-focus-start]'); "
                "if (!b) return 'start-missing'; b.click(); return 'started'; }"],
         "poll_js": "() => (document.querySelector('.focus-clock') "
                    "|| {textContent: ''}).textContent",
         "poll_want": "24:5",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => (document.querySelector('.focus-clock') "
                      "|| {textContent: ''}).textContent.includes('24:5')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 23",
         "title": "Start. Practice. Break.",
         "subtitle": "focustimer.py keeps no history -- refresh resets only the clock."},
    ],
}


def seed_db(db_path: str) -> dict:
    """No fixture needed: live dues already fill the block."""
    return {"seeded": True, "note": "live due queue fills the block"}
