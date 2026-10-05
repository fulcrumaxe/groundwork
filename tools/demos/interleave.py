"""Feature demo: interleaving engine (F-61).

Full behavior: the Due queue ranks concept x type cells weakest-first
with no same-concept run (since Batch 14 -- empty mastery falls back
to the legacy order). seed_db parks every card but two: a weak card
(grades 1,2) and a strong card (grades 5,5) on different concepts; the
queue must lead with the weak one.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "interleave",
    "kind": "feature",
    "batch": 13,
    "item": "F-61",
    "title": "Interleaving engine",
    "blurb": "Weakest cell first, never the same idea twice running.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Feature F-61",
         "title": "Interleaving engine",
         "subtitle": "Weakest cell first, never the same idea twice running."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-interleave",
         "caption": "Status homes the engine with four sample weakest-first picks.",
         "assert_js": "() => !!document.querySelector('#status-b13-interleave')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: weakest cell wins, neighbors always contrast.",
         "commands": [
             ["python3", "-c",
              "from groundwork import interleave as m; "
              "cells = [('retry', 'predict', 0.2), ('retry', 'author', 0.8), "
              "('cache', 'predict', 0.4), ('cache', 'author', 0.6)]; "
              "picks = m.schedule(cells, 4); "
              "print('order:', [(c, t) for c, t, _ in picks]); "
              "print('interleaved:', m.is_interleaved(picks))"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/due",
         "focus": "article.next",
         "caption": "The live queue leads with the weakest concept -- mastery-ranked, contrast-kept.",
         "assert_js": "() => { const a = document.querySelector('article.next'); "
                      "return !!a && a.innerHTML.includes('{seed_weak}'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture DB: the lead card averages 1.5, the trailer 5.0.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "for cid in ('{seed_weak}', '{seed_strong}'): "
              "  g = con.execute('SELECT AVG(grade) FROM reviews WHERE card_id=?', (cid,)).fetchone()[0]; "
              "  print(cid[-12:], 'avg grade:', round(g, 1))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Contrast, not blocks.",
         "subtitle": "interleave.py orders Due -- unknown concepts rank weakest, never mastered."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Two due cards on different concepts: weak (1,2) vs strong (5,5)."""
    con = sqlite3.connect(db_path)
    try:
        first = con.execute(
            "SELECT id, concept_id FROM cards ORDER BY rowid LIMIT 1"
        ).fetchone()
        if not first:
            return {"seeded": False, "reason": "no cards"}
        second = con.execute(
            "SELECT id, concept_id FROM cards WHERE concept_id != ?"
            " ORDER BY rowid LIMIT 1", (first[1],)).fetchone()
        if not second:
            return {"seeded": False, "reason": "single concept"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute(
            "UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id IN (?, ?)",
            (first[0], second[0]))
        con.execute("DELETE FROM reviews WHERE card_id IN (?, ?)",
                    (first[0], second[0]))
        for grade in (1, 2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES(?, ?, 5)", (first[0], grade))
        for grade in (5, 5):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES(?, ?, 5)", (second[0], grade))
        con.commit()
        return {"seeded": True, "weak": first[0], "strong": second[0]}
    finally:
        con.close()
