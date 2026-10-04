"""Feature demo: grade disputes (Batch 3, I-193).

Full functionality: a learner flags a wrong reference from the Due
card's one-click dispute box (disputes.dispute_form_html); the POST
lands on a filed confirmation, and the Status triage queue shows the
dispute with accept/reject actions (disputes.queue_html). seed_db
clears the queue to exactly one card and wipes disputes, so the
Status beat must show the dispute this video just filed.
"""
from __future__ import annotations

import re
import sqlite3

_ANCHOR_OK = re.compile(r"[A-Za-z0-9_-]+")


def _slug(text: str) -> str:
    """Mirror scrollpos.card_anchor: keep [A-Za-z0-9_-], cap at 48."""
    return "".join(_ANCHOR_OK.findall((text or "").strip()))[:48] or "unknown"


SCENARIO = {
    "id": "grade-disputes",
    "kind": "feature",
    "batch": 3,
    "item": "I-193",
    "title": "Grade disputes",
    "blurb": "Flag a wrong reference with one click; maintainers triage the queue.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 3 - Feature I-193",
         "title": "Grade disputes",
         "subtitle": "Flag a wrong reference with one click; maintainers triage the queue."},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/dispute']\"); "
                "if (!f) return 'dispute-form-missing'; "
                "const d = f.closest('details'); d.id = 'seed-dispute'; d.open = true; "
                "return 'dispute-ready'; }"],
         "focus": "#seed-dispute",
         "caption": "Every Due card carries a one-click dispute box under its answer area.",
         "assert_js": "() => !!document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/dispute']\")",
         "assert_want": "True"},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "caption": "One click files the dispute -- the confirmation points at the Status queue.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/dispute']\"); "
                "if (!f) return 'dispute-form-missing'; "
                "const inp = f.querySelector('input[name=reason]'); "
                "if (!inp) return 'no-reason'; inp.value = '{seed_reason}'; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "filed",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('filed') && "
                      "document.body.innerText.includes('Status page')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/status",
         "focus": "#status-disputes",
         "caption": "The Status queue shows the filed dispute with accept/reject actions.",
         "assert_js": "() => document.body.innerText.includes('{seed_reason}') && "
                      "!!document.querySelector(\"form[action*='/resolve']\")",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof in the fixture DB: one open dispute with the filed reason.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute('SELECT id, card_id, reason, status FROM disputes').fetchall(); "
              "print(rows); "
              "print('open:', con.execute(\"SELECT COUNT(*) FROM disputes WHERE status='open'\").fetchone()[0])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 3",
         "title": "Wrong references get fixed.",
         "subtitle": "disputes.py files from any card; the Status queue triages."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One due card, zero disputes: the queue beat shows this film's filing.

    Wiping reviews also suppresses probe cards, so the Due page holds
    exactly the seed card and the dispute form targets it by exact
    action URL.
    """
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT cards.id, concepts.name FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " ORDER BY cards.due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid = card[0]
        con.execute("DELETE FROM reviews")
        con.execute("DELETE FROM disputes")
        con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z'"
                    " WHERE id=?", (cid,))
        con.commit()
        return {"seeded": True, "card_id": cid, "a": _slug(cid),
                "concept": card[1],
                "reason": "SeedRef42 reference swaps Paris and Lyon"}
    finally:
        con.close()
