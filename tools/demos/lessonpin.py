"""Improvement demo: pinned lessons (I-117).

Full behavior: ?pin= names must-read lessons and Handler.module_html
renders them first with a Pinned chip; no pins keeps the legacy
order byte-identical. seed_db picks a real 3+-concept module and
pins its last concept, so both the legacy order and the pinned-first
flip film on the real caller path.
"""
from __future__ import annotations

import sqlite3
from urllib.parse import quote

SCENARIO = {
    "id": "lessonpin",
    "kind": "improvement",
    "batch": 20,
    "item": "I-117",
    "title": "Pinned lessons",
    "blurb": "Pin must-read lessons so they stay atop the module no matter how the list is ordered.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Improvement I-117",
         "title": "Pinned lessons",
         "subtitle": "Must-read lessons stay atop the module -- unpinned pages render exactly as before."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-lessonpin",
         "caption": "Status documents the rule: pinned rows first, with a marker.",
         "assert_js": "() => !!document.querySelector('#status-b20-lessonpin') && "
                      "document.body.innerText.includes('Pinned')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule: pinned names jump first in pin order; empty pins return the input order.",
         "commands": [
             ["python3", "-c",
              "from groundwork import lessonpin as m; "
              "rows = [{'cid': 'm:a', 'name': 'a'}, {'cid': 'm:b', 'name': 'b'}, {'cid': 'm:c', 'name': 'c'}]; "
              "print('pinned:', [r['name'] for r in m.order_with_pins(rows, ['c', 'a'])]); "
              "print('legacy:', [r['name'] for r in m.order_with_pins(rows, [])]); "
              "print('chip:', m.pin_marker_html({'name': 'c'}, ['c'])); "
              "print('css ships:', '.pin{' in m.pin_css())"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "caption": "No pins: the module keeps its legacy order and no chip renders.",
         "assert_js": "() => { const secs = [...document.querySelectorAll(\"section[id^='lesson-']\")].map(s => s.id); "
                      "return secs[0] === 'lesson-{seed_first_slug}' && !document.querySelector('.pin'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}?pin={seed_pin_enc}",
         "caption": "Pin the last lesson: the table of contents flips pinned-first.",
         "assert_js": "() => { const secs = [...document.querySelectorAll(\"section[id^='lesson-']\")].map(s => s.id); "
                      "const first = document.querySelector('#readtime a'); "
                      "return secs[0] === 'lesson-{seed_pin_slug}' && !!first && "
                      "first.getAttribute('href') === '#lesson-{seed_pin_slug}'; }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}?pin={seed_pin_enc}#lesson-{seed_pin_slug}",
         "focus": "#lesson-{seed_pin_slug}",
         "caption": "The pinned section leads the page and carries the Pinned chip.",
         "assert_js": "() => !!document.querySelector('#lesson-{seed_pin_slug} .pin')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Pin it, keep it close.",
         "subtitle": "lessonpin.py partitions pinned-first -- unknown pins keep legacy bytes."},
    ],
}


def _slug(text) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(text or ""))
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """A real 3+-concept module; the pin names its last concept's node."""
    con = sqlite3.connect(db_path)
    try:
        mods = con.execute("SELECT module_id, COUNT(*) FROM concepts"
                           " GROUP BY module_id HAVING COUNT(*) >= 3"
                           " ORDER BY COUNT(*) DESC").fetchall()
        for (mid, _n) in mods:
            rows = con.execute("SELECT id FROM concepts WHERE module_id=?"
                               " ORDER BY rowid", (mid,)).fetchall()
            if len(rows) < 3:
                continue
            first_node = rows[0][0].split(":", 1)[1] \
                if ":" in rows[0][0] else rows[0][0]
            pin_node = rows[-1][0].split(":", 1)[1] \
                if ":" in rows[-1][0] else rows[-1][0]
            if _slug(pin_node) == _slug(first_node):
                continue
            return {"seeded": True, "mid": mid, "pin": pin_node,
                    "pin_enc": quote(pin_node, safe=""),
                    "pin_slug": _slug(pin_node),
                    "first_slug": _slug(first_node)}
        return {"seeded": False, "reason": "no 3-concept module"}
    finally:
        con.close()
