"""Feature demo: growth rings (F-103).

Full behavior: History lays down one SVG ring per owned concept —
proof you can count, streak-free, capped at 30 drawn rings with an
exact overflow note. seed_db plants two owned concepts: two rings.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-rings-103"
NODES = ("demo/rings.py:one", "demo/rings.py:two")
CARD_IDS = ("demo-rings-card-1", "demo-rings-card-2")

SCENARIO = {
    "id": "growrings",
    "kind": "feature",
    "batch": 22,
    "item": "F-103",
    "title": "Growth rings",
    "blurb": "One ring per owned concept — your proof, counted in wood.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Feature F-103",
         "title": "Growth rings",
         "subtitle": "A tree counts years in wood -- History counts proof in rings."},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "focus": "#growth-rings-head",
         "caption": "Two owned concepts, two rings, the count at the center.",
         "assert_js": "() => document.querySelectorAll('#growth-rings circle').length",
         "assert_want": "2"},
        {"type": "terminal", "duration": 8,
         "caption": "Same owned rule as the headline; drawing caps at 30 rings.",
         "commands": [
             ["python3", "-c",
              "from groundwork import growrings as m; "
              "print('rings for 2:', m.ring_count(2)); "
              "print('rings for 99:', m.ring_count(99), '| cap:', m.MAX_RINGS); "
              "print('hostile:', m.ring_count('many')); "
              "svg = m.rings_svg(2, 9); "
              "print('svg circles:', svg.count('<circle'), '| says 2 of 9:', '2 of 9' in svg)"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b22-growrings",
         "caption": "Status documents the rings with a three-of-nine sample.",
         "assert_js": "() => !!document.querySelector('#status-b22-growrings')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Count the rings.",
         "subtitle": "growrings.py draws owned proof -- empty libraries get rings to earn."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant two owned concepts for two rings."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for cid in CARD_IDS:
            con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
            con.execute("DELETE FROM cards WHERE id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": node, "name": f"Ring {i + 1}",
             "kind": "function", "file": "demo/rings.py", "line": i + 1,
             "summary": f"Ring {i + 1} of the trunk."}
            for i, node in enumerate(NODES)]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/growrings", "Growth-rings module", now,
             json.dumps(lessons)))
        for i, node in enumerate(NODES):
            cid = f"{MODULE_ID}:{node}"
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, f"Ring {i + 1}", "function",
                 "demo/rings.py", i + 1, 0.0))
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type,"
                " front, back, due) VALUES(?, ?, '19', ?, ?, ?)",
                (CARD_IDS[i], cid, f"Refactor ring {i + 1}?", "Done.",
                 "2001-01-01T12:00:00Z"))
            for when in ("2026-09-01T09:00:00Z", "2026-09-08T09:00:00Z"):
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at, submission) VALUES(?, 5, 4, ?, ?)",
                    (CARD_IDS[i], when, "growrings seed"))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID, "rings": 2}
    finally:
        con.close()
