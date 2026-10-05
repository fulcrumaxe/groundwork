"""Improvement demo: share unfurls (I-88).

Full behavior: every page head carries og:title/type/site/description
from the live (title, lede), and module pages pass their task summary
as the lede so shares name the concept studied (demo-video batch 13
also wired the route, which never passed one). seed_db picks the
first module; the module beat asserts its summary unfurls.
"""
from __future__ import annotations

import re
import sqlite3


def _clean(text) -> str:
    return re.sub(r"\s+", " ", str(text or "")).replace(
        '"', "").replace("'", "").replace("\\", "")[:200]


SCENARIO = {
    "id": "ogtags",
    "kind": "improvement",
    "batch": 13,
    "item": "I-88",
    "title": "Share unfurls",
    "blurb": "Shared links unfurl with the page title and lede -- no localhost lie.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Improvement I-88",
         "title": "Share unfurls",
         "subtitle": "Shared links unfurl with title and lede -- no bare URLs."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-ogtags",
         "caption": "Status documents the minimal set: title, type, site, description.",
         "assert_js": "() => !!document.querySelector('#status-b13-ogtags')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: escaped, one line, capped -- and never a localhost URL.",
         "commands": [
             ["python3", "-c",
              "from groundwork import ogtags as m; "
              "tags = m.og_tags('Module', 'Study <b>closures</b>.'); "
              "print('set:', all(k in tags for k in ('og:title', 'og:type', 'og:site_name', 'og:description'))); "
              "print('escaped:', '<b>' not in tags); "
              "print('no url:', 'og:url' not in m.og_tags('Module', 'lede')); "
              "long = m.og_tags('T', 'x' * 400); "
              "print('capped:', '...' in long)"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/modules/{seed_module_id}",
         "caption": "A module share names what is studied: title plus the live summary lede.",
         "assert_js": "() => { const t = document.querySelector(\"meta[property='og:title']\"); "
                      "const d = document.querySelector(\"meta[property='og:description']\"); "
                      "const u = document.querySelector(\"meta[property='og:url']\"); "
                      "return !!t && !!d && !u && d.content.includes('{seed_summary}'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Paste it anywhere.",
         "subtitle": "ogtags.py unfurls every page -- module routes pass the summary."},
    ],
}


def seed_db(db_path: str) -> dict:
    """First module's id plus its quote-stripped summary for exact match."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id, task_summary FROM modules ORDER BY rowid LIMIT 1"
        ).fetchone()
        if not row:
            return {"seeded": False, "reason": "no modules"}
        summary = _clean(row[1])
        if not summary:
            return {"seeded": False, "reason": "blank summary"}
        return {"seeded": True, "module_id": row[0], "summary": summary}
    finally:
        con.close()
