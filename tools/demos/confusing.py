"""Improvement demo: per-section confusing flags (I-134).

Full behavior: every titled lesson block carries a confusing toggle; flagging
one shows a confirm page and raises a regen-queue banner atop the module
naming the flagged sections. seed_db plants a plain lesson; the beats flag
a real section through the real POST route and film the banner it raises.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-confusing-134"
NODE = "demo/flag.py:total"
CONCEPT_ID = f"{MODULE_ID}:{NODE}"

SCENARIO = {
    "id": "confusing",
    "kind": "improvement",
    "batch": 21,
    "item": "I-134",
    "title": "Per-section confusing flags",
    "blurb": "Flag the exact block that lost you -- authors rewrite flagged sections first.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Improvement I-134",
         "title": "Per-section confusing flags",
         "subtitle": "Not 'this lesson is hard' -- this exact block lost me."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-confusing",
         "caption": "Status documents the flag queue with a live sample.",
         "assert_js": "() => !!document.querySelector('#status-b21-confusing')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: flags queue oldest-first; unflagging drops out.",
         "commands": [
             ["python3", "-c",
              "from groundwork import confusing as m; "
              "flags = m.mark(m.mark({}, 'm:c#what-it-does'), 'm:c#how-it-works'); "
              "print('queue:', m.regen_queue(flags), '| count:', m.queue_count(flags)); "
              "print('after unmark:', m.regen_queue(m.unmark(flags, 'm:c#what-it-does'))); "
              "print(m.queue_banner_html(flags)[:70])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "focus": "form.confusing",
         "caption": "Every titled block carries its own confusing toggle.",
         "assert_js": "() => { const b = document.querySelector('form.confusing button'); "
                      "return !!b && b.innerText.includes('Mark confusing'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 14,
         "url_path": "/modules/{seed_mid}",
         "caption": "Flag the block -- the confirm page says authors rewrite these first.",
         "js": ["() => { const f = document.querySelector('form.confusing'); "
               "if (!f) return 'toggle-missing'; f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 4000)",
         "poll_want": "Flag saved",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('Flag saved')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "focus": ".regen-queue",
         "caption": "The module now carries a regen queue naming the flagged block.",
         "assert_js": "() => { const b = document.querySelector('.regen-queue'); "
                      "return !!b && b.innerText.includes('1 section(s) flagged'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Flagged first, fixed first.",
         "subtitle": "confusing.py queues flags -- unflagged pages stay byte-identical."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a module with one plain lesson (flags arrive via the POST)."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM concepts WHERE id=?", (CONCEPT_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lesson = {"concept_id": NODE, "name": "total", "kind": "function",
                  "file": "demo/flag.py", "line": 1,
                  "summary": "total() sums a running total from row values.",
                  "docstring": "Sum rows into a running total.",
                  "how": ["Seed the total at zero.", "Add each row once."]}
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/confusing", "Confusing flags module", now,
             json.dumps([lesson])))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CONCEPT_ID, MODULE_ID, "total", "function",
             "demo/flag.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID, "cid": CONCEPT_ID}
    finally:
        con.close()
