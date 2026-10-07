"""Feature demo: generated lessons ship diagram+trace packs (F-60 integration).

Full behavior: lesson_for stores the walkthrough as dualcode steps at
generation time, create_module fills measured trace states behind
them, and the module page renders words + diagram + trace for every
lesson that has steps. Legacy lessons without steps render no pack.
seed_db plants a two-concept module (one stepped, one stepless).
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b16-dual"
ADD_HOW = ["Read the two defaults", "Add them into total",
           "Return total to the caller"]
ADD_SOURCE = ("def add(a=2, b=3):\n    total = a + b\n    return total\n")
FLAT_SOURCE = ("def flat(xs):\n    out = []\n    for x in xs:\n        out.append(x)\n    return out\n")

SCENARIO = {
    "id": "dualpack",
    "kind": "feature",
    "batch": 16,
    "item": "F-60",
    "title": "Lessons ship diagram packs",
    "blurb": "Generation stores diagram steps, traced runs fill states -- the lesson page renders words, diagram, trace.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 16 - Feature F-60",
         "title": "Lessons ship diagram packs",
         "subtitle": "Generation stores diagram steps, traced runs fill states -- the lesson page renders words, diagram, trace."},
        {"type": "terminal", "duration": 6,
         "caption": "Generation stores the steps: lesson_for files the walkthrough as dualcode.",
         "commands": [
             ["python3", "-c",
              "import tempfile; from pathlib import Path; "
              "from groundwork import dualcode as d, graph as g, pipeline as p, select as s; "
              "t = Path(tempfile.mkdtemp(prefix='gw-dc-')); "
              "(t / 'calc.py').write_text('def add(a=2, b=3):\\n    total = a + b\\n    return total\\n'); "
              "c = s.ScoredConcept('calc.py:add', 'add', 'function', 'calc.py', 1, 1.0, 1.0, 1.0, 1.0); "
              "les = p.lesson_for(str(t), c, g.build_repo_graph(str(t))); "
              "print('steps == how:', les['dualcode']['steps'] == les['how']); "
              "print('diagram boxes:', d.diagram_svg(les['dualcode']['steps']).count('<rect'))"],
         ]},
        {"type": "terminal", "duration": 8,
         "caption": "Traced runs fill the states: create_module measures values behind the steps.",
         "commands": [
             ["python3", "-c",
              "import tempfile; from pathlib import Path; "
              "from groundwork import db as dbmod, pipeline as p; "
              "t = Path(tempfile.mkdtemp(prefix='gw-dc-')); "
              "(t / 'calc.py').write_text('def add(a=2, b=3):\\n    total = a + b\\n    return total\\n'); "
              "(t / 'app.ts').write_text(\"export function greet(name: string): string {\\n  return 'hi ' + name;\\n}\\n\"); "
              "db = str(t / 'dc.db'); dbmod.init_db(db); con = dbmod.connect(db); "
              "al = [{'concept': 'add', 'summary': 'add() totals two numbers.', 'how': ['Read the defaults', 'Trace the total']}, "
              "{'concept': 'greet', 'summary': 'greet() prefixes hi.', 'how': ['Read the name', 'Prefix hi']}]; "
              "ae = [{'concept': 'add', 'type': 1, 'front': 'add() with no args?', 'back': '5.'}, "
              "{'concept': 'greet', 'type': 1, 'front': 'greet bob?', 'back': 'hi bob.'}]; "
              "out = p.create_module(con, repo=str(t), learner_level='beginner', task_summary='d', agent_lessons=al, agent_exercises=ae); "
              "con.close(); "
              "tr = [L for L in out['lessons'] if (L.get('worked') or {}).get('trace')]; "
              "print('lessons:', len(out['lessons']), '| traced:', len(tr)); "
              "print('measured states:', tr[0]['dualcode']['states'])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#lesson-{seed_add_slug} .dual-pack",
         "caption": "The generated lesson carries its pack: words and diagram up top, measured trace below.",
         "assert_js": "() => { const s = document.querySelector('.dual-pack'); "
                      "return !!s && !!s.querySelector('.dual-diagram') && !!s.querySelector('.dual-trace'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 6,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#lesson-{seed_flat_slug} details.predict",
         "caption": "Legacy lessons without steps render no pack -- the cover still guards the snippet.",
         "assert_js": "() => !!document.querySelector('details.predict') && !document.querySelector('.dual-pack')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 16",
         "title": "Words, picture, trace.",
         "subtitle": "Dual-coding packs ride every generated lesson -- two channels, one concept."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant a stepped lesson (pack) and a stepless legacy one (no pack)."""
    con = sqlite3.connect(db_path)
    try:
        nodes = ["demo/dual.py:add", "demo/dual.py:flat"]
        cids = [f"{MODULE_ID}:{n}" for n in nodes]
        for cid in cids:
            con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
            con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": nodes[0], "name": "add", "kind": "function",
             "file": "demo/dual.py", "line": 1,
             "summary": "add() totals two numbers via its defaults.",
             "docstring": "Add a and b.", "callers": [], "callees": [],
             "key_lines": "", "source": ADD_SOURCE, "complexity": 1,
             "how": list(ADD_HOW), "worked": None,
             "dualcode": {"steps": list(ADD_HOW),
                          "states": ["2", "5", "5"]}},
            {"concept_id": nodes[1], "name": "flat", "kind": "function",
             "file": "demo/dual.py", "line": 5,
             "summary": "flat() copies a list item by item.",
             "docstring": "Copy the list.", "callers": [], "callees": [],
             "key_lines": "", "source": FLAT_SOURCE, "complexity": 2,
             "how": [], "worked": None},
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b16", "Diagram-pack lesson module", now,
             json.dumps(lessons)))
        for node, cid in zip(nodes, cids):
            name = node.rsplit(":", 1)[1]
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, name, "function", "demo/dual.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "add_slug": _slug(nodes[0]), "flat_slug": _slug(nodes[1])}
    finally:
        con.close()
