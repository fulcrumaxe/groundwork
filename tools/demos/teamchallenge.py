"""Feature demo: aggregate-only team challenges (F-129).

Full behavior: each repo is one fixed local challenge ("own <repo>
together") computed from existing owned/mastery data -- aggregate
counts only, no members, no ranking. The served library already
holds modules with concepts, so no fixture planting is needed; the
terminal beat reads the live aggregates from the fixture DB.
"""
from __future__ import annotations

SCENARIO = {
    "id": "teamchallenge",
    "kind": "feature",
    "batch": 25,
    "item": "F-129",
    "title": "Team challenges",
    "blurb": "Own each subsystem together -- aggregate only, no ranking.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Feature F-129",
         "title": "Team challenges",
         "subtitle": "One challenge per repo -- progress, never ranking."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-teamchallenge",
         "caption": "Status names the rule: per-repo counts, no members.",
         "assert_js": "() => !!document.querySelector('#status-b25-teamchallenge') "
                      "&& document.body.innerText.includes('no ranking')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Zero-total is 0, never div-zero; rows come from the DB.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import teamchallenge as m; "
              "print('pct:', m.progress(2, 8), '| empty:', m.progress(0, 0)); "
              "rows = m.challenges(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('repos:', len(rows)); "
              "print('first:', rows[0]['subsystem'], rows[0]['owned'], '/', rows[0]['total'])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "focus": "#teamchallenge",
         "caption": "History lists every subsystem: owned, total, attempts.",
         "assert_js": "() => !!document.querySelector('#teamchallenge') "
                      "&& document.body.innerText.includes('owned')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Together, unranked.",
         "subtitle": "teamchallenge.py reads owned maps -- no new tables."},
    ],
}
