"""Demo-video scenario: peer level hint (I-124).

Full behavior: lessons.render_levels appends a "Peers found X most
helpful" line beside the level tabs once opt-in votes reach a quorum
of three with a strict plurality; ties and thin counts render
nothing (byte-identical legacy output). The Status page carries a
live sample; the module page (no votes passed) shows the silent
fallback on the real caller path.
"""
from __future__ import annotations

import json
import sqlite3

SCENARIO = {
    "id": "peerhelp",
    "kind": "improvement",
    "batch": 20,
    "item": "I-124",
    "title": "Peer level hint",
    "blurb": "Tabs note which level peers found most helpful -- silent until quorum.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 20 - Improvement I-124",
         "title": "Peer level hint",
         "subtitle": "Opt-in peer votes name the most helpful level -- ties and thin counts stay silent."},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b20-peerhelp",
         "caption": "Status documents the hint with a live sample: Intermediate, 4 of 5 votes.",
         "assert_js": "() => document.body.innerText.includes('Peers found Intermediate most helpful')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule: quorum of 3 plus strict plurality -- thin counts and ties print empty.",
         "commands": [
             ["python3", "-c",
              "from groundwork import peerhelp as m; "
              "print(m.line_html([(3, True)] * 4 + [(2, True)])); "
              "print(repr(m.line_html([(1, True), (2, True)]))); "
              "print(repr(m.aggregate([(3, True)] * 2 + [(2, True)] * 2)))"],
         ]},
        {"type": "terminal", "duration": 8,
         "caption": "The real caller path: render_levels stays byte-identical until quorum, then shows the hint.",
         "commands": [
             ["python3", "-c",
              "from groundwork import lessons as L; "
              "les = {'concept_id': 'c', 'name': 'add', 'kind': 'function', 'file': 'calc.py', 'line': 1, "
              "'summary': 'add() totals two numbers.', 'docstring': '', 'callers': [], 'callees': [], "
              "'key_lines': '', 'source': 'def add(a, b): return a + b', 'how': ['Read the defaults.'], 'worked': None}; "
              "base = L.render_levels(les, 0.0, 0, 'auto', '/'); "
              "thin = L.render_levels(les, 0.0, 0, 'auto', '/', peer_votes=[(1, True)]); "
              "full = L.render_levels(les, 0.0, 0, 'auto', '/', peer_votes=[(3, True)] * 4 + [(2, True)]); "
              "print('silent until quorum:', thin == base and 'peerhelp' not in base); "
              "i = full.find('Peers found'); print(full[i:i + 70])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}#lesson-{seed_slug}",
         "focus": "#lesson-{seed_slug}",
         "caption": "The module page passes no votes, so the same path renders legacy bytes -- no hint.",
         "assert_js": "() => !document.querySelector('p.peerhelp') && "
                      "document.querySelector('#lesson-{seed_slug}').innerText.includes('Explain it')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Silent until quorum.",
         "subtitle": "peerhelp.py counts only opt-in votes on the lesson path -- ties render nothing."},
    ],
}


def _slug(text) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(text or ""))
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Point the module-page beat at a rendered lesson section.

    peerhelp is db-free (votes arrive as a render_levels argument, no
    table), so there is nothing to plant: return the first module id
    with a concept-backed lesson, guaranteeing the filmed section
    runs the real caller path (explainer tabs) while staying silent.
    """
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute("SELECT id, lessons FROM modules").fetchall()
        for mid, lessons in rows:
            try:
                parsed = json.loads(lessons or "[]")
            except ValueError:
                continue
            nodes = {r[0].split(":", 1)[1] if ":" in r[0] else r[0]
                     for r in con.execute("SELECT id FROM concepts"
                                          " WHERE module_id=?", (mid,))}
            hit = next((L for L in parsed
                        if isinstance(L, dict) and L.get("concept_id") in nodes
                        and (L.get("summary") or "").strip()), None)
            if hit is not None:
                return {"seeded": True, "mid": mid,
                        "slug": _slug(hit["concept_id"])}
        return {"seeded": False, "reason": "no lessons"}
    finally:
        con.close()
