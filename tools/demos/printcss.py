"""Improvement demo: print stylesheet (I-27).

One function, no DB changes: print_css() returns @media print CSS
so lessons print as serif study sheets. Real caller path: every
module lesson section carries a 'Print handout' link opening the
standalone handout doc, which embeds this CSS in its <style> block.
"""
from __future__ import annotations

import json
import sqlite3

SCENARIO = {
    "id": "printcss",
    "kind": "improvement",
    "batch": 5,
    "item": "I-27",
    "title": "Print stylesheet",
    "blurb": "Lessons print cleanly as serif study sheets.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-27",
         "title": "Print stylesheet",
         "subtitle": "Lessons print cleanly as serif study sheets."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-printcss",
         "caption": "Status documents the improvement with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-printcss')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}",
         "caption": "Every lesson section offers a Print handout link -- the entry path.",
         "js": ["() => { const a = document.querySelector('a.handout-link'); "
                "if (!a) return 'missing'; a.id = 'handout-hit'; return 'tagged'; }"],
         "focus": "#handout-hit",
         "assert_js": "() => { const a = document.querySelector('#handout-hit'); "
                      "return !!a && a.href.includes('/handout/'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}/handout/{seed_node}",
         "caption": "The handout embeds @media print CSS: chrome hidden, serif ink, sane breaks.",
         "assert_js": "() => { const s = document.querySelector('style'); "
                      "return !!s && s.textContent.includes('@media print') "
                      "&& s.textContent.includes('break-inside'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "The whole rule: one function returns the print block.",
         "commands": [
             ["python3", "-c",
              "from groundwork import printcss as m; "
              "print(m.print_css())"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "File > Print, done right.",
         "subtitle": "printcss.py feeds the handout -- study sheets, not web chrome."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pick a module lesson with study content for the handout beats.

    Reads the fixture copy only; returns URL-safe tokens (lesson
    name, matched by handout.page_for against concept_id/name/node).
    """
    con = sqlite3.connect(db_path)
    try:
        for (mid, lessons) in con.execute("SELECT id, lessons FROM modules"):
            try:
                items = json.loads(lessons or "[]")
            except ValueError:
                continue
            for les in items:
                if not isinstance(les, dict):
                    continue
                if not any(les.get(k) for k in (
                        "summary", "how", "key_lines", "worked",
                        "docstring", "source")):
                    continue
                name = les.get("name") or ""
                if name and "/" not in name and " " not in name:
                    return {"seeded": True, "mid": mid, "node": name}
        return {"seeded": False, "reason": "no content lesson"}
    finally:
        con.close()
