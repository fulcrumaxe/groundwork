"""Feature demo: collectible concept badges (F-113).

Full behavior: each owned concept earns its own emblem — motif
plus hue derived from sha256(name), stable across renders — with
no rarity tiers by design. Unowned concepts render the plain chip
byte-identical. seed_db plants a module with one owned concept.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-conceptbadges-113"
NODE = "demo/badge.py:earned"
CID = f"{MODULE_ID}:{NODE}"
CARD_ID = f"{MODULE_ID}:ex001"


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


SCENARIO = {
    "id": "conceptbadges",
    "kind": "feature",
    "batch": 23,
    "item": "F-113",
    "title": "Collectible concept badges",
    "blurb": "Each owned concept earns its own deterministic art badge -- equal badges, no rarity.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 23 - Feature F-113",
         "title": "Collectible concept badges",
         "subtitle": "Own a concept, earn its emblem -- stable, equal, yours."},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules/{seed_mid}",
         "focus": "#lesson-{seed_slug} h2",
         "caption": "The owned concept's heading wears its emblem; unowned chips stay plain.",
         "assert_js": "() => !!document.querySelector('.cbadge')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Motif plus hue from the name hash -- same name, same badge, every render.",
         "commands": [
             ["python3", "-c",
              "from groundwork import conceptbadges as m; "
              "a = m.badge_for('loops'); b = m.badge_for('loops'); "
              "print('stable:', a == b, a); "
              "print('unowned:', repr(m.badge_html('loops', False)))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b23-conceptbadges",
         "caption": "Status shows a live sample badge beside the no-rarity promise.",
         "assert_js": "() => !!document.querySelector("
                      "'#status-b23-conceptbadges') "
                      "&& !!document.querySelector('.cbadge')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 23",
         "title": "Proof, collected.",
         "subtitle": "conceptbadges.py hashes names to emblems -- every badge equal."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a module with one owned concept for its emblem."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM cards WHERE concept_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "earned",
             "kind": "function", "file": "demo/badge.py", "line": 1,
             "summary": "earned is owned, so it wears its emblem.",
             "docstring": "Badge material.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def earned():\n    return badge()\n",
             "complexity": 1,
             "how": ["Own the concept.", "Wear the emblem."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Concept-badge module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "earned", "function",
             "demo/badge.py", 1, 0.9))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, due)"
            " VALUES(?, ?, '27', ?)", (CARD_ID, CID, now))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
                " submission) VALUES(?, 5, 4, ?, 'conceptbadges seed')",
                (CARD_ID, now))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID, "slug": _slug(NODE)}
    finally:
        con.close()
