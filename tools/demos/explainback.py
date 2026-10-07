"""Feature demo: worked steps ask self-explanation prompts (F-58 integration).

Full behavior: render_levels renders one self-explanation prompt per
worked step under an "Explain it back" heading -- rotating why
questions, one per step. Lessons without worked steps render no
prompts at all.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b16-self"
HOW = ["Read the two defaults", "Add them into total",
       "Return total to the caller"]
SOURCE = "def add(a=2, b=3):\n    total = a + b\n    return total\n"
FLAT_SOURCE = ("def flat(xs):\n    out = []\n    for x in xs:\n        out.append(x)\n    return out\n")

SCENARIO = {
    "id": "explainback",
    "kind": "feature",
    "batch": 16,
    "item": "F-58",
    "title": "Explain it back",
    "blurb": "Every worked step asks a why question -- no steps, no prompts.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 16 - Feature F-58",
         "title": "Explain it back",
         "subtitle": "Every worked step asks a why question -- no steps, no prompts."},
        {"type": "terminal", "duration": 8,
         "caption": "One prompt per step, rotating why templates -- empty steps render nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import selfexplain as s; "
              "ps = s.selfexplain_prompts(['Read the defaults', 'Add them', 'Return total']); "
              "print(len(ps), 'prompts, one per step:'); "
              "[print('-', p['prompt'][:64]) for p in ps]; "
              "print('no steps -> no prompts:', s.prompts_html(s.selfexplain_prompts([])) == '')"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#lesson-{seed_add_slug} #selfexplain",
         "caption": "Three worked steps, three why questions -- explain each line back.",
         "js": ["() => { const d = document.querySelector('#lesson-{seed_add_slug} #selfexplain details'); "
               "if (!d) return 'missing'; d.open = true; return 'opened'; }"],
         "assert_js": "() => document.querySelectorAll('details.selfexplain').length === 3",
         "assert_want": "True"},
        {"type": "chrome", "duration": 6,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#lesson-{seed_flat_slug} details.predict",
         "caption": "No worked steps, no prompts -- the snippet still hides under its cover.",
         "assert_js": "() => !!document.querySelector('details.predict') && !document.querySelector('#selfexplain')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 16",
         "title": "Why, not just what.",
         "subtitle": "Self-explanation prompts ride every worked step."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant a stepped lesson (prompts) and a stepless one (none)."""
    con = sqlite3.connect(db_path)
    try:
        nodes = ["demo/self.py:add", "demo/self.py:flat"]
        cids = [f"{MODULE_ID}:{n}" for n in nodes]
        for cid in cids:
            con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
            con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": nodes[0], "name": "add", "kind": "function",
             "file": "demo/self.py", "line": 1,
             "summary": "add() totals two numbers via its defaults.",
             "docstring": "Add a and b.", "callers": [], "callees": [],
             "key_lines": "", "source": SOURCE, "complexity": 1,
             "how": list(HOW), "worked": None,
             "dualcode": {"steps": list(HOW), "states": []}},
            {"concept_id": nodes[1], "name": "flat", "kind": "function",
             "file": "demo/self.py", "line": 5,
             "summary": "flat() copies a list item by item.",
             "docstring": "Copy the list.", "callers": [], "callees": [],
             "key_lines": "", "source": FLAT_SOURCE, "complexity": 2,
             "how": [], "worked": None},
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b16", "Self-explain lesson module", now,
             json.dumps(lessons)))
        for node, cid in zip(nodes, cids):
            name = node.rsplit(":", 1)[1]
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, name, "function", "demo/self.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "add_slug": _slug(nodes[0]), "flat_slug": _slug(nodes[1])}
    finally:
        con.close()
