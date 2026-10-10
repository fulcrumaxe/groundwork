"""Improvement demo: ELI5 and tradeoff extremes (I-123).

Full behavior: a lesson carrying extreme data gains an ELI5 analogy
block above the level 1-4 tabs and a design-tradeoffs block below,
via lessons.render_levels; lessons without the data render
byte-identical. seed_db injects eli5/tradeoffs into one real lesson
(a non-B concept, so the legacy ELI5-first order films) of the
biggest module; beats show the Status home, the pure sidecar rule,
the real module lesson page, and the fixture proof.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3

SCENARIO = {
    "id": "levelextremes",
    "kind": "improvement",
    "batch": 20,
    "item": "I-123",
    "title": "ELI5 and tradeoff extremes",
    "blurb": "Explainers stretch both ways: an ELI5 analogy on top, design tradeoffs below.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Improvement I-123",
         "title": "ELI5 and tradeoff extremes",
         "subtitle": "Extreme levels wrap the standard tabs -- ELI5 above, tradeoffs below."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-levelextremes",
         "caption": "Status documents the sidecar: extremes render only when the lesson carries the data.",
         "assert_js": "() => !!document.querySelector('#status-b20-levelextremes') && "
                      "document.body.innerText.includes('piggy bank')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: rich lessons get both blocks; plain lessons get empty strings.",
         "commands": [
             ["python3", "-c",
              "from groundwork import levelextremes as m; "
              "rich = {'name': 'add', 'summary': 'add() totals two numbers.', "
              "'eli5': {'analogy': 'A piggy bank for twos.', 'takeaway': 'Defaults do the adding.'}, "
              "'tradeoffs': ['Inline the sum', 'Keep a running total', 'Use reduce', 'A fourth way']}; "
              "top, bottom = m.extreme_blocks(rich); "
              "print('rich:', 'extremes-eli5' in top, 'extremes-tradeoffs' in bottom); "
              "print('plain:', m.extreme_blocks({'name': 'add'})); "
              "print('alternatives capped at:', len(m.tradeoffs_for(rich)['alternatives']))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules/{seed_mid}#lesson-{seed_slug}",
         "focus": "#lesson-{seed_slug}",
         "caption": "The real lesson page: ELI5 analogy above the level tabs, tradeoffs below -- levels 1-4 untouched.",
         "assert_js": "() => { const s = document.querySelector('#lesson-{seed_slug}'); "
                      "if (!s) return false; const h = s.innerHTML; "
                      "const e = h.indexOf('extremes-eli5'); const t = h.indexOf('extremes-tradeoffs'); "
                      "return e > -1 && t > -1 && e < t; }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof in the fixture DB: the seeded lesson carries eli5 and tradeoffs keys.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3, json; "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "les = json.loads(con.execute(\"SELECT lessons FROM modules WHERE id='{seed_mid}'\").fetchone()[0]); "
              "hit = [l for l in les if l.get('name') == '{seed_name}'][0]; "
              "print('eli5:', sorted(hit['eli5'])); print('tradeoffs:', len(hit['tradeoffs']))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Both extremes, zero disruption.",
         "subtitle": "levelextremes.py rides render_levels -- no-data lessons stay byte-identical."},
    ],
}


def _slug(text) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(text or ""))
    return "-".join(filter(None, out.split("-"))) or "lesson"


def _variant_a(cid) -> bool:
    try:
        digest = hashlib.md5(str(cid or "").strip().encode("utf-8")).hexdigest()
        return int(digest, 16) % 2 == 0
    except Exception:
        return True


def seed_db(db_path: str) -> dict:
    """Inject eli5/tradeoffs into one rendered lesson of the biggest module."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT module_id FROM concepts GROUP BY module_id"
                          " ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
        if not row:
            row = con.execute("SELECT id FROM modules LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no modules"}
        mid = row[0]
        raw = con.execute("SELECT lessons FROM modules WHERE id=?",
                          (mid,)).fetchone()[0]
        try:
            lessons = json.loads(raw or "[]")
        except ValueError:
            return {"seeded": False, "reason": "bad lessons json"}
        lesson_map = {L.get("concept_id"): L for L in lessons
                      if isinstance(L, dict) and L.get("concept_id")}
        cands = []
        for (cid,) in con.execute("SELECT id FROM concepts WHERE module_id=?",
                                  (mid,)).fetchall():
            node = cid.split(":", 1)[1] if ":" in cid else cid
            lesson = lesson_map.get(node) or lesson_map.get(cid)
            if not lesson or not (lesson.get("summary") or "").strip():
                continue
            cands.append((cid, node, lesson))
        if not cands:
            return {"seeded": False, "reason": "no rendered lessons"}
        pick = next((c for c in cands if _variant_a(c[0])), cands[0])
        cid, node, lesson = pick
        name = lesson.get("name") or "this lesson"
        lesson["eli5"] = {"analogy": "Like a piggy bank that only takes twos.",
                          "takeaway": "Defaults do the adding."}
        lesson["tradeoffs"] = ["Inline the sum", "Keep a running total",
                               "Use reduce"]
        con.execute("UPDATE modules SET lessons=? WHERE id=?",
                    (json.dumps(lessons), mid))
        con.commit()
        return {"seeded": True, "mid": mid, "slug": _slug(node),
                "name": name}
    finally:
        con.close()
