"""Improvement demo: helpful 404 (Batch 4, I-13).

Full functionality: unknown paths render links plus a project repo
search instead of a bare error, and the search always does something
honest -- it filters the module library. seed_db tags the newest
module summary so the filtered library must echo the marker.
"""
from __future__ import annotations

import sqlite3
import urllib.parse

SCENARIO = {
    "id": "pretty-404",
    "kind": "improvement",
    "batch": 4,
    "item": "I-13",
    "title": "Helpful 404",
    "blurb": "Unknown paths get links and a project search, never a bare error.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Improvement I-13",
         "title": "Helpful 404",
         "subtitle": "Unknown paths get links and a project search, never a bare error."},
        {"type": "terminal", "duration": 7,
         "caption": "Pure renderer: the unknown path, links, and a repo search form.",
         "commands": [
             ["python3", "-c",
              "from groundwork import errors as e; "
              "h = e.not_found_html('/nope-xyz-404'); "
              "print('names path:', 'nope-xyz-404' in h); "
              "print('search form:', \"action='/modules'\" in h); "
              "print('links:', h.count('<a href'))"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/nope-xyz-404",
         "caption": "A wrong URL names itself and offers a way out.",
         "assert_js": "() => !!document.querySelector('#not-found') + '|' + "
                      "document.body.innerText.includes('Nothing lives at')",
         "assert_want": "true|true"},
        {"type": "chrome", "duration": 9,
         "url_path": "/nope-xyz-404",
         "caption": "The project search filters the real module library.",
         "js": ["() => { const f = document.querySelector(\"#not-found form[action='/modules']\"); "
                "if (!f) return 'search-form-missing'; "
                "const box = f.querySelector('input[name=repo]'); "
                "if (!box) return 'no-repo-box'; box.value = '{seed_repo}'; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "{seed_marker}",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('{seed_marker}')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Never a dead end.",
         "subtitle": "errors.py renders links plus a search that always lands somewhere real."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Tag the newest module so the repo search must surface it."""
    con = sqlite3.connect(db_path)
    try:
        m = con.execute(
            "SELECT id, repo FROM modules ORDER BY created_at DESC"
            " LIMIT 1").fetchone()
        if not m:
            return {"seeded": False, "reason": "no modules"}
        mid, repo = m[0], m[1] or ""
        marker = "FourOhFour42"
        con.execute(
            "UPDATE modules SET task_summary = ? || ' ' || COALESCE(task_summary, id)"
            " WHERE id=?", (marker, mid))
        con.commit()
        return {"seeded": True, "mid": mid, "repo": repo,
                "repo_q": urllib.parse.quote(repo, safe=""),
                "marker": marker}
    finally:
        con.close()
