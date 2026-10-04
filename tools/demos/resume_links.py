"""Demo: resume links (Batch 1 improvement).

Full functionality: each module card on /modules jumps straight to
its first unowned lesson (_first_unowned over module order). seed_db
wipes reviews on the lead module's first concept so the card reads
Resume with a lesson anchor (never Review again); the beats film
the library, the pure rule, the click landing mid-module, and the
fixture proof.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

SCENARIO = {
    "id": "resume-links",
    "kind": "improvement",
    "batch": 1,
    "item": "I-21",
    "title": "Resume links",
    "blurb": "Each module card jumps straight to its first unowned lesson.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Improvement resume-links",
         "title": "Resume links",
         "subtitle": "Each module card jumps to its first unowned lesson."},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules",
         "focus": "#library",
         "caption": "Every module card offers Resume into its first unowned lesson.",
         "assert_js": "() => { const a = document.querySelector('#resume'); return a && a.textContent === 'Resume' && a.getAttribute('href').includes('#lesson-'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule: first concept in module order that is not Owned.",
         "commands": [
             ["python3", "-c",
              "from groundwork.web import _first_unowned; "
              "print(_first_unowned({'a': (0, False), 'b': (3, True)}, ['a', 'b'])); "
              "print(_first_unowned({'a': (2, True), 'b': (0, False)}, ['a', 'b']))"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules",
         "focus": "#lesson-{seed_resume_slug}",
         "caption": "One click lands mid-module at the exact unowned lesson.",
         "js": ["() => { const a = document.querySelector('#resume'); if (!a) return 'resume-missing'; a.click(); return 'clicked:' + a.getAttribute('href'); }"],
         "poll_js": "() => location.href",
         "poll_want": "#lesson-{seed_resume_slug}",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('#lesson-{seed_resume_slug}')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture: the resume target holds zero attempts.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('attempts on resume target:', con.execute(\"SELECT COUNT(*) FROM reviews JOIN cards ON cards.id = reviews.card_id WHERE cards.concept_id = '{seed_concept}'\").fetchone()[0])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Pick up where you left off.",
         "subtitle": "_first_unowned aims the link; zero attempts means unowned."},
    ],
}


def _slug(text: str) -> str:
    """Anchor slug for a lesson node (mirrors lessons.slug: no groundwork
    imports allowed in seed -- the film process lacks ROOT on sys.path)."""
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Wipe reviews on the lead module's first concept to force Resume.

    The mi==0 card under default newest-sort is the newest module; if
    it holds no concepts, the newest module WITH concepts is bumped a
    day past the max created_at so it leads. Deleting that module's
    first-concept (rowid order) reviews makes _first_unowned aim at it
    and owned_map report zero attempts. Returns tokens for the beats.
    """
    con = sqlite3.connect(db_path)
    try:
        mods = con.execute(
            "SELECT id FROM modules ORDER BY created_at DESC, rowid DESC"
        ).fetchall()
        if not mods:
            return {"seeded": False, "reason": "no modules"}
        mid = None
        for (cand,) in mods:
            n = con.execute(
                "SELECT COUNT(*) FROM concepts WHERE module_id = ?",
                (cand,)).fetchone()[0]
            if n:
                mid = cand
                break
        if mid is None:
            return {"seeded": False, "reason": "no concepts"}
        if mid != mods[0][0]:
            raw = con.execute("SELECT MAX(created_at) FROM modules").fetchone()[0] or ""
            try:
                bumped = (datetime.strptime(raw[:19], "%Y-%m-%dT%H:%M:%S")
                          + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                bumped = "2999-01-01T00:00:00Z"
            con.execute("UPDATE modules SET created_at = ? WHERE id = ?",
                        (bumped, mid))
        first = con.execute(
            "SELECT id FROM concepts WHERE module_id = ? ORDER BY rowid LIMIT 1",
            (mid,)).fetchone()
        if not first:
            return {"seeded": False, "reason": "no concepts"}
        cid = first[0]
        node = cid.split(":", 1)[1] if ":" in cid else cid
        con.execute(
            "DELETE FROM reviews WHERE card_id IN "
            "(SELECT id FROM cards WHERE concept_id = ?)", (cid,))
        con.commit()
        return {"seeded": True, "module_id": mid, "concept": cid,
                "resume_slug": _slug(node)}
    finally:
        con.close()
