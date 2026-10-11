"""Improvement demo: inline SVG call graphs (I-126).

Full behavior: lessons carrying caller/callee name lists render an inline
SVG (callers left, self center, callees right) on the module page; lessons
without call data render nothing extra. seed_db plants one lesson with
two callers and two callees.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-callgraph-126"
NODE = "demo/cg.py:serve"
CONCEPT_ID = f"{MODULE_ID}:{NODE}"

SCENARIO = {
    "id": "callgraph",
    "kind": "improvement",
    "batch": 21,
    "item": "I-126",
    "title": "Inline SVG call graphs",
    "blurb": "Caller/callee lists draw as a graph: callers left, self center, callees right.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Improvement I-126",
         "title": "Inline SVG call graphs",
         "subtitle": "Text name-lists become a picture -- callers left, callees right."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-callgraph",
         "caption": "Status documents the improvement with a live sample graph.",
         "assert_js": "() => !!document.querySelector('#status-b21-callgraph') && "
                      "!!document.querySelector('svg.callgraph')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: call data draws; no data renders nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import callgraph as m; "
              "les = {'name': 'serve', 'callers': ['handle_request', 'retry_loop'], "
              "'callees': ['grade_answer', 'render_result']}; "
              "print('has_graph:', m.has_graph(les), '| svg bytes:', len(m.graph_svg(les))); "
              "print('legacy lesson:', repr(m.graph_svg({'name': 'plain'}))); "
              "print('callers:', m.callers_of(les))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}",
         "focus": "figure.callgraph-wrap",
         "caption": "The lesson grows a call graph: two callers, self, two callees.",
         "assert_js": "() => { const s = document.querySelector('svg.callgraph'); "
                      "return !!s && s.getAttribute('aria-label').includes('serve'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "See the calls.",
         "subtitle": "callgraph.py draws the graph -- legacy lessons stay byte-identical."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a module whose lesson carries caller/callee name lists."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id LIKE 'demo-cg-%'")
        con.execute("DELETE FROM cards WHERE id LIKE 'demo-cg-%'")
        con.execute("DELETE FROM concepts WHERE id=?", (CONCEPT_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lesson = {"concept_id": NODE, "name": "serve", "kind": "function",
                  "file": "demo/cg.py", "line": 1,
                  "summary": "Serve one review round trip end to end.",
                  "callers": ["handle_request", "retry_loop"],
                  "callees": ["grade_answer", "render_result"]}
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/callgraph", "Call graph module", now,
             json.dumps([lesson])))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CONCEPT_ID, MODULE_ID, "serve", "function",
             "demo/cg.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
