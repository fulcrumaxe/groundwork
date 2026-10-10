"""Improvement demo: calibration-aware levels (I-122).

Full behavior: auto-level weighs recent calibration, not just
mastery -- an overconfident streak steps one rung down on the
lesson rendering path. seed_db sets one lesson-backed concept to
mastery 0.9 with five confident-fail reviews; the Due and module
beats film Intermediate where legacy placement said Expert.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone

_ANCHOR_OK = re.compile(r"[A-Za-z0-9_-]+")

SCENARIO = {
    "id": "explcalib",
    "kind": "improvement",
    "batch": 20,
    "item": "I-122",
    "title": "Levels that read your calibration",
    "blurb": "Auto-level now weighs recent calibration, not just mastery.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Improvement I-122",
         "title": "Levels that read your calibration",
         "subtitle": "Confident fails step a rung down -- shy accuracy steps up."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-explcalib",
         "caption": "Status documents the nudge: gap over +0.20 steps one rung down.",
         "assert_js": "() => !!document.querySelector('#status-b20-explcalib') && "
                      "document.body.innerText.includes('one rung down')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Pure placement: mastery 0.9 says Expert; the overconfident tail says Intermediate.",
         "commands": [
             ["python3", "-c",
              "from groundwork import explcalib as m; "
              "over = [(1, 5)] * 5; "
              "print('gap:', round(m.recent_gap(over), 2)); "
              "print('no data:', m.pick_level(0.9, 5, None)); "
              "print('overconfident:', m.pick_level(0.9, 5, over)); "
              "print('shy-accurate:', m.pick_level(0.5, 5, [(4, 1)] * 5))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "focus": "#{seed_anchor} details[data-gw-remember]",
         "caption": "The Due explainer opens on Intermediate -- calibration overruled mastery 0.9.",
         "js": ["() => { const d = document.querySelector(\"#{seed_anchor} details[data-gw-remember]\"); "
                "if (!d) return 'panel-missing'; d.open = true; return 'opened'; }"],
         "assert_js": "() => { const h4 = [...document.querySelectorAll('h4')].map(h => h.innerText.trim()); "
                      "return h4.includes('Intermediate') && !h4.includes('Expert'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_mid}#lesson-{seed_slug}",
         "focus": "#lesson-{seed_slug}",
         "caption": "The module page agrees: merged history places the same lesson at Intermediate.",
         "assert_js": "() => { const s = document.querySelector('#lesson-{seed_slug}'); "
                      "if (!s) return false; const h4 = [...s.querySelectorAll('h4')].map(h => h.innerText.trim()); "
                      "return h4.includes('Intermediate') && !h4.includes('Expert'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "Proof in the fixture: mastery 0.9 plus five confident fails on the seeded card.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "cid = con.execute(\"SELECT concept_id FROM cards WHERE id='{seed_card_id}'\").fetchone()[0]; "
              "print('mastery:', con.execute('SELECT mastery FROM concepts WHERE id=?', (cid,)).fetchone()[0]); "
              "print('tail:', con.execute('SELECT grade, confidence FROM reviews WHERE card_id=? ORDER BY id', ('{seed_card_id}',)).fetchall())"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Placed by evidence, not ego.",
         "subtitle": "explcalib.py tails the last five -- no rows keeps legacy placement."},
    ],
}


def _slug(text) -> str:
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(text or ""))
    return "-".join(filter(None, out.split("-"))) or "lesson"


def seed_db(db_path: str) -> dict:
    """Mastery 0.9 + five confident fails on one lesson-backed card."""
    con = sqlite3.connect(db_path)
    try:
        mods = con.execute("SELECT id, lessons FROM modules").fetchall()
        target = None
        for mid, raw in mods:
            try:
                lessons = {L["concept_id"]: L for L in json.loads(raw or "[]")}
            except (ValueError, KeyError):
                continue
            if not lessons:
                continue
            for (cid,) in con.execute("SELECT id FROM concepts WHERE module_id=?",
                                      (mid,)).fetchall():
                node = cid.split(":", 1)[1] if ":" in cid else cid
                if node not in lessons:
                    continue
                card = con.execute("SELECT id FROM cards WHERE concept_id=?"
                                   " ORDER BY rowid LIMIT 1", (cid,)).fetchone()
                if card:
                    target = (mid, cid, node, card[0])
                    break
            if target:
                break
        if not target:
            return {"seeded": False, "reason": "no lesson-backed card"}
        mid, cid, node, card_id = target
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (card_id,))
        con.execute("UPDATE concepts SET mastery=0.9 WHERE id=?", (cid,))
        con.execute("DELETE FROM reviews WHERE card_id=?", (card_id,))
        now = datetime.now(timezone.utc)
        for i in range(5):
            stamp = (now - timedelta(days=5 - i)).strftime("%Y-%m-%dT%H:%M:%SZ")
            con.execute("INSERT INTO reviews(card_id, grade, confidence,"
                        " reviewed_at, submission) VALUES(?, 1, 5, ?, 'calib seed')",
                        (card_id, stamp))
        con.commit()
        slug = "".join(_ANCHOR_OK.findall(card_id.strip()))[:48] or "unknown"
        return {"seeded": True, "card_id": card_id, "mid": mid,
                "slug": _slug(node), "anchor": f"card-{slug}"}
    finally:
        con.close()
