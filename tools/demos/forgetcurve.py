"""Feature demo: forgetting-curve personalization (F-91).

Full behavior: recall history fits a personal decay constant k, and
the Due queue uses it twice -- minisession.apply_dial floors reviews
on the personal curve, and forgetcurve.order_due ranks most-forgotten
first. seed_db plants a fast fader (pass-then-fail on both due cards,
k=2.5): a fragile card (S=2.0) and a sturdy card (S=10.0) both a few
days overdue. Undialed, the fragile card leads; at dial 3 the personal
floor drops it while the sturdy card stays.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "forgetcurve",
    "kind": "feature",
    "batch": 20,
    "item": "F-91",
    "title": "Your forgetting curve",
    "blurb": "Reviews timed to your decay -- fast faders return sooner, slow faders later.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Feature F-91",
         "title": "Your forgetting curve",
         "subtitle": "Fast faders return sooner -- the Due queue floors and orders on your decay."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status#status-b20-forgetcurve",
         "focus": "#status-b20-forgetcurve",
         "caption": "Status documents the curve with live fast/slow fader samples.",
         "assert_js": "() => !!document.querySelector('#status-b20-forgetcurve')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The fit in one call: failing history yields k=2.5, and the fragile card fails its own floor.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "from groundwork import forgetcurve as f, minisession as m, sched as s; "
              "db = sqlite3.connect(os.environ['DEMO_DB']); "
              "ids = ['{seed_keep}', '{seed_drop}']; "
              "rows = db.execute('SELECT card_id, stability, grade, reviewed_at FROM reviews "
              "JOIN cards ON cards.id = reviews.card_id WHERE card_id IN (?, ?)', ids).fetchall(); "
              "k = f.fit_decay(f.clean_attempts(rows)); "
              "print('decay k =', k, '::', f.describe(k)); "
              "cards = [dict(r) for r in db.execute('SELECT id, stability, due FROM cards "
              "WHERE id IN (?, ?)', ids).fetchall()]; "
              "byid = {c['id']: c for c in cards}; keep, drop = byid['{seed_keep}'], byid['{seed_drop}']; "
              "print('fragile legacy R =', round(s.elapsed_retrievability(drop['stability'], drop['due']), 3), "
              "'personal R =', round(f.personal_retrievability(drop['stability'], f.overdue_days(drop), k), 3), "
              "'floor 0.70'); "
              "print('order [keep, drop] ->', [c['id'].split(':')[-1] for c in f.order_due([keep, drop], k)]); "
              "print('dial3 keeps:', [c['id'].split(':')[-1] "
              "for c in m.apply_dial([keep, drop], '3', {i: 2 for i in ids}, decay=k)])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "article.next",
         "caption": "Undialed, the queue leads most-forgotten-first -- the fragile card jumps the older-due one.",
         "assert_js": "() => { const a = document.querySelector('article.next'); "
                      "return !!a && a.innerHTML.includes('{seed_drop}'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture DB: stabilities, dues, and the pass-then-fail histories.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "[print(cid.split(':')[-1], 'S=' + str(con.execute('SELECT stability FROM cards "
              "WHERE id=?', (cid,)).fetchone()[0]), 'due=' + con.execute('SELECT due FROM cards "
              "WHERE id=?', (cid,)).fetchone()[0][:10], 'grades=' + str([r[0] for r in con.execute("
              "'SELECT grade FROM reviews WHERE card_id=? ORDER BY reviewed_at', (cid,)).fetchall()])) "
              "for cid in ('{seed_keep}', '{seed_drop}')]"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due?dial=3",
         "focus": "article.next",
         "caption": "Balanced dial floors on your curve: the fragile card drops out, the sturdy one stays.",
         "assert_js": "() => { const a = document.querySelector('article.next'); "
                      "return !!a && a.innerHTML.includes('{seed_keep}') && "
                      "!document.querySelector('form[action=\"/cards/{seed_drop}/review\"]'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Reviews timed to your decay.",
         "subtitle": "forgetcurve.py fits k from recall history -- no history keeps the standard schedule."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Two due cards plus failing histories: fragile (S=2) vs sturdy (S=10).

    Both carry pass-then-fail reviews one day apart, so fit_decay lands
    exactly on k=2.5 (fast fader). Dues sit 5.5/6.5 days back with a 12h
    cushion: the fragile card passes the legacy dial-3 floor (R~0.77)
    but fails its personal floor (R~0.55-0.59), while the sturdy card
    stays (R~0.82+). The sturdy card is due first, so the undialed flip
    to fragile-first is the order effect, not due order.
    """
    con = sqlite3.connect(db_path)
    try:
        first = con.execute(
            "SELECT id, concept_id FROM cards WHERE stale = 0"
            " ORDER BY rowid LIMIT 1").fetchone()
        if not first:
            return {"seeded": False, "reason": "no cards"}
        second = con.execute(
            "SELECT id, concept_id FROM cards WHERE stale = 0"
            " AND concept_id != ? ORDER BY rowid LIMIT 1",
            (first[1],)).fetchone()
        if not second:
            return {"seeded": False, "reason": "single concept"}
        keep_id, drop_id = first[0], second[0]
        now = datetime.now(timezone.utc)
        fmt = "%Y-%m-%dT%H:%M:%SZ"
        due_keep = (now - timedelta(days=6, hours=12)).strftime(fmt)
        due_drop = (now - timedelta(days=5, hours=12)).strftime(fmt)
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due=?, stability=10.0 WHERE id=?",
                    (due_keep, keep_id))
        con.execute("UPDATE cards SET due=?, stability=2.0 WHERE id=?",
                    (due_drop, drop_id))
        con.execute("DELETE FROM reviews WHERE card_id IN (?, ?)",
                    (keep_id, drop_id))
        old = (now - timedelta(days=2)).strftime(fmt)
        new = (now - timedelta(days=1)).strftime(fmt)
        for cid in (keep_id, drop_id):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at, submission)"
                " VALUES(?, 5, 4, ?, 'curve seed pass')", (cid, old))
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at, submission)"
                " VALUES(?, 1, 4, ?, 'curve seed fail')", (cid, new))
        con.commit()
        return {"seeded": True, "keep": keep_id, "drop": drop_id,
                "k": 2.5}
    finally:
        con.close()
