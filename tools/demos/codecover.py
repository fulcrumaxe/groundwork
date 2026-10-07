"""Feature demo: lesson snippets hide under covers (F-64 integration).

Full behavior: render_levels wraps each level's snippet in a
predict-then-reveal cover (native disclosure, no JS) instead of the
legacy open details; the cover language follows the lesson filename.
Clicking the summary reveals the snippet -- predict, then reveal.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b16-pred"
PY_HOW = ["Read the two defaults", "Add them into total",
          "Return total to the caller"]
PY_SOURCE = "def add(a=2, b=3):\n    total = a + b\n    return total\n"
TS_HOW = ["Read the name", "Prefix hi", "Hand back the greeting"]
TS_SOURCE = ("export function greet(name: string): string {\n"
             "  return 'hi ' + name;\n}\n")

SCENARIO = {
    "id": "codecover",
    "kind": "feature",
    "batch": 16,
    "item": "F-64",
    "title": "Snippets hide under covers",
    "blurb": "Every snippet hides under a predict-then-reveal cover -- language sniffed from the filename.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 16 - Feature F-64",
         "title": "Snippets hide under covers",
         "subtitle": "Every snippet hides under a predict-then-reveal cover -- language sniffed from the filename."},
        {"type": "terminal", "duration": 8,
         "caption": "The widget in one call: covered until clicked, empty code renders nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import lessons as l, predict as p; "
              "w = p.cover_html('print(add())', l._code_lang('demo/app.ts')); "
              "print('covered:', p.is_covered(w), '| js:', \"data-lang='javascript'\" in w); "
              "print('empty code ->', repr(p.cover_html('   '))); "
              "print('calc.py ->', l._code_lang('demo/calc.py'))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#lesson-{seed_py_slug} details.predict",
         "caption": "The snippet hides under its cover -- predict the output, then reveal.",
         "assert_js": "() => { const d = document.querySelector('details.predict'); "
                      "return !!d && !!d.querySelector('pre') && !d.open "
                      "&& d.querySelector('pre').dataset.lang === 'python'; }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#lesson-{seed_py_slug} details.predict",
         "caption": "One click reveals -- the struggle comes first, the code second.",
         "js": ["() => { const d = document.querySelector('#lesson-{seed_py_slug} details.predict'); "
               "if (!d) return 'missing'; d.querySelector('summary').click(); "
               "return d.open ? 'revealed' : 'still-shut'; }"],
         "assert_js": "() => { const d = document.querySelector('details.predict'); "
                      "return !!d && d.open; }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 6,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#lesson-{seed_ts_slug} details.predict",
         "caption": "Same cover on TypeScript -- the snippet reveals underneath, tagged JavaScript.",
         "js": ["() => { const d = document.querySelector('#lesson-{seed_ts_slug} details.predict'); "
               "if (!d) return 'missing'; d.querySelector('summary').click(); "
               "return d.open ? 'revealed' : 'still-shut'; }"],
         "assert_js": "() => { const d = document.querySelector('details.predict'); "
                      "return !!d && d.open && d.querySelector('pre').dataset.lang === 'javascript'; }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 16",
         "title": "Struggle first, code second.",
         "subtitle": "Predict-then-reveal covers guard every lesson snippet."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant a Python lesson and a TypeScript lesson, both covered."""
    con = sqlite3.connect(db_path)
    try:
        nodes = ["demo/calc.py:add", "demo/app.ts:greet"]
        cids = [f"{MODULE_ID}:{n}" for n in nodes]
        for cid in cids:
            con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
            con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": nodes[0], "name": "add", "kind": "function",
             "file": "demo/calc.py", "line": 1,
             "summary": "add() totals two numbers via its defaults.",
             "docstring": "Add a and b.", "callers": [], "callees": [],
             "key_lines": "", "source": PY_SOURCE, "complexity": 1,
             "how": list(PY_HOW), "worked": None,
             "dualcode": {"steps": list(PY_HOW), "states": []}},
            {"concept_id": nodes[1], "name": "greet", "kind": "function",
             "file": "demo/app.ts", "line": 1,
             "summary": "greet() prefixes any name with hi.",
             "docstring": "Greet a name.", "callers": [], "callees": [],
             "key_lines": "", "source": TS_SOURCE, "complexity": 1,
             "how": list(TS_HOW), "worked": None,
             "dualcode": {"steps": list(TS_HOW), "states": []}},
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b16", "Predict-cover lesson module", now,
             json.dumps(lessons)))
        specs = [("add", "demo/calc.py"), ("greet", "demo/app.ts")]
        for (name, file), cid in zip(specs, cids):
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, name, "function", file, 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "py_slug": _slug(nodes[0]), "ts_slug": _slug(nodes[1])}
    finally:
        con.close()
