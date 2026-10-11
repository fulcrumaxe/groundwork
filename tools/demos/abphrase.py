"""Improvement demo: A/B explainer phrasings kept by recall (I-136).

Full behavior: half the concepts explain ELI5-first (variant A) and
half tradeoffs-first (variant B) on the lesson rendering path, by
concept-id hash with no storage; delayed recall (second-and-later
reviews) scores the winner. seed_db plants one A and one B lesson
with passing vs failing recalls.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-ab-136"
NODE_A = "demo/ab.py:alpha"
NODE_B = "demo/ab.py:beta"
CARD_A = "demo-ab-card-a"
CARD_B = "demo-ab-card-b"


def _variant(cid: str) -> str:
    """Mirror of abphrase.variant_for (stdlib-only seed replica)."""
    text = str(cid or "").strip()
    if not text:
        return "A"
    digest = hashlib.md5(text.encode("utf-8")).hexdigest()
    return "B" if int(digest, 16) % 2 else "A"


SCENARIO = {
    "id": "abphrase",
    "kind": "improvement",
    "batch": 22,
    "item": "I-136",
    "title": "A/B explainer phrasings",
    "blurb": "Half lead simple-first, half tradeoffs-first — recall keeps the winner.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 22 - Improvement I-136",
         "title": "A/B explainer phrasings",
         "subtitle": "Two orders, one hash -- delayed recall picks the winner."},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}",
         "js": ["() => { const s = [...document.querySelectorAll(\"section[id^='lesson-']\")].find(x => { const h = x.querySelector('h2'); return h && h.textContent.trim().startsWith('Beta'); }); if (s) s.id = 'seed-beta'; return s ? 'marked' : 'missing'; }"],
         "focus": "#seed-beta",
         "caption": "Beta (variant B) leads tradeoffs-first; Alpha keeps ELI5-first.",
         "assert_js": "() => (document.querySelector('#seed-beta .extremes-tradeoffs').compareDocumentPosition(document.querySelector('#seed-beta .extremes-eli5')) & 4) ? 'T-first' : 'E-first'",
         "assert_want": "{seed_beta_first}"},
        {"type": "terminal", "duration": 10,
         "caption": "Delayed recall scores it live: study reviews never count.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import abphrase as m; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "print('alpha:', m.variant_for('{seed_cid_a}'), '| beta:', m.variant_for('{seed_cid_b}')); "
              "rep = m.variant_report(db); "
              "print('A:', rep['A']); print('B:', rep['B']); "
              "print('winner:', rep['winner'], '| total recalls:', rep['total'])"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b22-abphrase",
         "caption": "Status documents the hash assignment with a live sample.",
         "assert_js": "() => !!document.querySelector('#status-b22-abphrase')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 22",
         "title": "Recall keeps the winner.",
         "subtitle": "abphrase.py assigns by hash, scores by delayed pass rate."},
    ],
}


def _lesson(node, name):
    return {
        "concept_id": node, "name": name, "kind": "function",
        "file": "demo/ab.py", "line": 1,
        "summary": f"{name} adds with a carry.",
        "eli5": {"analogy": f"{name} is a piggy bank that only takes twos.",
                 "takeaway": "Defaults do the adding."},
        "tradeoffs": ["Inline the sum", "Use a running total"],
    }


def seed_db(db_path: str) -> dict:
    """Plant A/B lessons; A recalls pass, B recalls fail."""
    cid_a = f"{MODULE_ID}:{NODE_A}"
    cid_b = f"{MODULE_ID}:{NODE_B}"
    # Ensure the two nodes land on opposite variants; nudge if not.
    node_a, node_b = NODE_A, NODE_B
    for salt in range(50):
        cid_a = f"{MODULE_ID}:{node_a}"
        cid_b = f"{MODULE_ID}:{node_b}"
        if _variant(cid_a) != _variant(cid_b):
            break
        node_b = f"{NODE_B}-{salt}"
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        for cid in (CARD_A, CARD_B):
            con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
            con.execute("DELETE FROM cards WHERE id=?", (cid,))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/abphrase", "A/B phrasing module", now,
             json.dumps([_lesson(node_a, "Alpha"),
                         _lesson(node_b, "Beta")])))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid_a, MODULE_ID, "Alpha", "function", "demo/ab.py", 1, 0.0))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (cid_b, MODULE_ID, "Beta", "function", "demo/ab.py", 5, 0.0))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '1', ?, ?, ?)",
            (CARD_A, cid_a, "Alpha?", "A.",
             "2001-01-01T12:00:00Z"))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, due)"
            " VALUES(?, ?, '1', ?, ?, ?)",
            (CARD_B, cid_b, "Beta?", "B.",
             "2001-01-01T12:00:00Z"))
        # Study first, then two recalls each; the A variant passes.
        sched = [("2026-01-01T09:00:00Z", 3), ("2026-02-01T09:00:00Z", None),
                 ("2026-03-01T09:00:00Z", None)]
        for card, cid in ((CARD_A, cid_a), (CARD_B, cid_b)):
            recall_grade = 5 if _variant(cid) == "A" else 2
            for when, grade in sched:
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at, submission) VALUES(?, ?, ?, ?, ?)",
                    (card, grade if grade else recall_grade, 3, when,
                     "abphrase seed"))
        con.commit()
        rows = con.execute(
            "SELECT id FROM concepts WHERE module_id=? ORDER BY rowid",
            (MODULE_ID,)).fetchall()
        order = "".join("E" if _variant(r[0]) == "A" else "T" for r in rows)
        winner = "A"
        beta_first = "T-first" if _variant(cid_b) == "B" else "E-first"
        return {"seeded": True, "mid": MODULE_ID, "cid_a": cid_a,
                "cid_b": cid_b, "order": order, "winner": winner,
                "beta_first": beta_first}
    finally:
        con.close()
