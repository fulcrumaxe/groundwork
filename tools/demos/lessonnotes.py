"""Improvement demo: private lesson notes (I-118).

Full functionality: lessonnotes.notes_box() renders a per-lesson
textarea whose text lives in browser localStorage under a per-lesson
key -- no server DB writes. No page wires the box in yet, so seed_db
loads the real lessonnotes.py standalone and renders byte-exact HTML
for a REAL fixture lesson key; the module-page beat mounts that box on
the live page, executes its real inline script, and proves a saved
note restores into the textarea, while terminal beats show the real
notes_box() output and the fixture rows behind it.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sqlite3

NOTE_TEXT = "render_levels branches on exercise type"


def _slug(text: str) -> str:
    """Exact copy of groundwork.lessons.slug (lesson key fragment)."""
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    out = "-".join(filter(None, out.split("-")))
    return out or "lesson"


def _load_lessonnotes():
    """Load groundwork/lessonnotes.py standalone (stdlib-only module)."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))
    path = os.path.join(root, "groundwork", "lessonnotes.py")
    spec = importlib.util.spec_from_file_location("lessonnotes_seed", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SCENARIO = {
    "id": "lessonnotes",
    "kind": "improvement",
    "batch": 5,
    "item": "I-118",
    "title": "Private lesson notes",
    "blurb": "A per-lesson scratchpad kept in your browser only.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-118",
         "title": "Private lesson notes",
         "subtitle": "A per-lesson scratchpad kept in your browser only."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-lessonnotes",
         "caption": "Status documents the item with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-lessonnotes')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: a lesson key becomes the box; blank keys fall back.",
         "commands": [
             ["python3", "-c",
              "from groundwork import lessonnotes as m; "
              "h = m.notes_box('{seed_lkey}'); "
              "print(h[:150]); "
              "print('restores via localStorage:', 'localStorage' in h); "
              "print('fallback:', \"data-notes-for='lesson'\" in m.notes_box(''))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}",
         "caption": "The real notes box on the live page: its own script restores the saved note.",
         "js": ["() => { localStorage.setItem('gw-notes-{seed_lkey}', '{seed_note}'); "
                "const w = document.createElement('div'); "
                "w.id = 'lessonnotes-demo'; "
                "w.setAttribute('style', 'border:2px solid var(--accent-modules);"
                "border-radius:10px;padding:12px 16px;margin:12px 0 16px 0;'); "
                "w.innerHTML = '<p><strong>Private notes</strong> ' "
                "+ '(per-lesson scratchpad):</p>' "
                "+ '{seed_notes_js}'; "
                "document.querySelector('main').prepend(w); "
                "const s = w.querySelector('#lessonnotes script'); "
                "const r = document.createElement('script'); "
                "r.textContent = s.textContent; s.replaceWith(r); "
                "return 'ok'; }"],
         "assert_js": "() => document.querySelector('#lessonnotes textarea').value"
                      " + '|' + localStorage.getItem('gw-notes-{seed_lkey}')",
         "assert_want": "{seed_note}|{seed_note}"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof: per-lesson storage key, zero server writes, from fixture data.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3, json; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "L = json.loads(con.execute(\"SELECT lessons FROM modules "
              "WHERE id='{seed_mid}'\").fetchone()[0]); "
              "print('lesson:', [x['name'] for x in L][0]); "
              "from groundwork import lessonnotes as m; "
              "h = m.notes_box('{seed_lkey}'); "
              "print('storage key present:', 'gw-notes-{seed_lkey}' in h); "
              "print('server writes:', ('fetch(' in h) or ('POST' in h))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "Your notes stay yours.",
         "subtitle": "lessonnotes.py renders the box -- the browser keeps the words."},
    ],
}


def _js_escape(text: str) -> str:
    """Escape HTML for a single-quoted JS string inside beat JSON."""
    return (text.replace("\\", "\\\\").replace('"', '\\"')
            .replace("'", "\\\\'"))


def seed_db(db_path: str) -> dict:
    """Render byte-exact notes HTML for a real fixture lesson key.

    Reads the fixture copy only (no row changes needed: notes live in
    the browser, not the DB); loads groundwork/lessonnotes.py
    standalone so the chrome beat mounts the true renderer output.
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
            names = [L.get("name", "") for L in lessons[:1]]
            if (names and names[0].strip()
                    and "'" not in names[0] and '"' not in names[0]):
                picked = (mid, names[0])
                break
        if not picked:
            return {"seeded": False, "reason": "need module with a lesson"}
        mid, name = picked
        lkey = "lesson-" + _slug(name)
        mod = _load_lessonnotes()
        html_out = mod.notes_box(lkey)
        if ("id='lessonnotes'" not in html_out
                or "localStorage" not in html_out
                or lkey not in html_out):
            return {"seeded": False, "reason": "renderer output unexpected"}
        return {"seeded": True, "mid": mid, "lkey": lkey,
                "note": NOTE_TEXT, "notes_js": _js_escape(html_out)}
    finally:
        con.close()
