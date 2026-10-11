"""Feature demo: knowledge garden (F-104).

Full behavior: History shows one plot per module, bedded by repo —
seed (nothing owned), sprout (some), bloom (all) — as inline SVG.
seed_db plants three modules in one early-sorting repo covering all
three stages.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

REPO = "000-demo-garden"
MODULES = ("demo-garden-seed", "demo-garden-sprout", "demo-garden-bloom")
# (module, [(node, owned?)]) — seed 0/1, sprout 1/2, bloom 2/2.
PLOTS = (
    ("demo-garden-seed", (("demo/garden.py:dormant", False),)),
    ("demo-garden-sprout",
     (("demo/garden.py:first", True), ("demo/garden.py:next", False))),
    ("demo-garden-bloom",
     (("demo/garden.py:red", True), ("demo/garden.py:blue", True))),
)

SCENARIO = {
    "id": "knowngarden",
    "kind": "feature",
    "batch": 22,
    "item": "F-104",
    "title": "Knowledge garden",
    "blurb": "Your repo map in bloom — every module a plot, every owned a petal.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Feature F-104",
         "title": "Knowledge garden",
         "subtitle": "Seed, sprout, bloom -- proof taking root across the repos."},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "js": ["() => { const h = [...document.querySelectorAll('h3')].find(e => e.textContent.trim() === '000-demo-garden'); const bed = h && h.nextElementSibling; if (bed && bed.classList.contains('bed')) bed.id = 'seed-bed'; return bed ? 'marked' : 'missing'; }"],
         "focus": "#seed-bed",
         "caption": "The demo bed shows all three stages: dormant seed, half-sprout, full bloom.",
         "assert_js": "() => ['seed', 'sprout', 'bloom'].every(s => !!document.querySelector('.plot.' + s))",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Stage follows the owned fraction; plots link to their modules.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import knowngarden as m; "
              "print('0/1:', m.stage_of(0, 1), '| 1/2:', m.stage_of(1, 2), '| 2/2:', m.stage_of(2, 2)); "
              "rows = [r for r in m.garden_stats(os.environ.get('DEMO_DB', 'groundwork.db')) if r[0] == '000-demo-garden']; "
              "[print(r[1], r[3], '/', r[4], m.stage_of(r[3], r[4])) for r in rows]"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b22-knowngarden",
         "caption": "Status documents the beds with a two-plot sample.",
         "assert_js": "() => !!document.querySelector('#status-b22-knowngarden')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Tend the beds.",
         "subtitle": "knowngarden.py blooms by owned fraction -- fallow until first proof."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant seed/sprout/bloom modules in one early-sorting repo."""
    con = sqlite3.connect(db_path)
    try:
        created = "2020-01-01T00:00:00Z"
        for mid, _specs in PLOTS:
            for row in con.execute(
                    "SELECT cards.id FROM cards JOIN concepts"
                    " ON concepts.id = cards.concept_id"
                    " WHERE concepts.module_id=?", (mid,)).fetchall():
                con.execute("DELETE FROM reviews WHERE card_id=?", (row[0],))
                con.execute("DELETE FROM cards WHERE id=?", (row[0],))
            con.execute("DELETE FROM concepts WHERE module_id=?", (mid,))
            con.execute("DELETE FROM modules WHERE id=?", (mid,))
        for mid, specs in PLOTS:
            lessons = [
                {"concept_id": node, "name": node.split(":")[-1].title(),
                 "kind": "function", "file": "demo/garden.py",
                 "line": i + 1, "summary": f"Garden plot {node}."}
                for i, (node, _owned) in enumerate(specs)]
            con.execute(
                "INSERT INTO modules(id, repo, task_summary, created_at,"
                " lessons) VALUES(?, ?, ?, ?, ?)",
                (mid, REPO, f"Garden {mid.split('-')[-1]} module",
                 created, json.dumps(lessons)))
            for i, (node, owned) in enumerate(specs):
                cid = f"{mid}:{node}"
                con.execute(
                    "INSERT INTO concepts(id, module_id, name, kind, file,"
                    " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                    (cid, mid, node.split(":")[-1].title(), "function",
                     "demo/garden.py", i + 1, 0.0))
                if not owned:
                    continue
                card = f"{mid}-card-{i}"
                con.execute(
                    "INSERT INTO cards(id, concept_id, exercise_type,"
                    " front, back, due) VALUES(?, ?, '19', ?, ?, ?)",
                    (card, cid, f"Refactor {node}?", "Done.",
                     "2001-01-01T12:00:00Z"))
                for when in ("2026-09-01T09:00:00Z",
                             "2026-09-08T09:00:00Z"):
                    con.execute(
                        "INSERT INTO reviews(card_id, grade, confidence,"
                        " reviewed_at, submission) VALUES(?, 5, 4, ?, ?)",
                        (card, when, "knowngarden seed"))
        con.commit()
        return {"seeded": True, "repo": REPO,
                "modules": list(MODULES)}
    finally:
        con.close()
