"""Improvement demo: misconception callouts (I-111).

Full functionality: misconceptions.callout() renders one wrong idea
per lesson as an aside box (HTML-escaped, blank renders empty). No
page wires the callout in yet, so seed_db loads the real
misconceptions.py standalone and renders byte-exact HTML; the
module-page beat mounts that callout on the live page while terminal
beats show the real callout() output, its escaping, and the fixture
rows behind it.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sqlite3

MISCONCEPTION = "Variables hold values, not boxes."


def _load_misconceptions():
    """Load groundwork/misconceptions.py standalone (stdlib-only)."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))
    path = os.path.join(root, "groundwork", "misconceptions.py")
    spec = importlib.util.spec_from_file_location("misconceptions_seed",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SCENARIO = {
    "id": "misconceptions",
    "kind": "improvement",
    "batch": 5,
    "item": "I-111",
    "title": "Misconception callouts",
    "blurb": "Lessons flag the wrong idea learners most often hold.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-111",
         "title": "Misconception callouts",
         "subtitle": "Lessons flag the wrong idea learners most often hold."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-misconceptions",
         "caption": "Status documents the item with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-misconceptions')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: one wrong idea becomes the box; blank stays silent.",
         "commands": [
             ["python3", "-c",
              "from groundwork import misconceptions as m; "
              "print(m.callout('{seed_mis}')); "
              "print('blank:', repr(m.callout('')))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}",
         "caption": "The real callout HTML for a lesson, mounted on the live module page.",
         "js": ["() => { const w = document.createElement('div'); "
                "w.id = 'misconceptions-demo'; "
                "w.setAttribute('style', 'border:2px solid var(--accent-modules);"
                "border-radius:10px;padding:12px 16px;margin:12px 0 16px 0;'); "
                "w.innerHTML = '<p><strong>Misconception callout</strong> ' "
                "+ '(per-lesson wrong idea):</p>' "
                "+ '{seed_mis_js}'; "
                "document.querySelector('main').prepend(w); return 'ok'; }"],
         "assert_js": "() => document.querySelector('#misconception strong').textContent"
                      " + '|' + document.querySelector('#misconception p:last-child').textContent",
         "assert_want": "Common misconception|{seed_mis}"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof: markup in, escaped text out -- never a live tag.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('module:', con.execute(\"SELECT id FROM modules "
              "WHERE id='{seed_mid}'\").fetchone()[0]); "
              "from groundwork import misconceptions as m; "
              "print(m.callout('<script>x</script>')); "
              "print('none:', repr(m.callout(None)))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "Name the wrong idea.",
         "subtitle": "misconceptions.py flags it -- escaped, silent when blank."},
    ],
}


def _js_escape(text: str) -> str:
    """Escape HTML for a single-quoted JS string inside beat JSON."""
    return (text.replace("\\", "\\\\").replace('"', '\\"')
            .replace("'", "\\\\'"))


def seed_db(db_path: str) -> dict:
    """Render byte-exact callout HTML; anchor the mount to a real module.

    Reads the fixture copy only (no row changes needed: the callout is
    a pure function of its string); loads groundwork/misconceptions.py
    standalone so the chrome beat mounts the true renderer output.
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM modules ORDER BY id LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no modules"}
        mod = _load_misconceptions()
        html_out = mod.callout(MISCONCEPTION)
        if ("id='misconception'" not in html_out
                or MISCONCEPTION not in html_out):
            return {"seeded": False, "reason": "renderer output unexpected"}
        return {"seeded": True, "mid": row[0], "mis": MISCONCEPTION,
                "mis_js": _js_escape(html_out)}
    finally:
        con.close()
