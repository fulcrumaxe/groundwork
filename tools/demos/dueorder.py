"""Feature demo: Due queue orders by mastery (F-61 integration).

Full behavior: tool_list_due_reviews builds per-cell mastery and
bridges it through interleave.order_due (Batch 14) -- the weakest
concept leads the live queue, and blank mastery falls back to the
legacy sched.interleave order byte-identical. seed_db parks every
card but two: a weak card (grades 1,2) and a strong card (grades
5,5) on different concepts; the queue must lead with the weak one.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "dueorder",
    "kind": "feature",
    "batch": 14,
    "item": "F-61",
    "title": "Due queue orders by mastery",
    "blurb": "Weakest concept leads via the order_due bridge -- blank mastery keeps legacy order.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 14 - Feature F-61",
         "title": "Due queue orders by mastery",
         "subtitle": "Weakest concept leads via the order_due bridge -- blank mastery keeps legacy order."},
        {"type": "terminal", "duration": 7,
         "caption": "The bridge in one call: list_due_reviews leads weakest-first.",
         "commands": [
             ["bash", "-lc",
              "echo '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"list_due_reviews\",\"params\":{\"limit\":5}}'"
              " | python3 -m groundwork --db \"$DEMO_DB\" mcp 2>/dev/null"
              " | python3 -c \"import json,sys,sqlite3,os; d=json.load(sys.stdin);"
              " due=d['result']['due'];"
              " con=sqlite3.connect(os.environ['DEMO_DB']);"
              " print('due:', len(due));"
              " [print(('lead ' if i==0 else 'next ') + c['id'][-14:] + ' '"
              " + c['concept_id'].split(':')[-1]"
              " + ' avg ' + str(round(con.execute('select avg(grade) from reviews"
              " where card_id=?', (c['id'],)).fetchone()[0] or 0, 1)))"
              " for i, c in enumerate(due)];"
              " print('weakest leads:', bool(due) and due[0]['id']=='{seed_weak}')\""],
         ]},
        {"type": "terminal", "duration": 5,
         "caption": "Blank mastery falls back to the legacy interleave, byte-identical.",
         "commands": [
             ["python3", "-c",
              "from groundwork import interleave as m, sched as s; "
              "cards = [{'id': 1, 'concept_id': 'cA', 'exercise_type': 1}, "
              "        {'id': 2, 'concept_id': 'cA', 'exercise_type': 1}, "
              "        {'id': 3, 'concept_id': 'cB', 'exercise_type': 1}]; "
              "print('engaged:', [c['id'] for c in m.order_due(cards, {('cA', 1): 5.0, ('cB', 1): 1.0})]); "
              "print('blank falls back:', [c['id'] for c in m.order_due(cards, {})] "
              "== [c['id'] for c in s.interleave(cards)])"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/due",
         "focus": "article.next",
         "caption": "The live queue leads with the weakest concept -- the bridge, not the demo.",
         "assert_js": "() => { const a = document.querySelector('article.next'); "
                      "return !!a && a.innerHTML.includes('{seed_weak}'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture DB: the lead card averages 1.5, the trailer 5.0.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "[print(cid[-12:], 'avg grade:', round(con.execute('SELECT AVG(grade) FROM reviews"
              " WHERE card_id=?', (cid,)).fetchone()[0], 1)) "
              "for cid in ('{seed_weak}', '{seed_strong}')]"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 14",
         "title": "Weakest first, for real.",
         "subtitle": "order_due() bridges mastery into the Due queue -- blank mastery keeps legacy order."},
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
