"""Feature demo: worked support fades with practice (F-57 integration).

Full behavior: render_levels shows full steps only at zero attempts,
a Faded-recall partial stage at 1+ attempts (last step hides), and
the solo stage at 3+ (first step only). Three seeded concepts -- 0,
1, and 3 attempts -- prove each tier on one module page.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-b16-fade"
HOW = ["Read the two defaults", "Add them into total",
       "Return total to the caller"]
SOURCE = "def add(a=2, b=3):\n    total = a + b\n    return total\n"
CONCEPTS = [("fresh", 0), ("once", 1), ("often", 3)]

SCENARIO = {
    "id": "fadedrecall",
    "kind": "feature",
    "batch": 16,
    "item": "F-57",
    "title": "Support fades with practice",
    "blurb": "Full steps at zero tries, partial at one, solo at three -- the lesson fades as recall grows.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 16 - Feature F-57",
         "title": "Support fades with practice",
         "subtitle": "Full steps at zero tries, partial at one, solo at three -- the lesson fades as recall grows."},
        {"type": "terminal", "duration": 6,
         "caption": "The fade ladder in one call: full, then the last step hides, then only the first shows.",
         "commands": [
             ["python3", "-c",
              "from groundwork import fading as f; "
              "seq = f.fade_sequence(['Read the defaults', 'Add them', 'Return total']); "
              "print(*['%s | shown: %d | hidden: %d' % (s['stage'], len(s['shown']), len(s['hidden'])) for s in seq], sep=chr(10)); "
              "print('0 tries -> full only; 1+ -> partial; 3+ -> solo')"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#lesson-{seed_once_slug} #fading",
         "caption": "One attempt in: the last step hides -- partial recall, still scaffolded.",
         "js": ["() => { const d = document.querySelector('#lesson-{seed_once_slug} #fading details'); "
               "if (!d) return 'missing'; d.open = true; return 'opened'; }"],
         "assert_js": "() => !!document.querySelector('.fade-partial') && !document.querySelector('.fade-solo')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#lesson-{seed_often_slug} #fading",
         "caption": "Three attempts in: only the first step shows -- solo recall.",
         "js": ["() => { const d = document.querySelector('#lesson-{seed_often_slug} #fading details'); "
               "if (!d) return 'missing'; d.open = true; return 'opened'; }"],
         "assert_js": "() => !!document.querySelector('.fade-solo')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 6,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#lesson-{seed_fresh_slug} .dual-pack",
         "caption": "Zero attempts: full steps only -- no faded section until practice starts.",
         "assert_js": "() => !!document.querySelector('.dual-pack') && !document.querySelector('#fading')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 16",
         "title": "Recall grows, support shrinks.",
         "subtitle": "Faded recall tiers ride the learner's real attempt count."},
    ],
}


def _slug(text: str) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Plant three concepts with 0, 1, and 3 attempts on one module."""
    con = sqlite3.connect(db_path)
    try:
        nodes = [f"demo/fade.py:{name}" for name, _ in CONCEPTS]
        cids = [f"{MODULE_ID}:{n}" for n in nodes]
        for cid in cids:
            con.execute("DELETE FROM reviews WHERE card_id LIKE ?",
                        (f"card-b16-fade-%",))
            con.execute("DELETE FROM cards WHERE concept_id=?", (cid,))
            con.execute("DELETE FROM concepts WHERE id=?", (cid,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": node, "name": name, "kind": "function",
             "file": "demo/fade.py", "line": 1,
             "summary": f"{name}() totals two numbers via its defaults.",
             "docstring": "Add a and b.", "callers": [], "callees": [],
             "key_lines": "", "source": SOURCE, "complexity": 1,
             "how": list(HOW), "worked": None,
             "dualcode": {"steps": list(HOW), "states": []}}
            for node, (name, _n) in zip(nodes, CONCEPTS)
        ]
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/b16", "Faded-recall lesson module", now,
             json.dumps(lessons)))
        for (name, tries), node, cid in zip(CONCEPTS, nodes, cids):
            con.execute(
                "INSERT INTO concepts(id, module_id, name, kind, file,"
                " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
                (cid, MODULE_ID, name, "function", "demo/fade.py", 1, 0.0))
            card_id = f"card-b16-fade-{name}"
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
                " VALUES(?, ?, '1', ?, ?)",
                (card_id, cid, f"What does {name} do?", "probe back"))
            for _ in range(tries):
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at) VALUES(?, 5, 3, ?)",
                    (card_id, now))
        con.commit()
        slugs = [_slug(n) for n in nodes]
        return {"seeded": True, "module_id": MODULE_ID,
                "fresh_slug": slugs[0], "once_slug": slugs[1],
                "often_slug": slugs[2]}
    finally:
        con.close()
