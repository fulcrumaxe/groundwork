"""Improvement demo: next-gap forecast (Batch 3, I-203).

Full functionality: each Due card estimates its next gap at steady
passes from its stability (sched.forecast_gap, rendered by
cards.forecast_html). seed_db parks the queue to exactly two cards --
a strong memory (12.6d -> ~13d) and a faint one (2.0d -> ~2d) -- so
both forecasts film with real contrast.
"""
from __future__ import annotations

import re
import sqlite3

_ANCHOR_OK = re.compile(r"[A-Za-z0-9_-]+")


def _slug(text: str) -> str:
    """Mirror scrollpos.card_anchor: keep [A-Za-z0-9_-], cap at 48."""
    return "".join(_ANCHOR_OK.findall((text or "").strip()))[:48] or "unknown"


SCENARIO = {
    "id": "due-forecast",
    "kind": "improvement",
    "batch": 3,
    "item": "I-203",
    "title": "Next-gap forecast",
    "blurb": "Each Due card estimates its next gap at steady passes.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 3 - Improvement I-203",
         "title": "Next-gap forecast",
         "subtitle": "Each Due card estimates its next gap at steady passes."},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#forecast",
         "caption": "Each Due card forecasts its next gap at steady passes.",
         "assert_js": "() => { const f = document.querySelector('#forecast'); "
                      "return f ? f.textContent : 'missing'; }",
         "assert_want": "{seed_gap1}"},
        {"type": "terminal", "duration": 7,
         "caption": "One pure function: round stability to days, minimum one.",
         "commands": [
             ["python3", "-c",
              "from groundwork import sched as s; "
              "print('12.6d ->', s.forecast_gap(12.6)); "
              "print('2.0d ->', s.forecast_gap(2.0)); "
              "print('0.2d ->', s.forecast_gap(0.2))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_a2}",
         "caption": "A faint memory forecasts a short gap -- pass steadily to stretch it.",
         "assert_js": "() => { const a = document.querySelector('#card-{seed_a2}'); "
                      "return a ? a.textContent : 'missing'; }",
         "assert_want": "{seed_gap2}"},
        {"type": "terminal", "duration": 6,
         "caption": "The seeded stabilities behind the two forecasts.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute(\"SELECT id, stability FROM cards WHERE id IN ('{seed_c1}', '{seed_c2}') ORDER BY due\").fetchall(); "
              "print([(r[0][:8], r[1]) for r in rows])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 3",
         "title": "Pass steadily, return later.",
         "subtitle": "sched.forecast_gap mirrors the scheduler's own interval."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Two due cards, distinct concepts: 12.5d vs 2.0d stability.

    Everything else parks in 2999 and reviews wipe, so the queue holds
    exactly these two (no probes: probes need reviews, and both seeds
    stay well under the 7.0 stability probe floor anyway).
    """
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id, concept_id FROM cards ORDER BY due LIMIT 50").fetchall()
        picks = []
        seen = set()
        for cid, concept in cards:
            if concept not in seen:
                seen.add(concept)
                picks.append(cid)
            if len(picks) == 2:
                break
        if len(picks) < 2:
            return {"seeded": False, "reason": "need 2 concepts"}
        c1, c2 = picks
        con.execute("DELETE FROM reviews")
        con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z',"
                    " stability=12.6, retrievability=0.9, lapses=0"
                    " WHERE id=?", (c1,))
        con.execute("UPDATE cards SET due='2000-01-02T00:00:00Z',"
                    " stability=2.0, retrievability=0.3, lapses=0"
                    " WHERE id=?", (c2,))
        con.commit()
        return {"seeded": True, "c1": c1, "c2": c2,
                "a1": _slug(c1), "a2": _slug(c2),
                "gap1": "\u224813d", "gap2": "\u22482d"}
    finally:
        con.close()
