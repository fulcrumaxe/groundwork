"""Feature demo: every submit banks signed points (F-65 integration).

Full behavior: submit_review banks score(pass, conf) into
reviews.points beside the pass/fail grade -- grades stay pass/fail,
points ride along. The verdict shows the banked line and History
totals the bank. seed_db forces two rubric cards due; the terminal
beat submits one wrong at confidence 5 through MCPServer (-5), the
/due beat answers the other wrong at confidence 5, and History must
total the pre-existing bank minus 10.
"""
from __future__ import annotations

import json
import sqlite3

WRONG_ANSWER = "xylophone zebra quasar xyzzy"


def _rubric_cards(con, need: int) -> list:
    """First `need` type-5/6 card ids with a non-empty rubric."""
    out = []
    rows = con.execute(
        "SELECT id, payload FROM cards WHERE exercise_type IN ('5','6')"
        " ORDER BY rowid").fetchall()
    for cid, payload in rows:
        try:
            rub = [r for r in json.loads(payload or "{}").get(
                "rubric", []) if r]
        except ValueError:
            continue
        if rub:
            out.append(cid)
        if len(out) >= need:
            break
    return out


SCENARIO = {
    "id": "bankpoints",
    "kind": "feature",
    "batch": 15,
    "item": "F-65",
    "title": "Every submit banks",
    "blurb": "submit_review banks signed points beside the grade -- verdict shows it, History totals it.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 15 - Feature F-65",
         "title": "Every submit banks",
         "subtitle": "submit_review banks signed points beside the grade -- verdict shows it, History totals it."},
        {"type": "terminal", "duration": 8,
         "caption": "The seam in one call: submit_review returns grade and points side by side.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork.mcp import MCPServer; "
              "s = MCPServer(os.environ['DEMO_DB']); "
              "out = s.submit_review('{seed_card_a}', '"
              + WRONG_ANSWER + "', 5); "
              "print('pass:', out['result'].get('pass'), "
              "'| grade:', out['grade'], '| points:', out['points']); "
              "print('drill:', out['drill']); "
              "import sqlite3; con = sqlite3.connect(os.environ['DEMO_DB']); "
              "print('row:', con.execute(\"SELECT grade, points FROM reviews"
              " WHERE card_id='{seed_card_a}' ORDER BY id DESC LIMIT 1\").fetchone())"],
         ]},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Wrong at confidence 5 on Due -- the verdict banks -5 on the spot.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_b}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = '" + WRONG_ANSWER + "'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='5']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Calibration banked",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('Calibration banked -5 pts')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 6,
         "url_path": "/reviews",
         "focus": "#calibration",
         "caption": "History totals the bank: two bluffs paid, summed beside accuracy.",
         "assert_js": "() => { const c = document.querySelector('#calibration'); "
                      "return !!c && c.textContent.includes('bank {seed_bank_total} pts'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture DB: two fail grades, two -5 rows, one bank.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute(\"SELECT card_id, grade, points FROM reviews"
              " WHERE card_id IN ('{seed_card_a}', '{seed_card_b}')"
              " ORDER BY id DESC LIMIT 2\").fetchall(); "
              "[print(r[0][-12:], 'grade:', r[1], 'points:', r[2]) for r in rows]; "
              "print('bank:', con.execute('SELECT COALESCE(SUM(points),0) FROM reviews').fetchone()[0])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 15",
         "title": "Grades judge, points pay.",
         "subtitle": "One calibration currency -- banked every submit, totaled on History."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Two rubric cards due-now; bank total after two -5 submits."""
    con = sqlite3.connect(db_path)
    try:
        ids = _rubric_cards(con, 2)
        if len(ids) < 2:
            return {"seeded": False, "reason": "fewer than 2 rubric cards"}
        pre = con.execute(
            "SELECT COALESCE(SUM(points), 0) FROM reviews").fetchone()[0]
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z'"
                    " WHERE id IN (?, ?)", ids)
        con.commit()
        return {"seeded": True, "card_a": ids[0], "card_b": ids[1],
                "bank_total": "%+d" % (int(pre or 0) - 10)}
    finally:
        con.close()
