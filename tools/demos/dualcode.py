"""Feature demo: dual-coding packs (F-60).

Full behavior: generated lessons carry diagram steps plus measured
states, and lesson rendering emits the triple -- words line, inline
SVG box-and-arrow diagram, worked trace table -- on every module page
(since Batch 16). seed_db picks a module whose lessons have steps but
no measured trace (traced lessons replay step-by-step instead).
"""
from __future__ import annotations

import json
import sqlite3


def _has_pack_lessons(lessons_json) -> bool:
    try:
        lessons = json.loads(lessons_json or "[]")
    except ValueError:
        return False
    for lesson in lessons:
        if not isinstance(lesson, dict):
            continue
        steps = [s for s in (lesson.get("how") or [])
                 if isinstance(s, str) and s.strip()]
        worked = lesson.get("worked")
        traced = isinstance(worked, dict) and worked.get("trace")
        if steps and not traced:
            return True
    return False


SCENARIO = {
    "id": "dualcode",
    "kind": "feature",
    "batch": 13,
    "item": "F-60",
    "title": "Dual-coding packs",
    "blurb": "Every key idea gets words plus a diagram plus a worked trace.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Feature F-60",
         "title": "Dual-coding packs",
         "subtitle": "Words plus a diagram plus a worked trace -- two channels, one concept."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-dualcode",
         "caption": "Status homes the engine with a live retry-with-backoff pack.",
         "assert_js": "() => !!document.querySelector('#status-b13-dualcode') && "
                      "!!document.querySelector('.dual-pack')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: steps become boxes, arrows, and trace rows.",
         "commands": [
             ["python3", "-c",
              "from groundwork import dualcode as m; "
              "steps = ['attempt the call', 'sleep 1s', 'give up']; "
              "print('boxes:', m.diagram_svg(steps).count('<rect')); "
              "print('rows:', m.trace_table(steps, ['ok', 'slept', 'raised']).count('<tr>') - 1); "
              "print('capped:', len(m.clean_steps(['x'] * 20)) == 8)"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_module_id}",
         "focus": ".dual-pack",
         "caption": "The lesson's key ideas render as diagram plus trace -- from live lesson steps.",
         "assert_js": "() => !!document.querySelector('.dual-diagram') && "
                      "!!document.querySelector('.dual-trace')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Read it twice, keep it.",
         "subtitle": "dualcode.py packs every lesson -- generation stores, rendering emits."},
    ],
}


def seed_db(db_path: str) -> dict:
    """First module with untraced how-steps (packs, not step replays)."""
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id, lessons FROM modules ORDER BY rowid").fetchall()
        for mid, lessons_json in rows:
            if _has_pack_lessons(lessons_json):
                return {"seeded": True, "module_id": mid}
        return {"seeded": False, "reason": "no pack lessons"}
    finally:
        con.close()
