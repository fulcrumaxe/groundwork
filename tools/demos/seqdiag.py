"""Improvement demo: call-chain sequence diagrams (I-127).

Full behavior: type-10 order-the-calls widgets grow a lifelines-and-arrows
figure above the prompt, reusing the stored solution chain. seed_db plants
a grounded 3-step chain card on a fresh module; the module practice section
is the shared widget path (Due renders the same figure).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-seqdiag-127"
NODE = "demo/seq.py:resize"
CONCEPT_ID = f"{MODULE_ID}:{NODE}"
CARD_ID = "demo-seq-10"
CHAIN = ["handle_resize", "resize", "repaint"]

SCENARIO = {
    "id": "seqdiag",
    "kind": "improvement",
    "batch": 21,
    "item": "I-127",
    "title": "Call chains as sequence diagrams",
    "blurb": "Order-the-calls chains draw as lifelines and arrows above the prompt.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Improvement I-127",
         "title": "Call chains as sequence diagrams",
         "subtitle": "Three-step chains draw as lifelines -- predict the order, then check."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-seqdiag",
         "caption": "Status documents the diagram with a live 3-step sample.",
         "assert_js": "() => !!document.querySelector('#status-b21-seqdiag') && "
                      "!!document.querySelector('svg.seq-diagram')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: 2-3 grounded steps draw; singletons vanish.",
         "commands": [
             ["python3", "-c",
              "from groundwork import seqdiag as m; "
              "ex = {'payload': {'solution': ['handle_resize', 'resize', 'repaint'], 'grounded': True}}; "
              "print('chain:', m.chain_of(ex)); "
              "print('svg bytes:', len(m.sequence_svg(m.chain_of(ex)))); "
              "print('singleton:', repr(m.sequence_svg(['only']))); "
              "print('caption:', m.figure_html(ex, 'resize')[-70:])"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}",
         "focus": ".seq-figure",
         "caption": "The order-the-calls card grows its diagram above the prompt.",
         "assert_js": "() => { const f = document.querySelector('.seq-figure'); "
                      "return !!f && f.innerText.includes('Call order through'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "See the chain.",
         "subtitle": "seqdiag.py reuses the solution -- ungrounded chains stay quiet."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a module with one grounded 3-step type-10 card."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE id=?", (CONCEPT_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lesson = {"concept_id": NODE, "name": "resize", "kind": "function",
                  "file": "demo/seq.py", "line": 1,
                  "summary": "Order the three calls in a window resize."}
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/seqdiag", "Sequence diagram module", now,
             json.dumps([lesson])))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CONCEPT_ID, MODULE_ID, "resize", "function",
             "demo/seq.py", 1, 0.0))
        payload = {"solution": CHAIN, "grounded": True, "lines": CHAIN,
                   "hints": ["Entry point handles the event first."]}
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back,"
            " payload) VALUES(?, ?, '10', ?, ?, ?)",
            (CARD_ID, CONCEPT_ID, "Put the resize calls in order.",
             "handle_resize, resize, repaint.", json.dumps(payload)))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID, "card_id": CARD_ID}
    finally:
        con.close()
