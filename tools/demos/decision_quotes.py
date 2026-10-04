"""Improvement demo: decision quotes (Batch 4, I-110).

Full functionality: lessons quote the agent's recorded chose-X-over-Y
rationale that motivated them; lessons without a recorded decision
say so honestly. seed_db records one decision against the first
lesson node of the biggest module.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "decision-quotes",
    "kind": "improvement",
    "batch": 4,
    "item": "I-110",
    "title": "Decision quotes",
    "blurb": "Agent chose-X-over-Y rationale quoted inside the lesson it shaped.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Improvement I-110",
         "title": "Decision quotes",
         "subtitle": "Agent chose-X-over-Y rationale quoted inside the lesson it shaped."},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}",
         "focus": "#decisions",
         "caption": "The lesson quotes the decision that motivated it.",
         "assert_js": "() => document.body.innerText.includes("
                      "'Chose {seed_chosen} over {seed_rejected}')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Decisions attach to lesson nodes by symbol match.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import decisions as d; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "ms = d.matches_for_module(db, ['{seed_node}']); "
              "print('matches:', len(ms['{seed_node}'])); "
              "print('chose:', ms['{seed_node}'][0]['chosen'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "caption": "Lessons without a recorded decision say so honestly.",
         "assert_js": "() => document.body.innerText.includes("
                      "'No recorded agent decisions')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Why, in context.",
         "subtitle": "decisions.py matches MCP-logged rationale to lesson nodes."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Record one decision against the biggest module's first lesson.

    The symbol equals the lesson node exactly (mid stripped, like the
    module page computes it), so the quote must render on the first
    lesson while later lessons keep the honest empty state.
    """
    con = sqlite3.connect(db_path)
    try:
        m = con.execute(
            "SELECT concepts.module_id, COUNT(*) FROM cards "
            "JOIN concepts ON concepts.id = cards.concept_id "
            "GROUP BY concepts.module_id "
            "ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
        if not m:
            return {"seeded": False, "reason": "no cards"}
        mid = m[0]
        c = con.execute(
            "SELECT id FROM concepts WHERE module_id=?"
            " ORDER BY rowid LIMIT 1", (mid,)).fetchone()
        if not c:
            return {"seeded": False, "reason": "module without concepts"}
        cid = c[0]
        node = cid.split(":", 1)[1] if ":" in cid else cid
        chosen, rejected = "DecideSeed42A", "DecideSeed42B"
        con.execute("DELETE FROM decisions WHERE symbol=?", (node,))
        con.execute(
            "INSERT INTO decisions(repo, symbol, chosen, rejected, reason)"
            " VALUES(?, ?, ?, ?, ?)",
            (".", node, chosen, rejected, "quoted in the demo seed"))
        con.commit()
        return {"seeded": True, "mid": mid, "cid": cid, "node": node,
                "chosen": chosen, "rejected": rejected}
    finally:
        con.close()
