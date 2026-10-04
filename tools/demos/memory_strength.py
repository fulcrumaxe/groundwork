"""Improvement demo: memory-strength bars (Batch 2, I-76).

Full functionality: each Due card shows its FSRS memory strength in
days as a labeled bar, filled by retrievability. seed_db clears the
queue to exactly two cards -- a strong memory (12.5d at 90%) and a
faint one (2.0d at 30%) -- so both bars film with real contrast.
"""
from __future__ import annotations

import re
import sqlite3

_ANCHOR_OK = re.compile(r"[A-Za-z0-9_-]+")


def _slug(text: str) -> str:
    """Mirror scrollpos.card_anchor: keep [A-Za-z0-9_-], cap at 48."""
    return "".join(_ANCHOR_OK.findall((text or "").strip()))[:48] or "unknown"

SCENARIO = {
    "id": "memory-strength",
    "kind": "improvement",
    "batch": 2,
    "item": "I-76",
    "title": "Memory-strength bars",
    "blurb": "Each Due card shows its FSRS memory strength in days, as a bar.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 2 - Improvement I-76",
         "title": "Memory-strength bars",
         "subtitle": "Each Due card shows its FSRS memory strength in days, as a bar."},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#memory",
         "caption": "Each Due card carries its memory strength in days, as a labeled bar.",
         "assert_js": "() => { const m = document.querySelector('#memory'); "
                      "return m ? m.textContent + ' / ' + !!m.querySelector('span.bar') : 'missing'; }",
         "assert_want": "Memory strength"},
        {"type": "terminal", "duration": 7,
         "caption": "Stability in days drives the label; retrievability fills the bar.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; from groundwork import cards as c; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute(\"SELECT id, stability, retrievability FROM cards WHERE id IN ('{seed_c1}', '{seed_c2}')\").fetchall(); "
              "[print(r[0][:8], '->', c._memory_bar({'stability': r[1], 'retrievability': r[2]})) for r in rows]"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_a1}",
         "caption": "A strong memory: 12.5 days at 90% retrievability.",
         "assert_js": "() => { const a = document.querySelector('#card-{seed_a1}'); "
                      "return a ? a.textContent : 'missing'; }",
         "assert_want": "12.5d"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_a2}",
         "caption": "A faint memory: 2.0 days at 30% -- review it first.",
         "assert_js": "() => { const a = document.querySelector('#card-{seed_a2}'); "
                      "return a ? a.textContent : 'missing'; }",
         "assert_want": "2.0d"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 2",
         "title": "Strength you can see.",
         "subtitle": "cards.py renders stability days plus a retrievability bar."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Two due cards, distinct concepts: strong (12.5d/90%) vs faint (2.0d/30%).

    Everything else parks in 2999 and reviews wipe, so the queue holds
    exactly these two (no probes: probes need owned concepts, which
    need reviews). Distinct concepts keep both bars on screen.
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
                    " stability=12.5, retrievability=0.9, lapses=0"
                    " WHERE id=?", (c1,))
        con.execute("UPDATE cards SET due='2000-01-02T00:00:00Z',"
                    " stability=2.0, retrievability=0.3, lapses=0"
                    " WHERE id=?", (c2,))
        con.commit()
        return {"seeded": True, "c1": c1, "c2": c2,
                "a1": _slug(c1), "a2": _slug(c2)}
    finally:
        con.close()
