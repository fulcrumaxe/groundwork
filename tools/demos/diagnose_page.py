"""Feature demo: traceback diagnose page (Batch 1).

Full functionality: paste a Python traceback and every function it
names links to its lesson; unknown names are listed too. seed_db picks
a real fixture symbol (answer_widget) and resolves the exact
/modules/{mid}#lesson-{slug} href the page will emit, so the submit
beat can assert the lesson link and the follow-up beat can film it.
"""
from __future__ import annotations

import sqlite3


def _slug(text: str) -> str:
    """Anchor slug mirroring groundwork.lessons.slug (stdlib only).

    Scenario modules cannot import groundwork: the film process runs
    as tools/demo_video.py, so only tools/ is on sys.path.
    """
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


SCENARIO = {
    "id": "diagnose-page",
    "kind": "feature",
    "batch": 1,
    "item": "F-38",
    "title": "Traceback diagnose page",
    "blurb": "Paste a crash; every function it names links to its lesson.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Feature diagnose-page",
         "title": "Traceback diagnose page",
         "subtitle": "Paste a crash; every function it names links to its lesson."},
        {"type": "chrome", "duration": 7,
         "url_path": "/diagnose#diagnose-form",
         "focus": "#diagnose-form",
         "caption": "The diagnose form: paste the red text from a crash.",
         "assert_js": "() => !!document.querySelector('#diagnose-form textarea[name=trace]')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "The crash will name a real fixture symbol -- here is its concept row.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print(con.execute(\"SELECT name, module_id FROM concepts WHERE name='{seed_symbol}' LIMIT 1\").fetchone())"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/diagnose",
         "caption": "Submit the traceback -- every named function links to its lesson.",
         "js": ["() => { const f = document.querySelector(\"form#diagnose-form\"); "
                "if (!f) return 'form-missing'; "
                "const ta = f.querySelector('textarea[name=trace]'); "
                "if (!ta) return 'no-textarea'; "
                "ta.value = 'Traceback (most recent call last):\\n  File \"app.py\", line 10, in {seed_symbol}\\nNameError: name \\'{seed_symbol}\\' is not defined'; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Study these, then diagnose",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector(\"a[href='/modules/{seed_mid}#lesson-{seed_slug}']\")",
         "assert_want": "True"},
        {"type": "chrome", "duration": 9,
         "url_path": "/modules/{seed_mid}#lesson-{seed_slug}",
         "focus": "#lesson-{seed_slug}",
         "caption": "The link lands on the concept's leveled lesson -- study first, then fix.",
         "assert_js": "() => !!document.querySelector('#lesson-{seed_slug}')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Study these, then diagnose.",
         "subtitle": "diagnose.py maps traceback frames to lessons -- unknown names listed too."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Resolve a real fixture symbol to the exact lesson href diagnose emits.

    Prefers answer_widget (taught by dozens of fixture modules);
    otherwise falls back to the first concept by rowid. Replicates
    diagnose_html's own name->(module, slug) query so the {seed_mid}
    and {seed_slug} tokens match the filmed link byte for byte. No
    mutation: diagnose is a read-only bridge over existing lessons.
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts WHERE name='answer_widget'"
            " ORDER BY rowid LIMIT 1").fetchone()
        symbol = "answer_widget" if row else None
        if not row:
            row = con.execute(
                "SELECT id, name FROM concepts ORDER BY rowid LIMIT 1"
            ).fetchone()
            if not row:
                return {"seeded": False, "reason": "no concepts"}
            symbol = row[1]
        found = con.execute(
            "SELECT concepts.id, concepts.name, concepts.module_id,"
            " modules.task_summary FROM concepts"
            " JOIN modules ON modules.id = concepts.module_id"
            " WHERE concepts.name=? LIMIT 1", (symbol,)).fetchone()
        if not found:
            return {"seeded": False, "reason": "symbol has no module"}
        cid, _name, mid = found[0], found[1], found[2]
        node = cid.split(":", 1)[1] if ":" in cid else cid
        return {"seeded": True, "symbol": symbol, "mid": mid,
                "slug": _slug(node)}
    finally:
        con.close()
