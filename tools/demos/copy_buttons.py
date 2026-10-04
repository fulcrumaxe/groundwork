"""Improvement demo: copy buttons (Batch 1).

Full functionality: one page script (web.py GLOBAL_JS) wraps every <pre>
in a .codewrap div with a Copy button that copies the block via
navigator.clipboard. seed_db finds a module whose lesson HTML contains
a code block and returns its id plus the lesson anchor; the beats film
the wrapped block, click its button, and show the wiring in source.
"""
from __future__ import annotations

import json
import sqlite3

SCENARIO = {
    "id": "copy-buttons",
    "kind": "improvement",
    "batch": 1,
    "item": "I-61",
    "title": "Copy buttons",
    "blurb": "Every code block grows a Copy button. Try one in the lesson below.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Improvement copy-buttons",
         "title": "Copy buttons",
         "subtitle": "Every code block grows a Copy button."},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules/{seed_mid}",
         "focus": "#lesson-{seed_lesson} .codewrap",
         "caption": "Every code block carries its own Copy button, wired by one script.",
         "assert_js": "() => { const w = document.querySelector('main .codewrap'); "
                      "return !!w && !!w.querySelector('pre') "
                      "&& !!w.querySelector('button.copybtn'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "The wiring in source: each pre gets a wrap plus a Copy button.",
         "commands": [
             ["bash", "-lc",
              "grep -n 'codewrap\\|copybtn' groundwork/web.py"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}",
         "focus": "#lesson-{seed_lesson} .codewrap",
         "caption": "One click copies the block; the button confirms it landed.",
         "js": ["() => { const b = document.querySelector("
                "\"#lesson-{seed_lesson} .codewrap button.copybtn\"); "
                "if (!b) return 'copybtn-missing'; b.click(); return 'clicked'; }"],
         "assert_js": "() => { const w = document.querySelector('main .codewrap'); "
                      "return !!w && !!w.querySelector('pre') "
                      "&& !!w.querySelector('button.copybtn'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "The fixture module really has code lessons to copy from.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3, json; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "les = json.loads(con.execute(\"SELECT lessons FROM modules WHERE id='{seed_mid}'\").fetchone()[0]); "
              "print('code lessons:', sum(1 for L in les if L.get('source')))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Copy, paste, keep reading.",
         "subtitle": "One script wires every block on every page."},
    ],
}


def _slug(text: str) -> str:
    """Anchor slug mirroring groundwork.lessons.slug (stdlib only)."""
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in (text or ""))
    return "-".join(filter(None, out.split("-"))) or "lesson"


def _lesson_has_code(lesson: dict) -> bool:
    try:
        if not isinstance(lesson, dict):
            return False
        if lesson.get("source"):
            return True
        levels = lesson.get("levels") or {}
        if isinstance(levels, dict):
            for view in levels.values():
                if not isinstance(view, dict):
                    continue
                if view.get("code"):
                    return True
                for blk in view.get("blocks") or []:
                    if isinstance(blk, dict) and blk.get("pre"):
                        return True
        return False
    except Exception:
        return False


def seed_db(db_path: str) -> dict:
    """A real module id plus a lesson anchor whose section has a code block.

    Scans modules newest-first and returns the first concept (page
    order) whose lesson carries source or level code; the anchor matches
    Handler.module_html exactly ('lesson-' + slug of the concept node).
    No fixture rows change: every module page already has code blocks,
    so seeding only selects where to point the camera.
    """
    con = sqlite3.connect(db_path)
    try:
        modules = con.execute(
            "SELECT id, lessons FROM modules ORDER BY rowid DESC").fetchall()
        if not modules:
            return {"seeded": False, "reason": "no modules"}
        for mid, lessons_raw in modules:
            try:
                lessons = json.loads(lessons_raw or "[]")
            except (TypeError, ValueError):
                lessons = []
            by_concept = {}
            for entry in lessons if isinstance(lessons, list) else []:
                try:
                    by_concept[entry.get("concept_id", "")] = entry
                except (AttributeError, TypeError):
                    continue
            concepts = con.execute(
                "SELECT id FROM concepts WHERE module_id=?", (mid,)).fetchall()
            if not concepts:
                continue
            first_node = None
            for (cid,) in concepts:
                node = cid.split(":", 1)[1] if ":" in cid else cid
                if first_node is None:
                    first_node = node
                lesson = by_concept.get(node, by_concept.get(cid, {}))
                if _lesson_has_code(lesson):
                    return {"seeded": True, "mid": mid,
                            "lesson": _slug(node)}
            if first_node is not None:
                return {"seeded": True, "mid": mid,
                        "lesson": _slug(first_node),
                        "note": "no coded lesson; first section"}
        return {"seeded": False, "reason": "no concepts"}
    finally:
        con.close()
