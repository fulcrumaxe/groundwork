"""Improvement demo: lesson audio summaries (I-141).

Full behavior: every lesson with study text grows a Listen button
that reads a spoken summary (the lesson's own summary plus its
first how-step, capped at 60 words) via speechSynthesis — no
stored audio, no network, a second click stops. seed_db plants a
module whose lesson has a summary and how-steps.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

MODULE_ID = "demo-audiosum-141"
NODE = "demo/speak.py:summarize"
CID = f"{MODULE_ID}:{NODE}"

SCENARIO = {
    "id": "audiosum",
    "kind": "improvement",
    "batch": 23,
    "item": "I-141",
    "title": "Audio summaries",
    "blurb": "Lessons grow a Listen button -- the summary, spoken offline.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 23 - Improvement I-141",
         "title": "Audio summaries",
         "subtitle": "A Listen button per lesson -- spoken offline, nothing stored."},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules/{seed_mid}",
         "focus": ".audiosum",
         "caption": "Each lesson with study text grows a Listen button plus its transcript.",
         "js": ["() => { const b = document.querySelector('.audiosum-listen'); "
                "if (!b) return 'button-missing'; b.click(); return 'clicked'; }"],
         "assert_js": "() => document.body.innerText.includes('Listen to summary')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "Spoken text: the lesson's own summary plus its first step, capped at 60 words.",
         "commands": [
             ["python3", "-c",
              "from groundwork import audiosum as m; "
              "les = {'summary': 'Render the answer form for one card.', "
              "'how': ['Pick the widget by exercise type.', 'Wire the submit.']}; "
              "t = m.summary_text(les); "
              "print(len(t.split()), 'words:', t); "
              "print('empty lesson:', repr(m.summary_text({})))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b23-audiosum",
         "caption": "Status documents the guarantee: no summary, no JS, or no speech means no change.",
         "assert_js": "() => !!document.querySelector('#status-b23-audiosum')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 23",
         "title": "Sixty words, spoken.",
         "subtitle": "audiosum.py speaks via speechSynthesis -- no audio files, no network."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant a module whose one lesson has a summary plus how-steps."""
    con = sqlite3.connect(db_path)
    try:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        con.execute("DELETE FROM reviews WHERE card_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM cards WHERE concept_id LIKE ?",
                    (MODULE_ID + ":%",))
        con.execute("DELETE FROM concepts WHERE module_id=?", (MODULE_ID,))
        con.execute("DELETE FROM modules WHERE id=?", (MODULE_ID,))
        lessons = [
            {"concept_id": NODE, "name": "summarize",
             "kind": "function", "file": "demo/speak.py", "line": 1,
             "summary": "summarize builds the sixty-word spoken script "
                        "from a lesson's own summary plus its first how-step.",
             "docstring": "Spoken summaries, offline.",
             "callers": [], "callees": [], "key_lines": "",
             "source": "def summarize(lesson):\n    return ' '.join(words)\n",
             "complexity": 1,
             "how": ["Take the lesson summary first.",
                     "Append the first how-step.",
                     "Cap the whole script at sixty words."]},
        ]
        con.execute(
            "INSERT INTO modules(id, repo, task_summary, created_at, lessons)"
            " VALUES(?, ?, ?, ?, ?)",
            (MODULE_ID, "", "Spoken-summary module", now,
             json.dumps(lessons)))
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file,"
            " line, mastery) VALUES(?, ?, ?, ?, ?, ?, ?)",
            (CID, MODULE_ID, "summarize", "function",
             "demo/speak.py", 1, 0.0))
        con.commit()
        return {"seeded": True, "mid": MODULE_ID}
    finally:
        con.close()
