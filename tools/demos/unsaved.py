"""Improvement demo: unsaved-answer guard (I-29).

Full behavior: start typing an answer and wander off and the browser
asks first -- a beforeunload guard fires only when a card textarea
holds unsent text and the form was never submitted, so real submits
and clean navigation are never blocked. The interaction beat proves
the matrix live: dirty warns, clean stays quiet.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "unsaved",
    "kind": "improvement",
    "batch": 7,
    "item": "I-29",
    "title": "Unsaved-answer guard",
    "blurb": "Start typing an answer and wander off and the browser asks first.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Improvement I-29",
         "title": "Unsaved-answer guard",
         "subtitle": "Half-typed answers survive wandering -- clean pages stay silent."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-unsaved",
         "caption": "Status documents the improvement: beforeunload only on unsent text.",
         "assert_js": "() => !!document.querySelector('#status-b7-unsaved')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: non-space text is dirty -- blanks and nothing are not.",
         "commands": [
             ["python3", "-c",
              "from groundwork import unsaved as m; "
              "print(m.is_dirty('half-typed answer'), m.is_dirty('   '), m.is_dirty(None))"],
         ]},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "Type, and the guard arms -- clear it, and navigation stays silent.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; "
                "ta.value = 'half-typed answer'; "
                "var e1 = new Event('beforeunload', {cancelable: true}); "
                "window.dispatchEvent(e1); var armed = e1.defaultPrevented; "
                "ta.value = ''; "
                "var e2 = new Event('beforeunload', {cancelable: true}); "
                "window.dispatchEvent(e2); var clean = e2.defaultPrevented; "
                "ta.value = 'half-typed answer'; "
                "ta.textContent = 'half-typed answer'; "
                "document.title = 'armed=' + armed + ' clean=' + clean; "
                "return document.title; }"],
         "assert_js": "() => document.title === 'armed=true clean=false'",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "Wander safely.",
         "subtitle": "unsaved.py uses the submitted-flag pattern -- real submits never block."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Force one textarea-type card due-first for the guard beat to type in."""
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id FROM cards WHERE exercise_type IN "
            "('5','6','24','25','82','83','84','85','86','90','26','27','28',"
            "'29','31','32','33','34','35','37','38','39','40')"
            " ORDER BY due LIMIT 1").fetchone()
        if not card:
            card = con.execute(
                "SELECT id FROM cards ORDER BY due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid = card[0]
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (cid,))
        con.commit()
        return {"seeded": True, "card_id": cid}
    finally:
        con.close()
