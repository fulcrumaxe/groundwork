"""Improvement demo: due-count favicon (I-87).

Full behavior: every page's <link rel='icon'> carries the live due
count as a badge (capped at 99+, plain mark at zero), so the tab says
whether cards are waiting. seed_db leaves exactly three cards due;
the /due beat decodes the badge number from the live link tag.
"""
from __future__ import annotations

import sqlite3

DUE_COUNT = 3

SCENARIO = {
    "id": "pageicon",
    "kind": "improvement",
    "batch": 13,
    "item": "I-87",
    "title": "Due-count favicon",
    "blurb": "The tab icon carries the live due count -- zero means the plain mark.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Improvement I-87",
         "title": "Due-count favicon",
         "subtitle": "The tab icon says whether cards are waiting."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b13-pageicon",
         "caption": "Status documents the badge: SVG data URI, capped at 99+, no new route.",
         "assert_js": "() => !!document.querySelector('#status-b13-pageicon')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: zero hides, counts show, triple digits cap.",
         "commands": [
             ["python3", "-c",
              "from groundwork import pageicon as m; "
              "print('badges:', repr(m.badge_text(0)), repr(m.badge_text(3)), repr(m.badge_text(150))); "
              "print('badged svg longer:', len(m.icon_svg(3)) > len(m.icon_svg(0))); "
              "print('link:', m.link_tag({'due': 3})[:60])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "caption": "Three cards due, three on the tab: the badge decodes from the live link tag.",
         "assert_js": "() => { const l = document.querySelector(\"link#gw-icon[rel='icon']\"); "
                      "if (!l) return false; "
                      "return decodeURIComponent(l.href).includes('>{seed_due}<'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture DB: exactly three cards due, matching the badge.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; from datetime import datetime, timezone; "
              "now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'); "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "n = con.execute('SELECT COUNT(*) FROM cards WHERE due <= ? AND stale = 0', (now,)).fetchone()[0]; "
              "print('due now:', n)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Glance at the tab.",
         "subtitle": "pageicon.py reads the nav counts the head wire already receives."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Exactly DUE_COUNT cards due-now; everything else parked in 2030."""
    con = sqlite3.connect(db_path)
    try:
        ids = [r[0] for r in con.execute(
            "SELECT id FROM cards ORDER BY rowid LIMIT ?",
            (DUE_COUNT,)).fetchall()]
        if len(ids) < DUE_COUNT:
            return {"seeded": False, "reason": "not enough cards"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute(
            f"UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id IN "
            f"({','.join('?' * len(ids))})", ids)
        con.commit()
        return {"seeded": True, "due": DUE_COUNT, "card_ids": ",".join(ids)}
    finally:
        con.close()
