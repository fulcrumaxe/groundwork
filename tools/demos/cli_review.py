"""Feature demo: CLI review (cli-review).

Full functionality: `python3 -m groundwork review` runs the due queue
in a terminal -- prompt, stdin answer, confidence, graded verdict --
no browser needed. seed_db backdates one self-rated (type 1) card to
year 2000 so it queues first; the terminal beat pipes "5" (recall)
and "4" (confidence) through the real loop and the DB beat shows the
banked grade-5 review.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "cli-review",
    "kind": "feature",
    "batch": 1,
    "item": "F-356",
    "title": "CLI review",
    "blurb": "python3 -m groundwork review \u2014 the queue without a browser.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Feature cli-review",
         "title": "CLI review",
         "subtitle": "The queue without a browser -- stdin in, verdict out."},
        {"type": "chrome", "duration": 8,
         "url_path": "/status#status-cli",
         "focus": "#status-cli",
         "caption": "Status names the command and the live due count.",
         "assert_js": "() => !!document.querySelector('#status-cli') && "
                      "document.body.innerText.includes('review --limit')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 12,
         "caption": "One piped answer through the real loop: prompt, grade, verdict.",
         "commands": [
             ["bash", "-lc",
              "printf '5\\n4\\n' | python3 -m groundwork --db \"$DEMO_DB\" review --limit 1"],
         ]},
        {"type": "terminal", "duration": 8,
         "caption": "Proof in the fixture DB: the CLI banked a grade-5 review.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print(con.execute(\"SELECT grade, submission FROM reviews "
              "WHERE card_id='{seed_card_id}' "
              "ORDER BY rowid DESC LIMIT 1\").fetchone())"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Reviews from any terminal.",
         "subtitle": "__main__.py review loop -- same grader as the web queue."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Backdate one self-rated card to year 2000 so it queues first.

    Type 1 (self-rating) keeps the piped answer trivial: "5" passes
    with "Logged." The review loop lists ORDER BY due with probes
    appended after, so the backdated card is what --limit 1 shows.
    """
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT cards.id, concepts.name, cards.front FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE cards.exercise_type = '1'"
            " ORDER BY cards.due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no type-1 cards"}
        cid = card[0]
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (cid,))
        con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
        con.commit()
        return {"seeded": True, "card_id": cid, "concept": card[1],
                "front": (card[2] or "")[:80]}
    finally:
        con.close()
