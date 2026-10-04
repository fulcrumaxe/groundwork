"""Improvement demo: answer-field autofocus (I-41).

Full behavior: the global focus_js() embed watches queue forms
with one IntersectionObserver and focuses each answer field as
it scrolls into view -- never while typing, never scrolling.
seed_db deals two due textarea cards; /due scrolls each into
view and the observer focuses its answer box (the poll types one
line into the focused field so the frame shows the effect); the
module page beat proves the second covered surface.
"""
from __future__ import annotations

import re
import sqlite3

TEXTAREA_ETYPES = ("5", "6", "24", "25", "26", "27", "28", "29", "31",
                   "32", "33", "34", "35", "37", "38", "39", "40",
                   "82", "83", "84", "85", "86", "90")


def _anchor(card_id: str) -> str:
    """Mirror scrollpos.card_anchor: the <article> id for a card."""
    slug = "".join(re.findall(r"[A-Za-z0-9_-]+", card_id.strip()))[:48]
    return "card-%s" % (slug or "unknown")

SCENARIO = {
    "id": "autofocus",
    "kind": "improvement",
    "batch": 8,
    "item": "I-41",
    "title": "Answer-field autofocus",
    "blurb": ("Cards focus their answer box as they scroll into view -- "
              "just start typing."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Improvement I-41",
         "title": "Answer-field autofocus",
         "subtitle": ("Cards focus their answer box on scroll -- typing "
                      "is never stolen.")},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-autofocus",
         "caption": ("Status homes the contract: focus on scroll into "
                     "view, never while typing, never scrolling."),
         "assert_js": "() => !!document.querySelector('#status-b8-autofocus')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The rule in one line: observe, guard typing, focus "
                     "without scrolling."),
         "commands": [
             ["python3", "-c",
              "from groundwork import autofocus as m; js = m.focus_js(); "
              "print(all(k in js for k in ('IntersectionObserver', 'preventScroll', 'activeElement'))); "
              "print(all(k not in js for k in ('sessionStorage', 'scrollIntoView', 'scrollTo')))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": ("Scroll the first card into view -- its answer box "
                     "takes focus, no click."),
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; f.scrollIntoView({behavior: 'instant', block: 'start'}); return 'scrolled'; }"],
         "poll_js": "() => { const a = document.activeElement; "
                    "const f = a && a.closest ? a.closest('form') : null; "
                    "const act = f ? f.getAttribute('action') : 'none'; "
                    "if (act === '/cards/{seed_card_id}/review' && a && !a.value) { "
                    "a.value = 'focused without a click'; a.textContent = 'focused without a click'; } "
                    "return act; }",
         "poll_want": "/cards/{seed_card_id}/review",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\") && "
                      "document.querySelector('main').innerHTML.includes('focused without a click')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "focus": "form[action='/cards/{seed_card2_id}/review']",
         "caption": ("Keep scrolling -- focus hands off to the next card's "
                     "answer box."),
         "js": ["() => { if (document.activeElement) document.activeElement.blur(); "
                "const f = document.querySelector(\"form[action='/cards/{seed_card2_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; f.scrollIntoView({behavior: 'instant', block: 'start'}); return 'scrolled'; }"],
         "poll_js": "() => { const a = document.activeElement; "
                    "const f = a && a.closest ? a.closest('form') : null; "
                    "const act = f ? f.getAttribute('action') : 'none'; "
                    "if (act === '/cards/{seed_card2_id}/review' && a && !a.value) { "
                    "a.value = 'focus hands off on scroll'; a.textContent = 'focus hands off on scroll'; } "
                    "return act; }",
         "poll_want": "/cards/{seed_card2_id}/review",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector("
                      "\"form[action='/cards/{seed_card2_id}/review']\") && "
                      "document.querySelector('main').innerHTML.includes('focus hands off on scroll')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#practice",
         "caption": ("Module practice cards carry the same script -- one "
                     "embed covers both queues."),
         "assert_js": "() => !!document.querySelector('script[data-autofocus-answer]') && "
                      "!!document.querySelector(\"main form[action^='/cards/']\")",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Just start typing.",
         "subtitle": ("autofocus.py focuses queue fields -- scrollpos and "
                      "the verdict keep their turf.")},
    ],
}


def seed_db(db_path: str) -> dict:
    """Deal two due textarea cards from one module."""
    con = sqlite3.connect(db_path)
    try:
        marks = ",".join("?" * len(TEXTAREA_ETYPES))
        rows = con.execute(
            "SELECT cards.id, concepts.module_id FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            f" WHERE cards.exercise_type IN ({marks})"
            " ORDER BY cards.due LIMIT 2", TEXTAREA_ETYPES).fetchall()
        if len(rows) < 2:
            return {"seeded": False, "reason": "need 2 textarea cards"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        ids = [rows[0][0], rows[1][0]]
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z'"
                    " WHERE id IN (?, ?)", ids)
        con.commit()
        return {"seeded": True, "card_id": ids[0], "card2_id": ids[1],
                "module_id": rows[0][1],
                "anchor": _anchor(ids[0]), "anchor2": _anchor(ids[1])}
    finally:
        con.close()
