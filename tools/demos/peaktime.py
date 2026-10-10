"""Feature demo: optimal review time (F-92).

Full behavior: past grades bucketed into four dayparts banner the
winning window on the Due queue; histories under three reviews
omit the banner. seed_db plants five evening passes plus one
morning fail; a mid-run terminal beat trims the history below
threshold and the closing Due beat proves the omission live.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "peaktime",
    "kind": "feature",
    "batch": 20,
    "item": "F-92",
    "title": "Best time to review",
    "blurb": "Your past grades reveal when your recall peaks -- review then for more passes.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Feature F-92",
         "title": "Best time to review",
         "subtitle": "Evening passes beat morning fails -- the Due queue banners the peak."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-peaktime",
         "caption": "Status documents the dayparts with a live evening sample.",
         "assert_js": "() => !!document.querySelector('#status-b20-peaktime') && "
                      "document.body.innerText.includes('Peak recall: evening')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Pure verdict: evening wins on pass rate; two reviews name no peak.",
         "commands": [
             ["python3", "-c",
              "from groundwork import peaktime as m; "
              "rows = [(5, '2020-01-05T19:00:00Z')] * 5 + [(1, '2020-01-06T08:00:00Z')]; "
              "print(m.describe(rows)); "
              "print(m.describe(rows[:2])); "
              "print('banner omits:', repr(m.banner_html(rows[:2]))[:30])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "#peaktime",
         "caption": "The Due queue banners the peak: evening -- review then for more passes.",
         "assert_js": "() => { const b = document.querySelector('#peaktime'); "
                      "return !!b && b.innerText.includes('evening'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Trim the history to two reviews mid-run -- the server re-reads every request.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ['DEMO_DB']); "
              "con.execute('DELETE FROM reviews WHERE rowid NOT IN "
              "(SELECT rowid FROM reviews ORDER BY rowid LIMIT 2)'); "
              "con.commit(); "
              "print('reviews left:', con.execute('SELECT COUNT(*) FROM reviews').fetchone()[0])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "Below threshold the banner vanishes -- Due renders exactly as before.",
         "assert_js": "() => !document.querySelector('#peaktime') && !!document.querySelector('main')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Review at your peak.",
         "subtitle": "peaktime.py buckets four dayparts -- thin histories stay quiet."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Five evening passes + one morning fail; one card due."""
    con = sqlite3.connect(db_path)
    try:
        card = con.execute("SELECT id FROM cards ORDER BY rowid LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        con.execute("DELETE FROM reviews")
        for day in range(1, 6):
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " reviewed_at, submission) VALUES(?, 5, 4, ?, 'peak seed')",
                        (card[0], f"2020-02-{day:02d}T19:15:00Z"))
        con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at, submission) VALUES(?, 1, 2, ?, 'peak seed')",
                    (card[0], "2020-02-06T08:15:00Z"))
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (card[0],))
        con.commit()
        return {"seeded": True, "card_id": card[0]}
    finally:
        con.close()
