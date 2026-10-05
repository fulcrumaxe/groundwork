"""Improvement demo: library-shelf Modules theme (I-72).

Full behavior: every module card on the Modules index grows a left
spine bar plus a subtle cover-style elevation, so the index reads as
a shelf of books. Pure CSS via the head wire; no DB or schema change.
seed_db plants one module with a concept and card so the shelf has a
deterministic top card; the /modules beat proves the theme with
computed styles, not just markup.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-shelf-72"
CONCEPT_ID = "demo-shelf-72-concept"
CARD_ID = "demo-shelf-72-card"
REPO = "shelf-demo/repo"
SUMMARY = "Shelf demo module"

SCENARIO = {
    "id": "shelf",
    "kind": "improvement",
    "batch": 12,
    "item": "I-72",
    "title": "Library shelf",
    "blurb": "Module cards stand like books on a shelf -- spine bar, cover lift.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Improvement I-72",
         "title": "Library shelf",
         "subtitle": "Module cards stand like books -- spine bar, cover lift, motion gate."},
        {"type": "chrome", "duration": 5,
         "url_path": "/status",
         "focus": "#status-b12-shelf",
         "caption": "Status documents the shelf with its real card selectors.",
         "assert_js": "() => { const el = document.querySelector('#status-b12-shelf'); "
                      "return !!el && el.textContent.includes('Library'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: spine matches the cover palette, gate included.",
         "commands": [
             ["python3", "-c",
              "from groundwork import cover as c, shelf as m; "
              "print('spine==cover:', m.shelf_spine('groundwork') == c.cover_color('groundwork')); "
              "print('decl:', m.spine_decl('shelf-demo/repo')); "
              "css = m.shelf_css(); "
              "print('bar+lift+gate:', '--shelf-spine' in css and 'transition:none' in css.replace(' ',''))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules",
         "focus": ".modcard",
         "caption": "The Modules shelf: seeded module on top, every card with a spine bar.",
         "assert_js": "() => { const card = document.querySelector('.modcard'); "
                      "if (!card) return false; "
                      "const spine = getComputedStyle(card).borderLeftWidth === '6px'; "
                      "const lift = getComputedStyle(card).boxShadow !== 'none'; "
                      "const seeded = document.body.innerText.includes('{seed_summary}'); "
                      "return spine && lift && seeded; }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture DB: the seeded module heads the shelf.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "row = con.execute(\"SELECT task_summary, repo FROM modules WHERE id='"
              + MODULE_ID + "'\").fetchone(); "
              "n = con.execute(\"SELECT COUNT(*) FROM cards JOIN concepts ON concepts.id=cards.concept_id"
              " WHERE concepts.module_id='" + MODULE_ID + "'\").fetchone()[0]; "
              "print('seeded module:', row, '| cards:', n)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Take one down.",
         "subtitle": "shelf.py shelves the modules -- spine, shadow, reduced-motion gate."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one module (concept + card) as the newest card on the shelf.

    Borrows an exercise type from an existing card; created_at=now
    sorts it first under the newest-first default. The beat targets
    its summary text and the computed spine on .modcard.
    """
    con = sqlite3.connect(db_path)
    try:
        src = con.execute(
            "SELECT exercise_type FROM cards ORDER BY rowid LIMIT 1").fetchone()
        if not src:
            return {"seeded": False, "reason": "no cards"}
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute("DELETE FROM concepts WHERE id=?", (CONCEPT_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at)"
            " VALUES(?, ?, ?, ?)",
            (MODULE_ID, REPO, SUMMARY, now))
        con.execute(
            "INSERT INTO concepts(id, module_id, name) VALUES(?, ?, ?)",
            (CONCEPT_ID, MODULE_ID, "Shelf spine"))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES(?, ?, ?, ?, ?)",
            (CARD_ID, CONCEPT_ID, src[0],
             "What does the shelf theme add to module cards?",
             "A spine bar and cover-style lift."))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID,
                "summary": SUMMARY, "repo": REPO}
    finally:
        con.close()
