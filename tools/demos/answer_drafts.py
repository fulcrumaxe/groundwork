"""Batch 1 improvement demo: answer drafts survive reload.

Full functionality: every keystroke in a Due answer box is saved to
localStorage under a per-form key and restored on reload; submitting
clears the key. seed_db forces one textarea card due-first; the /due
interaction beat types a probe into the seeded form, dispatches input
exactly like a real keystroke, and the assert reads the draft key back
-- proving persistence without a reload round-trip through the
beforeunload unsaved guard (reload survival was verified by hand in a
live browser during authoring).
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "answer-drafts",
    "kind": "improvement",
    "batch": 1,
    "item": "I-152",
    "title": "Answer drafts",
    "blurb": "Type an answer, reload the page \u2014 your text survives. Cleared on submit.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Improvement answer-drafts",
         "title": "Answer drafts",
         "subtitle": "Type an answer, reload, your text survives -- cleared on submit."},
        {"type": "chrome", "duration": 7,
         "url_path": "/due",
         "focus": "article.next",
         "caption": "The lead card's answer box is draft-guarded: every keystroke saves locally.",
         "assert_js": "() => document.body.innerHTML.includes('gw-draft')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "The key scheme: one localStorage key per answer form action.",
         "commands": [
             ["bash", "-lc", "grep -n \"gw-draft\" groundwork/web.py"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "Typed text lands in localStorage under the form's own key -- no submit yet.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = '{seed_probe}'; "
                "ta.textContent = '{seed_probe}'; "
                "ta.dispatchEvent(new Event('input', {bubbles: true})); "
                "return localStorage.getItem('gw-draft:/cards/{seed_card_id}/review') || 'none'; }"],
         "assert_js": "() => localStorage.getItem('gw-draft:/cards/{seed_card_id}/review') || 'none'",
         "assert_want": "{seed_probe}"},
        {"type": "terminal", "duration": 6,
         "caption": "And submitting clears the key -- drafts never haunt the next review.",
         "commands": [
             ["bash", "-lc", "grep -n \"removeItem\" groundwork/web.py"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Reload-proof answers.",
         "subtitle": "web.py GLOBAL_JS saves drafts per form, clears on submit."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One textarea card due-first so its answer form takes typed drafts.

    Prefers textarea exercise types so the beat can type a probe into
    a real field; the beat targets this card's answer form (the FIRST
    form with its action URL -- the template emits the answer form
    before the give-up form) and dispatches a bubbling input event,
    which is exactly what the draft script listens for. The textContent
    mirror keeps the probe visible after the pipeline reframes <main>
    from outerHTML (live .value would not serialize).
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
        return {"seeded": True, "card_id": cid, "probe": "draft-probe-xyz"}
    finally:
        con.close()
