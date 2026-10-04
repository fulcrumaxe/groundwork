"""Feature demo: serendipity cards (Batch 4, F-137).

Full functionality: Due suggests an adjacent non-due concept from
the head card's module -- a labeled bonus wander, never a duty.
seed_db leaves one module with a single due card, so the wander must
name the module's first other concept.
"""
from __future__ import annotations

import sqlite3


def _slug(text: str) -> str:
    """Mirror lessons.slug: lowercased alnum, runs of other chars to '-'."""
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in (text or ""))
    return "-".join(filter(None, out.split("-"))) or "lesson"


SCENARIO = {
    "id": "serendipity",
    "kind": "feature",
    "batch": 4,
    "item": "F-137",
    "title": "Serendipity cards",
    "blurb": "An adjacent concept you might love -- bonus, never duty.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Feature F-137",
         "title": "Serendipity cards",
         "subtitle": "An adjacent concept you might love -- bonus, never duty."},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "#serendipity",
         "caption": "Bonus, not duty: the adjacent concept sits next to your work.",
         "assert_js": "() => document.body.innerText.includes('Bonus, not duty') + '|' + "
                      "document.body.innerText.includes('{seed_concept}')",
         "assert_want": "true|true"},
        {"type": "terminal", "duration": 7,
         "caption": "The pick: first non-due concept in the head card's module.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import serendipity as s; "
              "c = s.pick(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('wander to:', c['concept']); print('module:', c['summary'][:40])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#lesson-{seed_lesson}",
         "caption": "Wandering over lands on the adjacent lesson.",
         "js": ["() => { const a = document.querySelector('#serendipity a'); "
                "if (!a) return 'wander-link-missing'; a.click(); return 'clicked'; }"],
         "poll_js": "() => location.pathname",
         "poll_want": "/modules/{seed_mid}",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { window.scrollTo(0, 0); "
                      "return location.pathname + '|' + location.hash.slice(0, 8); }",
         "assert_want": "/modules/{seed_mid}|#lesson-"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Wander if curious.",
         "subtitle": "serendipity.py picks adjacent non-due concepts."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One due card; its module's first other concept is the wander.

    The head card comes from the module's last concept, so the first
    concept (by rowid) is deterministically the adjacent pick.
    """
    con = sqlite3.connect(db_path)
    try:
        m = con.execute(
            "SELECT concepts.module_id, COUNT(DISTINCT concepts.id) FROM cards "
            "JOIN concepts ON concepts.id = cards.concept_id "
            "GROUP BY concepts.module_id HAVING COUNT(DISTINCT concepts.id) >= 2"
            " ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
        if not m:
            return {"seeded": False, "reason": "need a 2-concept module"}
        mid = m[0]
        concepts = con.execute(
            "SELECT id, name FROM concepts WHERE module_id=?"
            " ORDER BY rowid", (mid,)).fetchall()
        wander = concepts[0]
        head_concept = concepts[-1][0]
        head = con.execute(
            "SELECT id FROM cards WHERE concept_id=? ORDER BY due LIMIT 1",
            (head_concept,)).fetchone()
        if not head:
            return {"seeded": False, "reason": "head concept without cards"}
        con.execute("DELETE FROM reviews")
        con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z',"
                    " stability=1.0, retrievability=0.9, lapses=0"
                    " WHERE id=?", (head[0],))
        con.commit()
        node = wander[0].split(":", 1)[1] if ":" in wander[0] else wander[0]
        return {"seeded": True, "mid": mid, "concept": wander[1],
                "wander_cid": wander[0], "head_card": head[0],
                "lesson": _slug(node)}
    finally:
        con.close()
