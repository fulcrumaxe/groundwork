"""Feature demo: tool-call analytics (Batch 4, F-389).

Full functionality: every MCP dispatch is logged with ok/ms, and
Status aggregates per-tool calls, failure share, and mean latency.
seed_db logs five annotate calls (one failed) plus two creates, so
the table must show the exact failure share and mean.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "tool-analytics",
    "kind": "feature",
    "batch": 4,
    "item": "F-389",
    "title": "Tool-call analytics",
    "blurb": "Which MCP tools fire, with failure rates and latency.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Feature F-389",
         "title": "Tool-call analytics",
         "subtitle": "Which MCP tools fire, with failure rates and latency."},
        {"type": "terminal", "duration": 7,
         "caption": "The log: five annotates at mixed latency, one failed.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute('SELECT method, COUNT(*), SUM(ok = 0), AVG(ms) FROM tool_calls GROUP BY method ORDER BY 2 DESC').fetchall(); "
              "[print('%s: %d calls, %d failed, %.1f ms mean' % r) for r in rows]"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/status",
         "focus": "#status-tools",
         "caption": "Status aggregates per tool: calls, failure share, mean latency.",
         "assert_js": "() => { const h = document.querySelector('#status-tools'); "
                      "let n = h ? h.nextElementSibling : null; "
                      "let t = ''; "
                      "while (n && !/^H[23]$/.test(n.tagName)) { t += n.innerText + ' '; n = n.nextElementSibling; } "
                      "return t.includes('annotate_decision') + '|' + t.includes('20%') + '|' + t.includes('14.0 ms'); }",
         "assert_want": "true|true|true"},
        {"type": "terminal", "duration": 6,
         "caption": "Five calls, one failure: the 20% the table shows.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "n, bad = con.execute(\"SELECT COUNT(*), SUM(ok = 0) FROM tool_calls WHERE method = 'annotate_decision'\").fetchone(); "
              "print(f'{n} calls, {bad} failed -> {100 * bad / n:.0f}%')"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Every dispatch, counted.",
         "subtitle": "tools.py aggregates the dispatch log per tool."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Five annotates (one failed, mean 14.0ms) plus two creates."""
    con = sqlite3.connect(db_path)
    try:
        con.execute("DELETE FROM tool_calls")
        for ms in (10, 10, 10, 10):
            con.execute("INSERT INTO tool_calls(method, ok, ms)"
                        " VALUES('annotate_decision', 1, ?)", (ms,))
        con.execute("INSERT INTO tool_calls(method, ok, ms)"
                    " VALUES('annotate_decision', 0, 30)")
        for _ in range(2):
            con.execute("INSERT INTO tool_calls(method, ok, ms)"
                        " VALUES('create_learning_module', 1, 50)")
        con.commit()
        return {"seeded": True}
    finally:
        con.close()
