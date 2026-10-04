"""Improvement demo: Ctrl+Enter to submit (Batch 1).

Full functionality: one global keydown handler (web.py GLOBAL_JS)
submits the enclosing form when Ctrl/Cmd+Enter fires inside a textarea
or text input. seed_db forces a textarea card due-first; the beat types
an answer and dispatches a real synthetic Ctrl+Enter keydown, which
takes the handler's native-submit path to the full verdict page.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "ctrl-enter",
    "kind": "improvement",
    "batch": 1,
    "item": "I-155",
    "title": "Ctrl+Enter to submit",
    "blurb": "Submit from any text field with Ctrl/Cmd+Enter. Try it in the box below.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Improvement ctrl-enter",
         "title": "Ctrl+Enter to submit",
         "subtitle": "Submit from any text field with Ctrl/Cmd+Enter."},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The lead card waits in its answer box; the mouse can stay parked.",
         "assert_js": "() => !!document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review'] textarea[name=answer]\") "
                      "&& document.documentElement.innerHTML.includes('ctrlKey')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "The binding in source: Ctrl or Cmd plus Enter submits the form.",
         "commands": [
             ["bash", "-lc",
              "grep -n 'Ctrl/Cmd+Enter\\|ctrlKey' groundwork/web.py"],
         ]},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "caption": "A real Ctrl+Enter keystroke submits the answer, no click.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; "
                "ta.value = 'Explained from the keyboard.'; "
                "ta.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', ctrlKey: true, bubbles: true, cancelable: true})); "
                "return 'key-sent'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Next review:",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('Next review:')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof in the fixture: the keyboard-typed answer just landed.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print(con.execute(\"SELECT submission, confidence FROM reviews WHERE card_id='{seed_card_id}'"
              " ORDER BY rowid DESC LIMIT 1\").fetchone())"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Hands stay home.",
         "subtitle": "One binding, every text field, no mouse."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One textarea card due-first so the binding has a box to fire in.

    Prefers textarea exercise types (the GLOBAL_JS handler only fires
    from TEXTAREA and text INPUT targets); the beat targets this card's
    form by exact action URL and dispatches a real Ctrl+Enter
    KeyboardEvent, which the page handler turns into a native submit.
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
