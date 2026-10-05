"""Feature demo: self-explanation prompts (F-58).

Full behavior: every worked step of the seeded lesson carries a
"why does this line exist?" disclosure on its module page; the
terminal shows the rotating templates behind them.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-selfexplain-58"
NODE = "demo/why.py:explain"
CONCEPT_ID = f"{MODULE_ID}:{NODE}"
HOW = [
    "Open the queue before reading any card.",
    "Grade the answer before seeing the verdict.",
    "Read the verdict line before continuing.",
]

SCENARIO = {
    "id": "selfexplain",
    "kind": "feature",
    "batch": 12,
    "item": "F-58",
    "title": "Self-explanation prompts",
    "blurb": "Every worked step asks why it exists -- explain it in your own words.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Feature F-58",
         "title": "Self-explanation prompts",
         "subtitle": "Every worked step asks why it exists."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b12-selfexplain",
         "caption": "Status homes the nudges: one rotating why per step, never graded.",
         "assert_js": "() => { const el = document.querySelector("
                      "\"#status-b12-selfexplain\"); return !!el && "
                      "document.body.innerText.includes('selfexplain_prompts'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: templates rotate, blanks skip, garbage rests.",
         "commands": [
             ["python3", "-c",
              "from groundwork import selfexplain as m; "
              "ps = m.selfexplain_prompts(['a', 'b', 'c', 'd']); "
              "print('prompts:', len(ps)); "
              "print('0:', ps[0]['prompt']); "
              "print('3:', ps[3]['prompt']); "
              "print('blank skipped:', m.selfexplain_prompts(['ok', ' ']))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": "#selfexplain",
         "caption": "Explain it back: each step asks why, in your own words.",
         "js": ["() => { document.querySelectorAll('#selfexplain details')"
                ".forEach(d => { d.open = true; }); return 'opened'; }"],
         "assert_js": "() => { const el = document.querySelector("
                      "'#selfexplain'); return !!el && "
                      "el.innerText.includes('Step 1') && "
                      "el.innerText.includes('your own words'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Say the why.",
         "subtitle": "selfexplain.py nudges each line -- retrieval, not grades."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a lesson with three worked steps (no attempts needed)."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM cards WHERE concept_id=?", (CONCEPT_ID,))
        con.execute("DELETE FROM concepts WHERE id=?", (CONCEPT_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lesson = {"concept_id": NODE, "name": "Explain back",
                  "kind": "function", "file": "demo/why.py", "line": 1,
                  "summary": "Ask why after every worked step.",
                  "docstring": "Explain back, self-explanation edition.",
                  "how": HOW}
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "demo/why", "Self-explain module", now,
             json.dumps([lesson])))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CONCEPT_ID, MODULE_ID, "Explain back", "function",
             "demo/why.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "module_id": MODULE_ID}
    finally:
        con.close()
