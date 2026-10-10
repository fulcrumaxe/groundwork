"""Feature demo: refactoring kata library (F-87).

Full behavior: kata tracks group buggy snippets by smell id and the
Due queue leads with the weakest track. seed_db wipes smell-card
reviews, plants one weak card (broad-except, 3 fails, older last)
and one strong card (long-function, 5 passes, newer last) as the
sole due cards, then the MCP beat calls the real caller
(MCPServer.tool_list_due_reviews) to prove weakest-track-first.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone

WEAK_ID = "demo-kata-weak"
STRONG_ID = "demo-kata-strong"
CONCEPT_ID = "demo-kata-concept"
WEAK_SMELL = "broad-except"
STRONG_SMELL = "long-function"

FRONT_WEAK = ("Which code smell best describes this snippet?\n"
              "```python\ntry:\n    save(row)\nexcept Exception:\n    pass\n```")
BACK_WEAK = "Overly Broad Except -- catch the narrowest error you can handle."
FRONT_STRONG = ("Which code smell best describes this snippet?\n"
                "```python\ndef report(rows):\n    out = []\n    for r in rows:\n        x = r.strip()\n        if x:\n            out.append(x.upper())\n    total = len(out)\n    print(total)\n    return out\n```")
BACK_STRONG = "Long Function -- extract one helper per job."

SCENARIO = {
    "id": "katabank",
    "kind": "feature",
    "batch": 20,
    "item": "F-87",
    "title": "Refactoring kata library",
    "blurb": "Same smell across many repos on a spaced schedule -- the Due queue leads with your weakest track.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Feature F-87",
         "title": "Refactoring kata library",
         "subtitle": "One smell, many repos, spaced -- weakest track deals first."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-katabank",
         "caption": "Status homes the six kata tracks, one per detected smell.",
         "assert_js": "() => !!document.querySelector('#status-b20-katabank')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Pure logic: 3 fails on broad-except outranks 5 passes on long-function.",
         "commands": [
             ["python3", "-c",
              "from groundwork import katabank as k; "
              "h = {'long-function': {'passes': 5, 'fails': 0, 'last': '2020-01-31'}, "
              "'broad-except': {'passes': 0, 'fails': 3, 'last': '2020-01-22'}}; "
              "print('next kata:', k.pick_kata(h, None, 'long-function', now='2020-02-01')); "
              "cards = [{'id': 'a', 'payload': {'smell': 'long-function'}}, "
              "{'id': 'b', 'payload': {'smell': 'broad-except'}}, "
              "{'id': 'c', 'payload': {}}]; "
              "print('queue:', [c['id'] for c in k.order_due(cards, h, now='2020-02-01')])"],
         ]},
        {"type": "terminal", "duration": 9,
         "caption": "The real caller: list_due_reviews ranks the failing broad-except kata first.",
         "commands": [
             ["python3", "-c",
              "import os, json, sqlite3; "
              "from groundwork import mcp as M, katabank as K; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "con = sqlite3.connect(db); "
              "h = K.kata_history_from_rows(con.execute("
              "'SELECT grade, reviewed_at, payload FROM reviews "
              "JOIN cards ON cards.id = reviews.card_id').fetchall()); "
              "print('broad-except:', h.get('broad-except')); "
              "print('long-function:', h.get('long-function')); "
              "d = M.MCPServer(db).tool_list_due_reviews({'limit': 50})['due']; "
              "print('seeded queue order:', "
              "[(c['id'], json.loads(c['payload']).get('smell')) "
              "for c in d if c['id'].startswith('demo-kata-')])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_weak_id}",
         "caption": "The weakest kata is due now -- answer it on the Due path.",
         "assert_js": "() => !!document.querySelector("
                      "\"form[action='/cards/{seed_weak_id}/review']\")",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Weakest smell first.",
         "subtitle": "katabank.py ranks the queue -- no history keeps legacy order."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One weak + one strong kata card as the sole due cards with history.

    Wipes smell-card reviews so the seeded history is the only kata
    signal, then inserts 5 passes (fresh stamp) on the strong card and
    3 fails (older stamp) on the weak card. The fresh stamp makes
    long-function the last-dealt track so it sinks last for variety;
    the failing tail keeps the boredom layer calm; the fresh concept
    has no lesson needs or votes so later reorder layers keep the
    kata order. Both cards are reviewed, so the sleep hook keeps
    their stored due times.
    """
    con = sqlite3.connect(db_path)
    try:
        mod = con.execute(
            "SELECT id FROM modules ORDER BY rowid LIMIT 1").fetchone()
        if not mod:
            return {"seeded": False, "reason": "no modules"}
        con.execute(
            "DELETE FROM reviews WHERE card_id IN "
            "(SELECT id FROM cards WHERE payload LIKE '%\"smell\"%')")
        con.execute(
            "INSERT OR REPLACE INTO concepts(id, module_id, name, kind)"
            " VALUES(?, ?, 'Kata ordering demo', 'demo')",
            (CONCEPT_ID, mod[0]))
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        weak_payload = {"choices": ["Overly Broad Except", "Long Function",
                                    "Deep Nesting"],
                        "answer": "Overly Broad Except",
                        "smell": WEAK_SMELL, "grounded": True,
                        "detail": "a bare handler swallows every failure"}
        strong_payload = {"choices": ["Long Function", "Deep Nesting",
                                      "Duplicated Code"],
                          "answer": "Long Function",
                          "smell": STRONG_SMELL, "grounded": True,
                          "detail": "one function spans 20+ lines"}
        for cid, front, back, payload in (
                (WEAK_ID, FRONT_WEAK, BACK_WEAK, weak_payload),
                (STRONG_ID, FRONT_STRONG, BACK_STRONG, strong_payload)):
            con.execute(
                "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
                " front, back, payload, due, stale)"
                " VALUES(?, ?, '15', ?, ?, ?, '2000-01-01T00:00:00Z', 0)",
                (cid, CONCEPT_ID, front, back, json.dumps(payload)))
        now = datetime.now(timezone.utc)
        fresh = (now - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
        old = (now - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        for _ in range(5):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at, submission)"
                " VALUES(?, 5, 4, ?, 'kata seed pass')",
                (STRONG_ID, fresh))
        for _ in range(3):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at, submission)"
                " VALUES(?, 1, 2, ?, 'kata seed fail')",
                (WEAK_ID, old))
        con.commit()
        return {"seeded": True, "weak_id": WEAK_ID,
                "strong_id": STRONG_ID, "concept_id": CONCEPT_ID,
                "module_id": mod[0]}
    finally:
        con.close()
