"""Improvement demo: diagrams-per-lesson gate (I-125).

Full behavior: lessons with study text but zero visuals get a
"Needs a visual" badge plus a TOC mark on the module rendering
path; passing lessons render nothing extra. seed_db strips all
visuals from one rendered lesson of a 2+ lesson module and forces
a sibling to pass, so both states film on the real caller path.
"""
from __future__ import annotations

import json
import sqlite3

SCENARIO = {
    "id": "diagrams",
    "kind": "improvement",
    "batch": 20,
    "item": "I-125",
    "title": "Every lesson gets a visual",
    "blurb": "Lessons missing a visual are flagged until fixed.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Improvement I-125",
         "title": "Every lesson gets a visual",
         "subtitle": "Diagram, trace, code, or figure -- missing all four flags the lesson."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-diagrams",
         "caption": "Status documents the gate with a live failing sample.",
         "assert_js": "() => !!document.querySelector('#status-b20-diagrams') && "
                      "document.body.innerText.includes('Needs a visual')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The gate in one line: words without visuals fail; a code snippet passes.",
         "commands": [
             ["python3", "-c",
              "from groundwork import diagrams as m; "
              "fail = {'summary': 'words, no picture.'}; "
              "ok = {'summary': 'x', 'source': 'def f(): pass'}; "
              "print('fail:', m.gate_lesson(fail)['ok'], '|', m.badge_html(fail)[:42]); "
              "print('pass:', m.gate_lesson(ok), '|', repr(m.badge_html(ok))); "
              "print('empty passes vacuously:', m.gate_lesson({})['ok'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "caption": "The module TOC marks the failing lesson -- needs visual.",
         "assert_js": "() => { const t = document.querySelector('#readtime'); "
                      "return !!t && t.innerText.includes('needs visual'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}#lesson-{seed_fail_slug}",
         "focus": "#lesson-{seed_fail_slug} .needs-visual",
         "caption": "The failing lesson carries the badge: no diagram, trace, code, or figure.",
         "assert_js": "() => { const b = document.querySelector('.needs-visual'); "
                      "return !!b && b.innerText.includes('Needs a visual'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 7,
         "url_path": "/modules/{seed_mid}#lesson-{seed_pass_slug}",
         "focus": "#lesson-{seed_pass_slug}",
         "caption": "The passing sibling renders nothing extra -- the gate stays quiet.",
         "assert_js": "() => !!document.querySelector('#lesson-{seed_pass_slug}') && "
                      "!document.querySelector('#lesson-{seed_pass_slug} .needs-visual')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Flagged until fixed.",
         "subtitle": "diagrams.py counts visual evidence -- empty lessons pass vacuously."},
    ],
}


def _slug(text) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(text or ""))
    return "-".join(filter(None, out.split("-"))) or "lesson"


def _strip_visuals(lesson: dict) -> None:
    lesson["source"] = ""
    lesson["key_lines"] = ""
    lesson.pop("dualcode", None)
    lesson.pop("worked", None)
    lesson.pop("figure", None)
    if not (lesson.get("summary") or "").strip():
        lesson["summary"] = "A lesson with words but no picture."


def seed_db(db_path: str) -> dict:
    """Strip one rendered lesson; force a rendered sibling to pass."""
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
            rendered = [L for L in lessons
                        if isinstance(L, dict) and L.get("concept_id") in nodes]
            if len(rendered) < 2:
                continue
            fail, keep = rendered[0], rendered[1]
            _strip_visuals(fail)
            keep["source"] = (keep.get("source") or "").strip() or "def f(): pass"
            con.execute("UPDATE modules SET lessons=? WHERE id=?",
                        (json.dumps(lessons), mid))
            con.commit()
            return {"seeded": True, "mid": mid,
                    "fail_slug": _slug(fail["concept_id"]),
                    "pass_slug": _slug(keep["concept_id"])}
        return {"seeded": False, "reason": "no 2-lesson module"}
    finally:
        con.close()
