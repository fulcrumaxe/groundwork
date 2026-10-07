"""Feature demo: generated lessons retrieve first (F-63 integration).

Full behavior: levels_for prepends a recall probe to every level and
orders blocks via enforce_template -- questions before prose, stable.
The module page opens each level with "Recall first"; the Expert
level keeps its Worth-probing question second, ahead of the prose.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b16-ret"
HOW = ["Read the two defaults", "Add them into total",
       "Return total to the caller"]
SOURCE = "def add(a=2, b=3):\n    total = a + b\n    return total\n"

SCENARIO = {
    "id": "recallfirst",
    "kind": "feature",
    "batch": 16,
    "item": "F-63",
    "title": "Recall first, questions next",
    "blurb": "Every level opens with a recall probe -- questions stay ahead of prose.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 16 - Feature F-63",
         "title": "Recall first, questions next",
         "subtitle": "Every level opens with a recall probe -- questions stay ahead of prose."},
        {"type": "terminal", "duration": 8,
         "caption": "The template in one call: recall probe prepended, questions ahead of prose.",
         "commands": [
             ["python3", "-c",
              "from groundwork import explain as e, retrieval as r; "
              "blocks = [{'h': 'Summary', 'b': 'Adds.'}, {'h': 'Worth probing', 'b': 'What breaks?'}]; "
              "ordered = e._retrieval_first('add', blocks); "
              "print('order:', [b['h'] for b in ordered]); "
              "kinds = [('question' if b['h'] in e.QUESTION_HEADS else 'prose', 'x') for b in ordered]; "
              "print('template holds:', r.check_order(kinds)); "
              "print('empty/hostile pass through:', e._retrieval_first('add', []), e._retrieval_first('add', None))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#lesson-{seed_slug} h5",
         "caption": "Every level opens with a recall probe -- before a word of explanation.",
         "assert_js": "() => { const h = document.querySelector('main h5'); "
                      "return !!h && h.textContent.trim() === 'Recall first'; }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 6,
         "url_path": "/modules/{seed_module_id}?level=4",
         "focus": "#lesson-{seed_slug} h5",
         "caption": "Expert level: probe, then the Worth-probing question, then prose.",
         "assert_js": "() => { const hs = [...document.querySelectorAll('main h5')]"
                      ".map(e => e.textContent.trim()); "
                      "return hs[0] === 'Recall first' && hs[1] === 'Worth probing' "
                      "&& hs.indexOf('Contract') > 1; }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 16",
         "title": "Retrieve, then read.",
         "subtitle": "Retrieval-first ordering rides every generated level."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant one lesson; its levels must all retrieve first."""
    con = sqlite3.connect(db_path)
    try:
        node = "demo/ret.py:add"
        cid = f"{MODULE_ID}:{node}"
        con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": node, "name": "add", "kind": "function",
             "file": "demo/ret.py", "line": 1,
             "summary": "add() totals two numbers via its defaults.",
             "docstring": "Add a and b.", "callers": [], "callees": [],
             "key_lines": "", "source": SOURCE, "complexity": 1,
             "how": list(HOW), "worked": None,
             "dualcode": {"steps": list(HOW), "states": []}},
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b16", "Retrieval-first lesson module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid, MODULE_ID, "add", "function", "demo/ret.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "slug": _slug(node)}
    finally:
        con.close()
