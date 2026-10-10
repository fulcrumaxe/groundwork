"""Feature demo: reading-group mode (F-89).

Full functionality: one shared lesson carries three deterministic
discussion prompts (recall, connect, challenge), a locally synced
presence roster, and minute-share plan rows. Handler.module_html
passes presence None, so solo module visits render byte-identical
legacy HTML; with live presence the same path appends the
<section id='readgroup'> block (roster + prompts + plan). The Status
page carries a live presence sample under status-b20-readgroup.
seed_db selects a real module id (read-only); the module beat films
the real caller path proving the None fallback keeps legacy bytes.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "readgroup",
    "kind": "feature",
    "batch": 20,
    "item": "F-89",
    "title": "Reading-group mode",
    "blurb": "Study one module together: shared lesson, discussion prompts, local presence sync.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Feature F-89",
         "title": "Reading-group mode",
         "subtitle": "One lesson, three prompts, a live roster -- solo visits render exactly as before."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-readgroup",
         "caption": "Status documents the feature with a live presence sample.",
         "assert_js": "() => !!document.querySelector('#status-b20-readgroup')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Pure logic: three deterministic prompts, minute shares, last-writer-wins merge.",
         "commands": [
             ["python3", "-c",
              "from groundwork import readgroup as m; "
              "les = {'name': 'add', 'summary': 'Totals two numbers.', 'how': ['Read the defaults.']}; "
              "[print('-', p) for p in m.discussion_prompts(les)]; "
              "print(m.session_plan([('add', 1), ('loops', 3)])); "
              "print(m.presence_merge({'ann': {'done': 1, 'at': '2020-01-01'}}, {'ann': {'done': 2, 'at': '2020-01-02'}}))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}",
         "caption": "Solo visit on the real module path: presence is None, so no section -- legacy bytes.",
         "assert_js": "() => !document.querySelector('#readgroup') && !!document.querySelector('main')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/status#status-b20-readgroup",
         "focus": "#readgroup",
         "caption": "With live presence the same section appears: roster, prompts, and plan.",
         "assert_js": "() => document.querySelector('#readgroup').innerText.includes('ann')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Byte proof: None renders empty; live presence renders roster plus plan.",
         "commands": [
             ["python3", "-c",
              "from groundwork import readgroup as m; "
              "les = {'n': {'name': 'add', 'summary': 'Totals two numbers.', 'how': ['Read the defaults.']}}; "
              "print('presence None:', repr(m.session_html(les, None))); "
              "live = m.session_html(les, {'ann': {'done': 1, 'at': '2020-01-01'}, 'bob': {'done': 0, 'at': '2020-01-01'}}, {'n': 4}); "
              "print('live:', 'ann' in live and 'bob' in live and '4 min' in live and \"id='readgroup'\" in live)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Study together, render solo.",
         "subtitle": "readgroup.py appends the section only when presence is live -- sync stays out of scope."},
    ],
}


def seed_db(db_path: str) -> dict:
    """A real module id with concepts (read-only select).

    The module beat films Handler.module_html for this id and
    asserts the None fallback (no #readgroup section); no fixture
    rows change, so the served library DB is untouched.
    """
    con = sqlite3.connect(db_path)
    try:
        modules = con.execute(
            "SELECT id FROM modules ORDER BY rowid DESC").fetchall()
        for (mid,) in modules:
            row = con.execute(
                "SELECT id FROM concepts WHERE module_id=? ORDER BY rowid LIMIT 1",
                (mid,)).fetchone()
            if row:
                return {"seeded": True, "mid": mid}
        return {"seeded": False, "reason": "no concepts"}
    finally:
        con.close()
