"""Improvement demo: copy-link anchors (I-28).

Full functionality: every lesson section carries its own deep link --
sections render as id='lesson-<slug>' and the lesson list jumps to them;
copylink.copy_link() renders the '#' anchor link itself. seed_db selects
a real module plus its first lesson slug (read-only); the module beat
clicks that lesson's TOC link and shows the live location hash.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "copylink",
    "kind": "improvement",
    "batch": 5,
    "item": "I-28",
    "title": "Copy-link anchors",
    "blurb": "Every lesson section carries its own deep link.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-28",
         "title": "Copy-link anchors",
         "subtitle": "Every lesson section carries its own deep link."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-copylink",
         "caption": "Status documents the improvement with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-copylink')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The helper in one line: a section name becomes a '#' deep link.",
         "commands": [
             ["python3", "-c",
              "from groundwork import copylink as m; "
              "print(m.copy_link('Lesson One')); "
              "print(repr(m.copy_link('')))"],
         ]},
        {"type": "chrome", "duration": 13,
         "url_path": "/modules/{seed_mid}",
         "caption": "One click on the lesson list jumps to that section -- the readout shows the live hash.",
         "js": ["() => { const a = document.querySelector("
                "\"p.toc a[href='#lesson-{seed_lesson}']\"); "
                "if (!a) return 'toc-link-missing'; a.click(); "
                "const p = document.createElement('p'); p.id = 'hash-readout'; "
                "const target = document.querySelector(location.hash); "
                "p.textContent = 'Deep link: ' + location.hash + "
                "' -- section found: ' + !!target; "
                "p.setAttribute('style', 'border:2px solid var(--accent-modules);"
                "padding:8px 12px;font-weight:bold'); "
                "document.querySelector('main').prepend(p); "
                "return location.hash; }"],
         "poll_js": "() => location.hash",
         "poll_want": "#lesson-{seed_lesson}",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => location.hash",
         "assert_want": "#lesson-{seed_lesson}"},
        {"type": "terminal", "duration": 5,
         "caption": "Blanks render empty and markup is escaped -- anchors stay fragment-safe.",
         "commands": [
             ["python3", "-c",
              "from groundwork import copylink as m; "
              "print(repr(m.copy_link(None))); "
              "print(m.copy_link('<b>x</b>'))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "Deep links everywhere.",
         "subtitle": "copylink.py renders the '#' link -- sections carry their own anchors."},
    ],
}


def _slug(text: str) -> str:
    """Anchor slug mirroring groundwork.lessons.slug (stdlib only)."""
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in (text or ""))
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """A real module id plus its first lesson slug (read-only select).

    Matches Handler.module_html exactly ('lesson-' + slug of the
    concept node); no fixture rows change, so the served library DB
    is untouched by construction.
    """
    con = sqlite3.connect(db_path)
    try:
        modules = con.execute(
            "SELECT id FROM modules ORDER BY rowid DESC").fetchall()
        for (mid,) in modules:
            concepts = con.execute(
                "SELECT id FROM concepts WHERE module_id=? ORDER BY rowid",
                (mid,)).fetchall()
            if not concepts:
                continue
            cid = concepts[0][0]
            node = cid.split(":", 1)[1] if ":" in cid else cid
            return {"seeded": True, "mid": mid, "lesson": _slug(node)}
        return {"seeded": False, "reason": "no concepts"}
    finally:
        con.close()
