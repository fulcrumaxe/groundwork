"""Improvement demo: keyboard shortcuts cheat sheet (Batch 3, I-40).

Full functionality: ? toggles the shortcut overlay on any page, g
then d jumps to Due, and keystrokes typed into answer fields never
fire shortcuts. seed_db forces one textarea card due so the typing
beat has a real answer box to stand down in.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "shortcuts-cheatsheet",
    "kind": "improvement",
    "batch": 3,
    "item": "I-40",
    "title": "Keyboard shortcuts",
    "blurb": "g then d jumps to Due, ? opens the cheat sheet -- typing never hijacked.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 3 - Improvement I-40",
         "title": "Keyboard shortcuts",
         "subtitle": "g then d jumps to Due, ? opens the cheat sheet -- typing never hijacked."},
        {"type": "chrome", "duration": 10,
         "url_path": "/",
         "caption": "Press ? on any page and the cheat sheet pops open.",
         "js": ["() => { document.body.dispatchEvent(new KeyboardEvent('keydown', {key: '?', bubbles: true, cancelable: true})); return 'key-sent'; }"],
         "assert_js": "() => (!document.querySelector('#shortcuts').hidden) + '|' + document.body.innerText.includes('g then d')",
         "assert_want": "true|true"},
        {"type": "chrome", "duration": 12,
         "url_path": "/",
         "caption": "g then d jumps straight to the Due queue -- the mouse stays parked.",
         "js": ["() => { const b = document.body; "
                "b.dispatchEvent(new KeyboardEvent('keydown', {key: 'g', bubbles: true})); "
                "b.dispatchEvent(new KeyboardEvent('keydown', {key: 'd', bubbles: true})); "
                "return 'seq-sent'; }"],
         "poll_js": "() => location.href",
         "poll_want": "/due",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => location.pathname",
         "assert_want": "/due"},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "caption": "Typed 'g d ?' sits harmlessly in the answer box -- no jump, no sheet.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; "
                "ta.textContent = 'g d ?'; ta.value = 'g d ?'; "
                "ta.dispatchEvent(new KeyboardEvent('keydown', {key: 'g', bubbles: true})); "
                "ta.dispatchEvent(new KeyboardEvent('keydown', {key: 'd', bubbles: true})); "
                "ta.dispatchEvent(new KeyboardEvent('keydown', {key: '?', bubbles: true})); "
                "return 'keys-sent'; }"],
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "assert_js": "() => (!!document.querySelector(\"form[action='/cards/{seed_card_id}/review'] textarea[name=answer]\")) + '|' + location.href.includes('/due') + '|' + document.getElementById('shortcuts').hidden",
         "assert_want": "true|true|true"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 3",
         "title": "Hands stay home.",
         "subtitle": "shortcuts.py: two-key jumps plus ? -- fields always win."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One textarea card due-now so the typing beat has an answer box.

    Prefers textarea exercise types (the shortcuts handler only
    stands down inside real fields); the beat targets this card's
    form by exact action URL and dispatches g, d, ? keydowns into
    its textarea, proving no navigation and no overlay.
    """
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id FROM cards WHERE exercise_type IN "
            "('5','6','24','25','82','83','84','85','86','90')"
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
