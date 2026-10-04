"""Improvement demo: prerequisite chain path (I-147).

Full functionality: prereq.chain_html() renders an ordered
understand-X-first nav with one jump link per concept (anchors via
lessons.slug). No page wires the chain in yet, so seed_db loads the
real prereq.py (stubbing only the lessons.slug import) and renders
byte-exact HTML for three REAL fixture lesson names; the module-page
beat mounts that nav atop the live page while terminal beats show the
real chain_html() output and the fixture rows behind it.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
import types


def _slug(text: str) -> str:
    """Exact copy of groundwork.lessons.slug (URL-fragment anchor slug)."""
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    out = "-".join(filter(None, out.split("-")))
    return out or "lesson"


def _load_prereq():
    """Load groundwork/prereq.py standalone (stub only lessons.slug)."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))
    path = os.path.join(root, "groundwork", "prereq.py")
    pkg = types.ModuleType("prereq_seed_pkg")
    pkg.__path__ = []
    sys.modules["prereq_seed_pkg"] = pkg
    stub = types.ModuleType("prereq_seed_pkg.lessons")
    stub.slug = _slug
    sys.modules["prereq_seed_pkg.lessons"] = stub
    spec = importlib.util.spec_from_file_location("prereq_seed_pkg.prereq",
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SCENARIO = {
    "id": "prereq",
    "kind": "improvement",
    "batch": 5,
    "item": "I-147",
    "title": "Prerequisite chain",
    "blurb": "Understand-X-first path with jump links atop each module.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-147",
         "title": "Prerequisite chain",
         "subtitle": "Understand-X-first path with jump links atop each module."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-prereq",
         "caption": "Status documents the item with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-prereq')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: ordered concepts become slug jump links; empty stays silent.",
         "commands": [
             ["python3", "-c",
              "from groundwork import prereq as m; "
              "print(m.chain_html(['{seed_c0}', '{seed_c1}', '{seed_c2}'])); "
              "print('empty:', repr(m.chain_html([])))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}",
         "caption": "The real chain_html nav for this module's lessons, mounted atop the live page.",
         "js": ["() => { const w = document.createElement('div'); "
                "w.id = 'prereq-demo'; "
                "w.setAttribute('style', 'border:2px solid var(--accent-modules);"
                "border-radius:10px;padding:12px 16px;margin:12px 0 16px 0;'); "
                "w.innerHTML = '<p><strong>Prerequisite chain</strong> ' "
                "+ '(understand-X-first path):</p>' "
                "+ '{seed_prereq_js}'; "
                "document.querySelector('main').prepend(w); return 'ok'; }"],
         "assert_js": "() => [...document.querySelectorAll('#prereq a')]"
                      ".map(a => a.getAttribute('href')).join(',')",
         "assert_want": "#{seed_s0},#{seed_s1},#{seed_s2}"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof: the chain names come from real fixture lessons; dict inputs work too.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3, json; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "L = json.loads(con.execute(\"SELECT lessons FROM modules "
              "WHERE id='{seed_mid}'\").fetchone()[0]); "
              "print('module {seed_mid}:', [x['name'] for x in L][:3]); "
              "from groundwork import prereq as m; "
              "print(m.chain_html([{'name': '{seed_c0}'}, "
              "{'concept': '{seed_c1}'}]))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "Understand X first.",
         "subtitle": "prereq.py builds the path -- pure HTML over concept names."},
    ],
}


def _js_escape(text: str) -> str:
    """Escape HTML for a single-quoted JS string inside beat JSON."""
    return text.replace("'", "\\\\'")


def seed_db(db_path: str) -> dict:
    """Render byte-exact chain HTML for three real fixture lesson names.

    Reads the fixture copy only (no row changes needed: lesson names
    already exist); loads groundwork/prereq.py standalone so the
    chrome beat mounts the true renderer output.
    """
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id, lessons FROM modules ORDER BY id").fetchall()
        picked = None
        for mid, lessons_json in rows:
            try:
                lessons = json.loads(lessons_json or "[]")
            except ValueError:
                continue
            names = [L.get("name", "") for L in lessons[:3]]
            if (len(names) >= 3 and all(n.strip() for n in names)
                    and not any("'" in n or '"' in n for n in names)):
                picked = (mid, names[:3])
                break
        if not picked:
            return {"seeded": False, "reason": "need module with 3 lessons"}
        mid, names = picked
        mod = _load_prereq()
        html_out = mod.chain_html(names)
        slugs = [_slug(n) for n in names]
        if ("id='prereq'" not in html_out
                or not all("#" + s in html_out for s in slugs)):
            return {"seeded": False, "reason": "renderer output unexpected"}
        return {"seeded": True, "mid": mid,
                "c0": names[0], "c1": names[1], "c2": names[2],
                "s0": slugs[0], "s1": slugs[1], "s2": slugs[2],
                "prereq_js": _js_escape(html_out)}
    finally:
        con.close()
