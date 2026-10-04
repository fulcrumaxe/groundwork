"""Improvement demo: related modules (Batch 4, I-23).

Full functionality: each module page ends with related modules --
same repo or shared concept names -- each link explained. seed_db
tags one sibling summary so the list must echo the marker.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "related-modules",
    "kind": "improvement",
    "batch": 4,
    "item": "I-23",
    "title": "Related modules",
    "blurb": "Same repo or shared concepts -- keep following the thread.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 4 - Improvement I-23",
         "title": "Related modules",
         "subtitle": "Same repo or shared concepts -- keep following the thread."},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}",
         "focus": "#related",
         "caption": "The module page ends with related modules, each explained.",
         "assert_js": "() => document.body.innerText.includes('{seed_marker}')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The renderer over the fixture rows: the marked sibling.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import related as r; "
              "db = os.environ.get('DEMO_DB', 'groundwork.db'); "
              "h = r.related_html(db, '{seed_mid}'); "
              "print('marked sibling listed:', '{seed_marker}' in h); "
              "print('related count:', h.count('<li>'))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "caption": "Following the thread lands on the sibling module.",
         "js": ["() => { const h = document.querySelector('#related'); "
                "let n = h ? h.nextElementSibling : null; "
                "while (n && n.tagName !== 'UL' && !/^H[23]$/.test(n.tagName)) n = n.nextElementSibling; "
                "const a = n ? Array.from(n.querySelectorAll('a')).find(x => x.textContent.includes('{seed_marker}')) : null; "
                "if (!a) return 'sibling-link-missing'; a.click(); return 'clicked'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "{seed_marker}",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => location.pathname",
         "assert_want": "/modules/{seed_sib}"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 4",
         "title": "Keep following the thread.",
         "subtitle": "related.py links same-repo and shared-concept siblings."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Tag one sibling of the biggest module.

    Every library module shares one repo, so same-repo siblings always
    exist; the marked sibling sorts first by recency either way.
    """
    con = sqlite3.connect(db_path)
    try:
        m = con.execute(
            "SELECT concepts.module_id, COUNT(*) FROM cards "
            "JOIN concepts ON concepts.id = cards.concept_id "
            "GROUP BY concepts.module_id "
            "ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
        if not m:
            return {"seeded": False, "reason": "no cards"}
        mid = m[0]
        sib = con.execute(
            "SELECT id FROM modules WHERE id != ?"
            " ORDER BY created_at DESC LIMIT 1", (mid,)).fetchone()
        if not sib:
            return {"seeded": False, "reason": "need a sibling module"}
        sib = sib[0]
        marker = "RelatedSeed42"
        con.execute(
            "UPDATE modules SET task_summary = ? || ' ' || COALESCE(task_summary, id)"
            " WHERE id=?", (marker, sib))
        con.commit()
        return {"seeded": True, "mid": mid, "sib": sib, "marker": marker}
    finally:
        con.close()
