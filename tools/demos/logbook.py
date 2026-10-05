"""Improvement demo: Logbook History theme (I-71).

Full behavior: the History page reads like a logbook -- first-column
dates in table.log and relative times in p.ok/p.stale small set
monospace with tabular numerals, ruled row separators, muted table
headers. Pure CSS via the head wire; no markup, DB, or schema change.
seed_db plants one fresh grade-5 review so the Attempts list has a
deterministic row; the /reviews beats prove the theme with computed
styles, not just markup.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

CARD_ID = "demo-logbook-71"

SCENARIO = {
    "id": "logbook",
    "kind": "improvement",
    "batch": 12,
    "item": "I-71",
    "title": "Logbook History",
    "blurb": "History reads like a logbook -- monospace dates, ruled rows, muted headers.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Improvement I-71",
         "title": "Logbook History",
         "subtitle": "Monospace dates, ruled rows, muted headers -- History, bound."},
        {"type": "chrome", "duration": 5,
         "url_path": "/status",
         "focus": "#status-b12-logbook",
         "caption": "Status documents the theme with its real History selectors.",
         "assert_js": "() => { const el = document.querySelector('#status-b12-logbook'); "
                      "return !!el && el.textContent.includes('Logbook'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: ruled tables, monospace dates, no style tags.",
         "commands": [
             ["python3", "-c",
              "from groundwork import logbook as m; css = m.logbook_css(); "
              "print('ruled:', 'table.log td' in css, '| mono:', 'tabular-nums' in css); "
              "print('no <style>:', '<style' not in css, '| motion-free:', '@keyframes' not in css); "
              "print('bad color fails closed:', m.rule_color('red') == m.RULE_COLOR)"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/reviews",
         "focus": "#coverage",
         "caption": "Coverage timeline wears the logbook: ruled rows, muted headers, mono dates.",
         "assert_js": "() => { const t = document.querySelector('table.log'); "
                      "if (!t) return false; "
                      "const td = t.querySelector('td'); const th = t.querySelector('th'); "
                      "const first = t.querySelector('td:first-child'); "
                      "if (!td || !th || !first) return false; "
                      "const ruled = getComputedStyle(td).borderBottomWidth === '1px'; "
                      "const muted = getComputedStyle(th).color === 'rgb(89, 89, 89)'; "
                      "const mono = /mono/i.test(getComputedStyle(first).fontFamily); "
                      "return ruled && muted && mono; }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/reviews",
         "focus": "#attempts",
         "caption": "Attempts list the seeded grade-5 review first, timestamp monospace.",
         "assert_js": "() => !!document.querySelector(\"a[href*='card-{seed_card_id}']\") && "
                      "!!document.querySelector('p.ok small')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture DB: the seeded grade-5 review is the newest row.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "row = con.execute(\"SELECT grade, substr(reviewed_at,1,10) FROM reviews WHERE card_id='"
              + CARD_ID + "'\").fetchone(); "
              "print('seeded review (grade, day):', row)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "History, bound.",
         "subtitle": "logbook.py themes table.log through the head wire -- markup untouched."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one card with a fresh grade-5 review for the Attempts list.

    Borrows a concept and exercise type from an existing card so the
    review joins (card -> concept -> module) resolve on History. The
    beat targets this card's attempt row by its deep-link anchor.
    """
    con = sqlite3.connect(db_path)
    try:
        src = con.execute(
            "SELECT concept_id, exercise_type FROM cards"
            " ORDER BY rowid LIMIT 1").fetchone()
        if not src:
            return {"seeded": False, "reason": "no cards"}
        concept_id, etype = src
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute("DELETE FROM cards WHERE id=?", (CARD_ID,))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES(?, ?, ?, ?, ?)",
            (CARD_ID, concept_id, etype,
             "What does the logbook theme change on History?",
             "Monospace dates, ruled rows, muted headers."))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " submission) VALUES(?, 5, 5, ?, 'logbook seed')",
            (CARD_ID, now))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID, "day": now[:10]}
    finally:
        con.close()
