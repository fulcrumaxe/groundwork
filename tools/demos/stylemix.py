"""Feature demo: learning-style tuning (F-98).

Full behavior: when graded history shows visual material retained better
than textual, lesson sections render visual blocks (call graph, figures)
before study text; otherwise the historical text-first order stands.
seed_db plants a visual lesson aced 3 times and a textual lesson failed 3
times, so page affinity runs fully visual.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-stylemix-98"
VIS_NODE = "demo/mix.py:Resize Flow"
TXT_NODE = "demo/mix.py:Total Walk"
VIS_CID = f"{MODULE_ID}:{VIS_NODE}"
TXT_CID = f"{MODULE_ID}:{TXT_NODE}"
VIS_CARD = "demo-mix-visual"
TXT_CARD = "demo-mix-textual"
VIS_SECTION = "lesson-demo-mix-py-resize-flow"

SCENARIO = {
    "id": "stylemix",
    "kind": "feature",
    "batch": 21,
    "item": "F-98",
    "title": "Learning-style tuning",
    "blurb": "Visuals retained better? Diagrams lead. Text stronger? Words lead.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 21 - Feature F-98",
         "title": "Learning-style tuning",
         "subtitle": "Your pass rates pick the order -- visuals or words first."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b21-stylemix",
         "caption": "Status documents the affinity mix with a live sample.",
         "assert_js": "() => !!document.querySelector('#status-b21-stylemix')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: visual wins flip the section order.",
         "commands": [
             ["python3", "-c",
              "from groundwork import stylemix as m; "
              "vis = {'figure': 's.png', 'summary': 'short'}; "
              "txt = {'summary': ' '.join(['word'] * 40)}; "
              "print('kinds:', m.classify_card(vis), m.classify_card(txt)); "
              "recs = [('visual', 5)] * 3 + [('textual', 1)] * 3; "
              "aff = m.affinity(recs); "
              "print('affinity:', aff, '|', m.recommend_line(aff)); "
              "print('order:', m.order_sections(vis, aff), '| calm:', m.order_sections(vis, 0.0))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}",
         "focus": "#{seed_section}",
         "caption": "Visual affinity leads: the call graph renders before the study text.",
         "assert_js": "() => { const sec = document.querySelector('#{seed_section}'); "
                      "if (!sec) return false; const h = sec.innerHTML; "
                      "const v = h.indexOf('callgraph-wrap'); "
                      "const t = h.indexOf('<h4'); "
                      "return v > 0 && t > 0 && v < t; }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 21",
         "title": "Lead with what works.",
         "subtitle": "stylemix.py tunes the mix -- no history keeps text-first."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a visual-aced + textual-failed lesson pair in one module."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for cid in (VIS_CARD, TXT_CARD):
            con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
            con.execute("DELETE FROM cards WHERE id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": VIS_NODE, "name": "Resize Flow",
             "kind": "function", "file": "demo/mix.py", "line": 1,
             "summary": "Resize flow diagram walk.",
             "dualcode": {"steps": ["See the resize flow."]},
             "callers": ["handle_resize"], "callees": ["repaint"]},
            {"concept_id": TXT_NODE, "name": "Total Walk",
             "kind": "function", "file": "demo/mix.py", "line": 20,
             "summary": " ".join(["Totals", "accumulate", "row", "values",
                                   "into", "a", "running", "sum", "across",
                                   "the", "whole", "table", "scan", "until",
                                   "every", "row", "contributes", "its",
                                   "share", "to", "the", "final", "answer",
                                   "without", "losing", "track", "of",
                                   "partial", "state", "along", "the",
                                   "way", "today", "again", "finally",
                                   "done", "yes", "indeed", "complete"])},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/stylemix", "Style tuning module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (VIS_CID, MODULE_ID, "Resize Flow", "function",
             "demo/mix.py", 1, 0.0))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (TXT_CID, MODULE_ID, "Total Walk", "function",
             "demo/mix.py", 20, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES(?, ?, '1', ?, ?)",
            (VIS_CARD, VIS_CID, "What leads the flow?",
             "The resize diagram."))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES(?, ?, '1', ?, ?)",
            (TXT_CARD, TXT_CID, "What accumulates?",
             "The running total."))
        for _ in range(3):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, 5, 4, 'stylemix seed')", (VIS_CARD,))
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, 1, 2, 'stylemix seed')", (TXT_CARD,))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID, "section": VIS_SECTION}
    finally:
        con.close()
