"""Improvement demo: difficulty-vote queue weights (I-146).

Full behavior: live difficulty votes reshape the Due queue — a
concept voted too-hard consolidates from its lowest tier first, a
concept voted too-easy leads with its hardest tier, and unvoted
concepts keep today's order byte-identical. seed_db prunes the
library to two voted concepts (hard + easy, recall and create
cards each) so the MCP queue call proves the reorder.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-diffweights-146"
HARD_NODE = "demo/queue.py:struggling"
EASY_NODE = "demo/queue.py:cruising"
HARD_CID = f"{MODULE_ID}:{HARD_NODE}"
EASY_CID = f"{MODULE_ID}:{EASY_NODE}"
DUE = "2000-01-01T12:00:00Z"

SCENARIO = {
    "id": "diffweights",
    "kind": "improvement",
    "batch": 23,
    "item": "I-146",
    "title": "Difficulty-vote exercise weights",
    "blurb": "Too-easy votes surface harder types first; too-hard votes consolidate foundations.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 23 - Improvement I-146",
         "title": "Difficulty-vote exercise weights",
         "subtitle": "Votes steer practice -- hard consolidates, easy stretches."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b23-diffweights",
         "caption": "Status documents the rule: votes reweight voted concepts only.",
         "assert_js": "() => !!document.querySelector('#status-b23-diffweights')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "Pure reorder: hard recalls first, easy creates first, unvoted untouched.",
         "commands": [
             ["python3", "-c",
              "from groundwork import diffweights as m; "
              "cards = [{'concept_id': 'H', 'tier': 'create'}, "
              "{'concept_id': 'H', 'tier': 'recall'}, "
              "{'concept_id': 'E', 'tier': 'recall'}, "
              "{'concept_id': 'E', 'tier': 'create'}, "
              "{'concept_id': 'U', 'tier': 'create'}]; "
              "out = m.order_due(cards, {'H': 'hard', 'E': 'easy'}); "
              "print([(c['concept_id'], c['tier']) for c in out])"],
         ]},
        {"type": "terminal", "duration": 10,
         "caption": "The real caller path: the MCP due queue serves the weighted order.",
         "commands": [
             ["bash", "-lc",
              "echo '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"list_due_reviews\","
              "\"params\":{\"limit\":4}}' "
              "| python3 -m groundwork --db \"$DEMO_DB\" mcp "
              "| python3 -c \"import json,sys; r=json.load(sys.stdin)['result'];"
              " print([(c['concept'],c['exercise_type']) for c in r['due']])\""],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 23",
         "title": "Votes steer practice.",
         "subtitle": "diffweights.py reorders within each concept -- upstream bridges survive."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Prune to two voted concepts: hard + easy, recall + create each."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for table in ("reviews", "cards", "diffvote_votes",
                      "clarity_ratings", "confusing_flags", "known_skips",
                      "concepts", "modules"):
            con.execute(f"DELETE FROM {table}")
        lessons = [
            {"concept_id": HARD_NODE, "name": "struggling",
             "kind": "function", "file": "demo/queue.py", "line": 1,
             "summary": "struggling earned its too-hard votes honestly.",
             "docstring": "Hard votes consolidate.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def struggling():\n    return practice()\n",
             "complexity": 3,
             "how": ["Vote it too hard.", "Drill foundations first."]},
            {"concept_id": EASY_NODE, "name": "cruising",
             "kind": "function", "file": "demo/queue.py", "line": 9,
             "summary": "cruising earned its too-easy votes honestly.",
             "docstring": "Easy votes stretch.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def cruising():\n    return practice()\n",
             "complexity": 1,
             "how": ["Vote it too easy.", "Lead with harder types."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Vote-weight module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (HARD_CID, MODULE_ID, "struggling", "function",
             "demo/queue.py", 1, 0.0))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (EASY_CID, MODULE_ID, "cruising", "function",
             "demo/queue.py", 9, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '1', ?)", (f"{MODULE_ID}:h-recall", HARD_CID, DUE))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '24', ?)", (f"{MODULE_ID}:h-create", HARD_CID, DUE))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '1', ?)", (f"{MODULE_ID}:e-recall", EASY_CID, DUE))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '24', ?)", (f"{MODULE_ID}:e-create", EASY_CID, DUE))
        for _ in range(2):
            con.execute(
                "INSERT INTO diffvote_votes(concept_id, vote) VALUES(?, 'hard')",
                (HARD_CID,))
            con.execute(
                "INSERT INTO diffvote_votes(concept_id, vote) VALUES(?, 'easy')",
                (EASY_CID,))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID,
                "hard": HARD_CID, "easy": EASY_CID}
    finally:
        con.close()
