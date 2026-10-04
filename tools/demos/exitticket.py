"""Improvement demo: one-question exit ticket (I-113).

Full functionality: exitticket.ticket_html() renders a single
lesson-closing prompt as an ungraded form (no action/method, so no
POST target by construction). No page wires the ticket in yet, so
seed_db loads the real exitticket.py standalone and renders byte-exact
HTML for a REAL fixture lesson name; the module-page beat appends that
form at lesson-end position on the live page, types an answer, and
proves the form has no POST target, while terminal beats show the real
ticket_html() output and the fixture rows behind it.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sqlite3

TYPED = "Renders the matched answer widget for the exercise type"


def _load_exitticket():
    """Load groundwork/exitticket.py standalone (stdlib-only module)."""
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(os.path.dirname(here))
    path = os.path.join(root, "groundwork", "exitticket.py")
    spec = importlib.util.spec_from_file_location("exitticket_seed", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SCENARIO = {
    "id": "exitticket",
    "kind": "improvement",
    "batch": 5,
    "item": "I-113",
    "title": "Exit tickets",
    "blurb": "Each lesson ends with one ungraded retrieval question.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-113",
         "title": "Exit tickets",
         "subtitle": "Each lesson ends with one ungraded retrieval question."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-exitticket",
         "caption": "Status documents the item with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-exitticket')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: concept plus prompt becomes the form; blank stays silent.",
         "commands": [
             ["python3", "-c",
              "from groundwork import exitticket as m; "
              "print(m.ticket_html('{seed_concept}', '{seed_prompt}')); "
              "print('blank:', repr(m.ticket_html('', '')))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}",
         "focus": "#exitticket-demo",
         "caption": "The real ticket form at lesson-end, with an answer typed -- and no POST target.",
         "js": ["() => { const w = document.createElement('div'); "
                "w.id = 'exitticket-demo'; "
                "w.setAttribute('style', 'border:2px solid var(--accent-modules);"
                "border-radius:10px;padding:12px 16px;margin:12px 0 16px 0;'); "
                "w.innerHTML = '<p><strong>Exit ticket</strong> ' "
                "+ '(lesson close, ungraded):</p>' "
                "+ '{seed_ticket_js}'; "
                "const t = w.querySelector(\"textarea[name='exit-answer']\"); "
                "t.value = '{seed_typed}'; t.textContent = '{seed_typed}'; "
                "document.querySelector('main').appendChild(w); return 'ok'; }"],
         "assert_js": "() => { const f = document.querySelector('#exitticket'); "
                      "const t = f && f.querySelector(\"textarea[name='exit-answer']\"); "
                      "return (f ? f.getAttribute('action') : 'noform') + '|' "
                      "+ (t ? t.value : 'notext'); }",
         "assert_want": "null|{seed_typed}"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof: ungraded by construction -- no action, no method, from fixture data.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3, json; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "L = json.loads(con.execute(\"SELECT lessons FROM modules "
              "WHERE id='{seed_mid}'\").fetchone()[0]); "
              "print('lesson 0:', [x['name'] for x in L][0]); "
              "from groundwork import exitticket as m; "
              "h = m.ticket_html('{seed_concept}', '{seed_prompt}'); "
              "print('has action:', 'action=' in h, '| has method:', 'method=' in h)"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "One question, no grade.",
         "subtitle": "exitticket.py renders retrieval practice -- the form posts nowhere."},
    ],
}


def _js_escape(text: str) -> str:
    """Escape HTML for a single-quoted JS string inside beat JSON."""
    return (text.replace("\\", "\\\\").replace('"', '\\"')
            .replace("'", "\\\\'"))


def seed_db(db_path: str) -> dict:
    """Render byte-exact ticket HTML for a real fixture lesson name.

    Reads the fixture copy only (no row changes needed: lesson names
    already exist); loads groundwork/exitticket.py standalone so the
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
            names = [L.get("name", "") for L in lessons[:1]]
            if (names and names[0].strip()
                    and "'" not in names[0] and '"' not in names[0]):
                picked = (mid, names[0])
                break
        if not picked:
            return {"seeded": False, "reason": "need module with a lesson"}
        mid, concept = picked
        prompt = f"In one sentence, what does {concept} do?"
        mod = _load_exitticket()
        html_out = mod.ticket_html(concept, prompt)
        if ("id='exitticket'" not in html_out
                or "ungraded" not in html_out
                or concept not in html_out or prompt not in html_out):
            return {"seeded": False, "reason": "renderer output unexpected"}
        return {"seeded": True, "mid": mid, "concept": concept,
                "prompt": prompt, "typed": TYPED,
                "ticket_js": _js_escape(html_out)}
    finally:
        con.close()
