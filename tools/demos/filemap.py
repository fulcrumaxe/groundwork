"""Improvement demo: file-map mini-view (I-128).

Full functionality: filemap.file_map() renders a breadcrumb plus a
sibling mini-tree (current path in <strong>) from repo-relative paths.
No page renders file maps live yet, so seed_db loads the real
filemap.py (stdlib-only, no groundwork imports) from its file path and
renders the byte-exact HTML for real fixture concept paths; the
/modules beat mounts that HTML on the live page while terminal beats
show the real file_map() output and the fixture paths behind it.
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3


def _load_filemap():
    """Load groundwork/filemap.py standalone (stdlib-only module)."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))
    path = os.path.join(root, "groundwork", "filemap.py")
    spec = importlib.util.spec_from_file_location("filemap_seed", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SCENARIO = {
    "id": "filemap",
    "kind": "improvement",
    "batch": 5,
    "item": "I-128",
    "title": "File-map mini-view",
    "blurb": "Breadcrumbs show where a concept sits in the repo tree.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-128",
         "title": "File-map mini-view",
         "subtitle": "Breadcrumbs show where a concept sits in the repo tree."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-filemap",
         "caption": "Status documents the item with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-filemap')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: breadcrumb links plus the sibling tree, current in bold.",
         "commands": [
             ["python3", "-c",
              "from groundwork import filemap as m; "
              "paths = ['{seed_path_a}', '{seed_path_b}', '{seed_path_c}']; "
              "print(m.file_map(paths, '{seed_current}'))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules",
         "caption": "The real file_map HTML for fixture concept paths, mounted on Modules.",
         "js": ["() => { const w = document.createElement('div'); "
                "w.id = 'filemap-demo'; "
                "w.setAttribute('style', 'border:2px solid var(--accent-modules);"
                "border-radius:10px;padding:12px 16px;margin:12px 0 16px 0;'); "
                "w.innerHTML = '<p><strong>File map</strong> ' "
                "+ '(repo position of {seed_current_leaf}):</p>' "
                "+ '{seed_filemap_js}'; "
                "document.querySelector('main').prepend(w); return 'ok'; }"],
         "assert_js": "() => document.querySelector('#filemap nav.crumbs').innerText"
                      " + '|' + document.querySelector('#filemap strong').textContent",
         "assert_want": "{seed_crumb_text}|{seed_current}"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof: the sibling paths come from real fixture concept ids.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('concepts:', [r[0] for r in con.execute(\"SELECT DISTINCT concept_id FROM cards WHERE concept_id LIKE '%{seed_current}%' LIMIT 3\")]); "
              "from groundwork import filemap as m; "
              "print('empty:', m.file_map([], ''))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "Never lost in the tree.",
         "subtitle": "filemap.py renders crumbs plus siblings -- pure HTML, no queries."},
    ],
}


def _js_escape(text: str) -> str:
    """Escape HTML for a single-quoted JS string via the JSON round-trip.

    render_beat() substitutes tokens into JSON text and json.loads it,
    so a literal backslash-quote in the final JS needs double-backslash
    in the token value (JSON has no \\' escape). file_map output never
    contains raw double quotes or newlines.
    """
    return text.replace("'", "\\\\'")


def seed_db(db_path: str) -> dict:
    """Render byte-exact file_map HTML for real fixture concept paths.

    Reads the fixture copy only (no row changes needed: concept paths
    already exist); loads groundwork/filemap.py standalone to produce
    the true HTML the chrome beat mounts.
    """
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT DISTINCT concept_id FROM cards").fetchall()
        files = []
        for (cid,) in rows:
            parts = (cid or "").split(":")
            if len(parts) >= 3:
                f = parts[1].strip()
                if f and f not in files:
                    files.append(f)
            if len(files) >= 4:
                break
        if len(files) < 3:
            return {"seeded": False, "reason": "need 3 concept files"}
        paths = files[:3]
        current = paths[1] if len(paths) > 1 else paths[0]
        fm = _load_filemap()
        html_out = fm.file_map(paths, current)
        leaf = current.rsplit("/", 1)[-1]
        crumb_text = " / ".join(current.split("/"))
        # Sanity: the HTML must carry the breadcrumb and the bold current.
        if "<strong>" not in html_out or leaf not in html_out:
            return {"seeded": False, "reason": "renderer output unexpected"}
        return {"seeded": True, "path_a": paths[0], "path_b": paths[1],
                "path_c": paths[2], "current": current,
                "current_leaf": leaf, "crumb_text": crumb_text,
                "filemap_js": _js_escape(html_out)}
    finally:
        con.close()
