"""Feature demo: debugging kata library (F-88).

Full behavior: each lesson's snippet matches the eight-shape bug
catalog at generation and the module page shows attached katas
(buggy/fixed pair plus failing call) per lesson. seed_db sets one
rendered lesson's source to a snippet matching exactly two shapes
and stamps the kata frame the way pipeline.create_module does; the
terminal beat proves the real matcher agrees.
"""
from __future__ import annotations

import json
import re
import sqlite3

SNIPPET = ("total = sum(xs) / len(xs)\n"
           "for i in range(len(xs)):\n"
           "    use(xs[i])")

# Catalog order mirrors debugkata.SHAPES so the seed stamps exactly
# what enrich_lesson would (same rules, same cap of two).
SPOT_RULES = (
    ("off-by-one", r"\[\s*len\("),
    ("wrong-operator", r"if\s+[^:\n]*[^=!<>]=(?![=])"),
    ("mutable-default", r"def\s+\w+\([^)]*=\s*(\[\]|\{\})"),
    ("none-deref", r"=\s*None\b"),
    ("swallowed-exception", r"except(?:\s+Exception)?\s*:[^\n]*\n\s*pass"),
    ("fencepost-range", r"range\("),
    ("aliasing-mutation", r"\.append\("),
    ("int-division", r"(?<!/)/(?![/=])"),
)

SCENARIO = {
    "id": "debugkata",
    "kind": "feature",
    "batch": 20,
    "item": "F-88",
    "title": "Debugging kata library",
    "blurb": "Meet the eight classic bug shapes with a failing call each, drawn from synthetic and real code.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Feature F-88",
         "title": "Debugging kata library",
         "subtitle": "Eight classic bug shapes -- your snippet matches at most two."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-debugkata",
         "caption": "Status documents the eight shapes with a live fencepost sample.",
         "assert_js": "() => !!document.querySelector('#status-b20-debugkata') && "
                      "document.body.innerText.includes('Fencepost range') && "
                      "document.body.innerText.includes('eight classic')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The real matcher: the snippet hits fencepost-range plus int-division; clean code hits none.",
         "commands": [
             ["python3", "-c",
              "from groundwork import debugkata as m; "
              "snip = 'total = sum(xs) / len(xs)\\nfor i in range(len(xs)):\\n    use(xs[i])'; "
              "print('shapes:', len(m.list_shapes())); "
              "print('matched:', [k['id'] for k in m.katas_for('avg', snip)]); "
              "frame = {'name': 'avg'}; "
              "print('stamped:', [k['id'] for k in m.enrich_lesson(frame, snip).get('kata', [])]); "
              "print('clean:', m.enrich_lesson({'name': 'x'}, 'return a + b').get('kata'))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}#lesson-{seed_slug}",
         "focus": "#lesson-{seed_slug} .debugkata",
         "caption": "The module lesson shows both katas: buggy versus fixed, each with its failing call.",
         "assert_js": "() => document.querySelectorAll('.debugkata').length === 2 && "
                      "document.body.innerText.includes('Failing call')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture: the lesson frame carries the stamped kata pair.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3, json; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "les = json.loads(con.execute(\"SELECT lessons FROM modules WHERE id='{seed_mid}'\").fetchone()[0]); "
              "hit = [l for l in les if l.get('name') == '{seed_name}'][0]; "
              "print('kata:', [k['id'] for k in hit.get('kata', [])])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Name the shape, fix the bug.",
         "subtitle": "debugkata.py stamps at generation -- unmatched snippets stay byte-identical."},
    ],
}


def _slug(text) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(text or ""))
    return "-".join(filter(None, out.split("-"))) or "lesson"


def _safe(name) -> bool:
    return bool(name) and all(ch.isalnum() or ch in " _-." for ch in name)


def seed_db(db_path: str) -> dict:
    """Snippet + stamped kata frame on one rendered lesson."""
    con = sqlite3.connect(db_path)
    try:
        for mid, raw in con.execute("SELECT id, lessons FROM modules"):
            try:
                lessons = json.loads(raw or "[]")
            except ValueError:
                continue
            nodes = {r[0].split(":", 1)[1] if ":" in r[0] else r[0]
                     for r in con.execute("SELECT id FROM concepts"
                                          " WHERE module_id=?", (mid,))}
            target = next((L for L in lessons
                           if isinstance(L, dict) and L.get("concept_id") in nodes
                           and (L.get("summary") or "").strip()
                           and _safe(L.get("name") or "")), None)
            if target is None:
                continue
            matched = [sid for sid, rule in SPOT_RULES
                       if re.search(rule, SNIPPET)][:2]
            if matched != ["fencepost-range", "int-division"]:
                return {"seeded": False, "reason": "snippet drift"}
            target["source"] = SNIPPET
            # Full catalog entries (groundwork/debugkata.py SHAPES): the
            # terminal beat runs the real katas_for over the same
            # snippet, so any catalog drift shows on screen.
            target["kata"] = [
                {"id": "fencepost-range", "title": "Fencepost range",
                 "buggy": "for i in range(len(xs)):\n    use(xs[i + 1])",
                 "fixed": "for i in range(len(xs) - 1):\n    use(xs[i + 1])",
                 "failing_call": "last i  -> IndexError",
                 "blurb": "the last step walks off the end"},
                {"id": "int-division", "title": "Integer division",
                 "buggy": "half = total / 2",
                 "fixed": "half = total // 2",
                 "failing_call": "5 / 2  -> 2.5, not 2",
                 "blurb": "float division where an int belongs"},
            ]
            con.execute("UPDATE modules SET lessons=? WHERE id=?",
                        (json.dumps(lessons), mid))
            con.commit()
            return {"seeded": True, "mid": mid,
                    "slug": _slug(target["concept_id"]),
                    "name": target.get("name") or ""}
        return {"seeded": False, "reason": "no rendered lesson"}
    finally:
        con.close()
