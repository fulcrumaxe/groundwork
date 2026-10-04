"""Feature demo: workload forecast graph (Batch 3, I-204).

Full functionality: History renders reviews-due-per-day for the next
30 days with a peak count, bucketed from stored due timestamps --
no simulation. seed_db pushes every other card out of the horizon
and spreads 60+ cards across the next 31 days (noon UTC cushion),
with an 8-card pile-up on day 3 so the peak reads on screen.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

SCENARIO = {
    "id": "workload-graph",
    "kind": "feature",
    "batch": 3,
    "item": "I-204",
    "title": "Workload forecast",
    "blurb": "Reviews due per day for the next 30 days -- see busy days coming.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 3 - Feature I-204",
         "title": "Workload forecast",
         "subtitle": "Reviews due per day for the next 30 days -- see busy days coming."},
        {"type": "terminal", "duration": 7,
         "caption": "Pure logic: bucket stored due dates -- the peak day pops out.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import workload as m; "
              "rows = m.buckets(os.environ['DEMO_DB']); "
              "print('next 7 days:'); "
              "[print(' ', d, n) for d, n in rows[:7]]; "
              "pk = max(rows, key=lambda r: r[1]); "
              "print('peak:', pk[1], 'on', pk[0])"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/reviews",
         "focus": "#workload",
         "caption": "History carries the 30-day graph -- {seed_peak} reviews pile onto {seed_peak_day}.",
         "assert_js": "() => (!!document.querySelector('#workload')) + '|' + document.body.innerText.includes('(peak {seed_peak})')",
         "assert_want": "true|true"},
        {"type": "terminal", "duration": 7,
         "caption": "The manipulated fixture: every coming day carries due reviews.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute(\"SELECT substr(due,1,10) AS d, COUNT(*) AS n FROM cards WHERE stale = 0 GROUP BY d ORDER BY d LIMIT 8\").fetchall(); "
              "[print(d, n) for d, n in rows]"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 3",
         "title": "Busy days, seen coming.",
         "subtitle": "workload.py buckets the due dates History already stores."},
    ],
}


PEAK_DAY = 3
PEAK_COUNT = 8


def seed_db(db_path: str) -> dict:
    """Spread cards across the next 31 days with an 8-card peak on day 3.

    Every other non-stale card is pushed 60 days out so the buckets
    hold only seeded counts (deterministic peak). Noon-UTC due times
    cushion against midnight-boundary bucket slips; 31 seeded days
    keep all 30 displayed buckets nonzero even if filming crosses
    midnight UTC between seed and request.
    """
    con = sqlite3.connect(db_path)
    try:
        cards = con.execute(
            "SELECT id FROM cards WHERE stale = 0").fetchall()
        if not cards:
            return {"seeded": False, "reason": "no cards"}
        today = datetime.now(timezone.utc).date()
        far = (today + timedelta(days=60)).strftime("%Y-%m-%dT12:00:00Z")
        con.execute("UPDATE cards SET due=? WHERE stale = 0", (far,))
        need = 0
        plan = {}
        for d in range(31):
            n = PEAK_COUNT if d == PEAK_DAY else 1 + (d % 3)
            plan[d] = n
            need += n
        if len(cards) < need:
            return {"seeded": False, "reason": "too few cards"}
        idx = 0
        peak_day = ""
        for d in range(31):
            day = (today + timedelta(days=d)).strftime("%Y-%m-%d")
            if d == PEAK_DAY:
                peak_day = day
            due = day + "T12:00:00Z"
            for _ in range(plan[d]):
                con.execute("UPDATE cards SET due=? WHERE id=?",
                            (due, cards[idx][0]))
                idx += 1
        con.commit()
        return {"seeded": True, "peak": PEAK_COUNT,
                "peak_day": peak_day, "spread": 31}
    finally:
        con.close()
