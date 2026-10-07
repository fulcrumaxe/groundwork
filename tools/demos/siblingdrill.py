"""Feature demo: mastered siblings drill the new concept (F-59 integration).

Full behavior: render_levels appends an elaboration drill connecting
the lesson to mastered (>=0.85) siblings -- the two closest owned
concepts become named partners. One owned partner is not enough: the
drill needs two, so siblings with a single owned peer render none.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b16-elab"
LESSONS = [
    ("demo/elab.py:add", "add", 0.2,
     "add() totals two numbers via its defaults.",
     "def add(a=2, b=3):\n    total = a + b\n    return total\n",
     ["Read the two defaults", "Add them into total",
      "Return total to the caller"]),
    ("demo/elab.py:total", "total", 0.9,
     "total() keeps a running sum accumulator.",
     "def total(xs):\n    s = 0\n    for x in xs:\n        s += x\n    return s\n",
     ["Start at zero", "Fold each item in"]),
    ("demo/elab.py:main", "main", 0.95,
     "main() entry point calling add for the demo.",
     "def main():\n    print(add())\n",
     ["Call add with defaults", "Print the result"]),
]

SCENARIO = {
    "id": "siblingdrill",
    "kind": "feature",
    "batch": 16,
    "item": "F-59",
    "title": "Mastered siblings drill you",
    "blurb": "Two owned siblings become named drill partners -- one owned peer is not enough.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 16 - Feature F-59",
         "title": "Mastered siblings drill you",
         "subtitle": "Two owned siblings become named drill partners -- one owned peer is not enough."},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one call: top-tier siblings are owned, the two closest drill you.",
         "commands": [
             ["python3", "-c",
              "from groundwork import elaboration as e, lessons as l; "
              "lm = {'add': {'name': 'add', 'summary': 'totals two numbers'}, "
              "'total': {'name': 'total', 'summary': 'running sum accumulator'}, "
              "'main': {'name': 'main', 'summary': 'entry point calling add'}}; "
              "mo = {'add': 0.2, 'total': 0.9, 'main': 0.95}; "
              "owned = l.owned_lessons(lm, mo, 'add'); "
              "print('owned for add:', [o['name'] for o in owned]); "
              "d = e.elaboration_drill({'name': 'add', 'summary': 'totals two numbers'}, owned); "
              "print('partners:', d['partners']); "
              "print('one owned -> no drill:', e.elaboration_drill({'name': 'add', 'summary': 'x'}, owned[:1])['partners'] == [])"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#drill-shot",
         "caption": "Two mastered siblings become named partners -- connect the new idea to both.",
         "js": ["() => { const hs = [...document.querySelectorAll('#lesson-{seed_add_slug} h4')]; "
               "const h = hs.find(e => e.textContent.includes('elaboration drill')); "
               "if (!h) return 'missing'; h.parentElement.id = 'drill-shot'; return 'tagged'; }"],
         "assert_js": "() => { const d = document.querySelector('#drill-shot'); "
                      "return !!d && d.textContent.includes('total') && d.textContent.includes('main'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 6,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#lesson-{seed_total_slug} .dual-pack",
         "caption": "One owned peer is not enough -- mastered siblings drill nobody.",
         "assert_js": "() => ![...document.querySelectorAll('main h4')]"
                      ".some(e => e.textContent.includes('elaboration drill'))",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 16",
         "title": "Own two, connect the third.",
         "subtitle": "Elaboration drills bridge new concepts to mastered siblings."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant a new concept plus two mastered siblings on one module."""
    con = sqlite3.connect(db_path)
    try:
        cids = [f"{MODULE_ID}:{node}" for node, _n, _m, _s, _src, _h in LESSONS]
        for cid in cids:
            con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
            con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": node, "name": name, "kind": "function",
             "file": "demo/elab.py", "line": 1, "summary": summary,
             "docstring": summary, "callers": [], "callees": [],
             "key_lines": "", "source": source, "complexity": 1,
             "how": list(how), "worked": None,
             "dualcode": {"steps": list(how), "states": []}}
            for node, name, _m, summary, source, how in LESSONS
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b16", "Elaboration-drill lesson module", now,
             json.dumps(lessons)))
        for (node, name, mastery, _s, _src, _h), cid in zip(LESSONS, cids):
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, name, "function", "demo/elab.py", 1,
                 mastery))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "add_slug": _slug(cids[0].split(":", 1)[1]),
                "total_slug": _slug(cids[1].split(":", 1)[1])}
    finally:
        con.close()
