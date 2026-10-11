"""Improvement demo: see-it-in-the-real-file links + viewer (I-129).

Full behavior: lesson headers link to the concept's exact source
line, and the /file viewer serves repo text files read-only and
jailed, every line anchored with the target highlighted. seed_db
plants the module AND the source file next to the fixture DB (the
viewer's repo root is the served DB's directory).
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-realfile-129"
NODE = "demo/realfile/add.py:add"
CID = f"{MODULE_ID}:{NODE}"
SOURCE_REL = "demo/realfile/add.py"
SOURCE_LINES = [
    "def add(a, b):",
    "    total = a + b",
    "    return total",
    "",
]
TARGET_LINE = 2

SCENARIO = {
    "id": "realfile",
    "kind": "improvement",
    "batch": 22,
    "item": "I-129",
    "title": "See it in the real file",
    "blurb": "Lesson headers link to the exact source line in a read-only viewer.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Improvement I-129",
         "title": "See it in the real file",
         "subtitle": "From lesson header to exact source line in one click."},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "js": ["() => { const a = document.getElementById('realfile'); const s = a && a.closest('section'); if (s) s.id = 'seed-lesson'; return s ? 'marked' : 'missing'; }"],
         "focus": "#seed-lesson",
         "caption": "The concept header links to its file and line.",
         "assert_js": "() => document.body.textContent.includes('see it in the real file')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 9,
         "url_path": "/file?path=demo%2Frealfile%2Fadd.py&line=2#L2",
         "caption": "The viewer lands on line 2, highlighted, every line anchored.",
         "assert_js": "() => !!document.querySelector('.file .at') && !!document.getElementById('L2')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Jailed and read-only: traversal and missing files get refusals.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import realfile as m; "
              "root = os.path.dirname(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('ok:      ', m.page_html(root, 'demo/realfile/add.py', 2)[0]); "
              "print('traverse:', m.page_html(root, '../../etc/passwd', 1)[0]); "
              "print('missing: ', m.page_html(root, 'demo/nope.py', 1)[0]); "
              "print('nolink:  ', repr(m.file_link('', 0)))"],
         ]},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Proof lives in the file.",
         "subtitle": "realfile.py links lessons to lines -- jailed, read-only, anchored."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a module plus its source file under the fixture root."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "Add",
             "kind": "function", "file": SOURCE_REL, "line": TARGET_LINE,
             "summary": "Add two numbers."},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/realfile", "Real-file module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "Add", "function",
             SOURCE_REL, TARGET_LINE, 0.0))
        con.commit()
    finally:
        con.close()
    root = os.path.dirname(os.path.abspath(db_path))
    full = os.path.join(root, *SOURCE_REL.split("/"))
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write("\n".join(SOURCE_LINES))
    return {"seeded": True, "mid": MODULE_ID, "path": SOURCE_REL,
            "line": TARGET_LINE}
