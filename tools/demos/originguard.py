"""Improvement demo: origin allowlist guard (I-34).

Full behavior: originguard.safe_origin() allowlists ?origin
back-links to known app pages; the Due queue embeds a hidden
origin in every review form and the verdict links back to it.
seed_db deals one textarea card + a module id; Status homes the
guard, terminal runs the verdict table, /due shows the hidden
origin, then a native submit round-trips to the module page.
"""
from __future__ import annotations

import re
import sqlite3

TEXTAREA_ETYPES = ("5", "6", "24", "25", "82", "83", "84", "85",
                   "86", "90")


def _anchor(card_id: str) -> str:
    """Mirror scrollpos.card_anchor: the <article> id for a card."""
    slug = "".join(re.findall(r"[A-Za-z0-9_-]+", card_id.strip()))[:48]
    return "card-%s" % (slug or "unknown")

SCENARIO = {
    "id": "originguard",
    "kind": "improvement",
    "batch": 8,
    "item": "I-34",
    "title": "Origin allowlist guard",
    "blurb": ("?origin back-links only return to known app pages -- "
              "open-redirect shapes fall back to the queue."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Improvement I-34",
         "title": "Origin allowlist guard",
         "subtitle": ("Back-links return to known pages only -- redirect "
                      "shapes fall back to the queue.")},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b8-originguard",
         "caption": ("Status homes the guard: hidden origins, allowlisted "
                     "targets, safe fallback."),
         "assert_js": "() => !!document.querySelector('#status-b8-originguard')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": ("The verdicts in one line: attacks fall home, real "
                     "pages pass through."),
         "commands": [
             ["python3", "-c",
              "from groundwork import originguard as m; "
              "print(m.safe_origin('//evil/x'), m.safe_origin('javascript:alert(1)'), "
              "m.safe_origin('/api/due.json'), m.safe_origin('/no-such-page')); "
              "print(m.safe_origin('/due'), m.safe_origin('/modules/abc'), "
              "m.safe_origin('/due?mode=one'), m.safe_origin('/due#card-c9'))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#{seed_anchor}",
         "caption": "The Due queue embeds a hidden origin in every review form.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "const o = f && f.querySelector(\"input[name='origin']\"); "
                      "return !!o && o.value === '/due'; }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "caption": ("Submit with a module-page origin -- the verdict links "
                     "back to exactly that page."),
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = 'originguard probe'; "
                "const o = f.querySelector(\"input[name='origin']\"); "
                "if (o) o.value = '/modules/{seed_mid}'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Continue where you left off",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { const a = [...document.querySelectorAll('a.btn')].find("
                      "x => x.textContent.includes('Continue where you left off')); "
                      "return !!a && a.getAttribute('href').startsWith('/modules/{seed_mid}#card-'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "Back-links you can trust.",
         "subtitle": ("originguard.py allowlists the return -- every future "
                      "page gets the test.")},
    ],
}


def seed_db(db_path: str) -> dict:
    """Deal one textarea card due-first; return a module id for origin."""
    con = sqlite3.connect(db_path)
    try:
        marks = ",".join("?" * len(TEXTAREA_ETYPES))
        row = con.execute(
            "SELECT id FROM cards"
            f" WHERE exercise_type IN ({marks})"
            " ORDER BY due LIMIT 1", TEXTAREA_ETYPES).fetchone()
        if not row:
            row = con.execute(
                "SELECT id FROM cards ORDER BY due LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no cards"}
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (row[0],))
        con.execute("DELETE FROM reviews WHERE card_id=?", (row[0],))
        mod = con.execute("SELECT id FROM modules LIMIT 1").fetchone()
        if not mod:
            return {"seeded": False, "reason": "no modules"}
        con.commit()
        return {"seeded": True, "card_id": row[0], "mid": mod[0],
                "anchor": _anchor(row[0])}
    finally:
        con.close()
