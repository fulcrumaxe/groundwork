"""Feature demo: milestone share-cards (F-108).

Full behavior: each achieved milestone offers an opt-in PNG download
— a flat card encoded with stdlib zlib/struct and a hand-authored 3x5
bitmap font, embedded as a data URI so nothing leaves the page until
the learner clicks. seed_db plants the First Owned milestone.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-share-108"
NODE = "demo/share.py:first"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = "demo-share-card"

SCENARIO = {
    "id": "sharecards",
    "kind": "feature",
    "batch": 22,
    "item": "F-108",
    "title": "Milestone share-cards",
    "blurb": "Your proof as a PNG — private until you download, yours to post.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Feature F-108",
         "title": "Milestone share-cards",
         "subtitle": "Exportable proof -- opt-in, offline, no Pillow."},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "focus": "#share-cards",
         "caption": "The milestone offers its card as a private-until-clicked download.",
         "assert_js": "() => !!document.querySelector(\"a[download$='.png']\")",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "A real PNG from stdlib bytes: magic header, bitmap-font words.",
         "commands": [
             ["python3", "-c",
              "from groundwork import sharecards as m; "
              "raw = m.card_for('first-owned', 'FIRST OWNED', '2026-03-04'); "
              "print('magic:', raw[:8]); print('bytes:', len(raw)); "
              "print('size:', m.CARD_W, 'x', m.CARD_H); "
              "print('glyphs:', len(m.FONT), '| data-uri:', m.card_data_uri('k', 'L', 'd')[:22])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b22-sharecards",
         "caption": "Status shows a live sample card rendered the same way.",
         "assert_js": "() => !!document.querySelector('#status-b22-sharecards') && !!document.querySelector('img[alt*=\"share card\"]')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Yours to post.",
         "subtitle": "sharecards.py encodes milestones -- private until you say so."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the two passing reviews behind the First Owned card."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "First",
             "kind": "function", "file": "demo/share.py", "line": 1,
             "summary": "The first owned concept."},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/sharecards", "Share-cards module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "First", "function",
             "demo/share.py", 1, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '19', ?, ?, ?)",
            (CARD_ID, CID, "Refactor this first?", "Done.",
             "2001-01-01T12:00:00Z"))
        for when in ("2026-03-01T09:00:00Z", "2026-03-04T09:00:00Z"):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " submission) VALUES(?, 5, 4, ?, 'sharecards seed')",
                (CARD_ID, when))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
