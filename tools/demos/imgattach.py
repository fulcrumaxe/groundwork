"""Improvement demo: concept-note images (I-130).

Full behavior: lessons with image attachments (an attachments list, or
![alt](src) refs in concept notes) render lazy figures on the module page;
lessons without images render nothing extra. seed_db plants one lesson with
a real embedded PNG attachment plus a caption.
"""
from __future__ import annotations

import base64
import json
import sqlite3
import struct
import zlib
from datetime import datetime, timezone

MODULE_ID = "demo-imgattach-130"
NODE = "demo/shot.py:resize"
CONCEPT_ID = f"{MODULE_ID}:{NODE}"


def _png_block(w: int = 200, h: int = 60,
               rgb: tuple = (31, 111, 92)) -> str:
    """Solid-color PNG as a data: URI (fits the 500-char src cap)."""
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    comp = zlib.compress(raw, 9)

    def chunk(typ: bytes, data: bytes) -> bytes:
        head = struct.pack(">I", len(data)) + typ + data
        return head + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    return "data:image/png;base64," + base64.b64encode(png).decode()


SCENARIO = {
    "id": "imgattach",
    "kind": "improvement",
    "batch": 21,
    "item": "I-130",
    "title": "Concept-note images",
    "blurb": "Attached photos and diagrams render as lazy figures on the lesson.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Improvement I-130",
         "title": "Concept-note images",
         "subtitle": "Sketches and screenshots ride along -- lazy, captioned, escaped."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-imgattach",
         "caption": "Status documents the attachments with a live sample figure.",
         "assert_js": "() => !!document.querySelector('#status-b21-imgattach')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: safe srcs attach; hostile ones vanish.",
         "commands": [
             ["python3", "-c",
              "from groundwork import imgattach as m; "
              "les = {'attachments': [{'src': 'shots/board.png', 'alt': 'whiteboard', "
              "'caption': 'Study sketch'}], "
              "'why_note': 'see ![desk](shots/desk.jpg)'}; "
              "print('found:', len(m.attachments_in(les))); "
              "print('evil src:', repr(m.clean_attachment({'src': 'javascript:alert(1)'}))); "
              "fig = m.figures_html({'attachments': [{'src': 'a.png', 'alt': '<b>'}]}); "
              "print('escape:', fig[fig.index('alt='):fig.index('alt=') + 18])"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}",
         "focus": ".concept-shots",
         "caption": "The lesson renders its attached photo with a caption.",
         "assert_js": "() => { const i = document.querySelector('.concept-shot img'); "
                      "return !!i && i.alt.includes('whiteboard'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Show, don't just tell.",
         "subtitle": "imgattach.py renders figures -- imageless lessons stay quiet."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a module whose lesson carries one embedded PNG attachment."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM concepts WHERE id=?", (CONCEPT_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lesson = {"concept_id": NODE, "name": "resize", "kind": "function",
                  "file": "demo/shot.py", "line": 1,
                  "summary": "A resize lesson with a study sketch attached.",
                  "attachments": [{"src": _png_block(), "alt": "whiteboard",
                                   "caption": "Study sketch: resize flow"}]}
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/imgattach", "Image attachment module", now,
             json.dumps([lesson])))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CONCEPT_ID, MODULE_ID, "resize", "function",
             "demo/shot.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
