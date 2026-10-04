"""Improvement demo: confidence pills (Batch 1).

Full functionality: every answer form carries five 1-5 confidence radios
(the segmented confslider control: Unsure/Shaky/OK/Solid/Sure), posted as
the same 'confidence' field the calibration coach reads; the lead Due
card carries the #confidence tour anchor. seed_db forces a write-the-
signature card due-first with its known expected answer; the beat answers
it correctly at confidence 5, and History banks grade 5/5, confidence 5/5.
"""
from __future__ import annotations

import base64
import json
import sqlite3

SCENARIO = {
    "id": "confidence-pills",
    "kind": "improvement",
    "batch": 1,
    "item": "I-64",
    "title": "Confidence pills",
    "blurb": "Rate 1–5 confidence with every answer; powers the calibration coach.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Improvement confidence-pills",
         "title": "Confidence pills",
         "subtitle": "Rate 1-5 confidence with every answer."},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#confidence",
         "caption": "Five pills, Unsure to Sure, riding on every answer form.",
         "assert_js": "() => String(document.querySelectorAll("
                      "\"#confidence input[name='confidence']\").length)",
         "assert_want": "5"},
        {"type": "terminal", "duration": 6,
         "caption": "One renderer, five radios, same posted field the coach reads.",
         "commands": [
             ["python3", "-c",
              "from groundwork import confslider as m; "
              "print('labels:', ' / '.join(m.LABELS)); "
              "print('radios:', m.slider_html(5).count(\"type='radio'\"))"],
         ]},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Answer right at confidence 5: the verdict confirms the grade.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector('input[name=answer]'); "
                "if (!inp) return 'no-answer-input'; "
                "inp.value = atob('{seed_expected_b64}'); "
                "const conf = f.querySelector(\"input[name='confidence'][value='5']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Next review:",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => document.body.innerText.includes('Signature matches.')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/reviews",
         "focus": "#attempts",
         "caption": "History banks the rating: grade 5 of 5, confidence 5 of 5.",
         "assert_js": "() => document.body.innerText.includes('grade 5/5, confidence 5/5')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Bets the coach can read.",
         "subtitle": "Honest ratings power the calibration coach."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One write-the-signature card due-first with its expected answer.

    Exercise type 3 grades by normalized match against the payload
    signature, so returning the signature (base64: signatures contain
    quotes that would break raw JS tokens) lets the beat answer exactly
    right at confidence 5. The beat targets this card's form by exact
    action URL and native-submits (f.submit skips the collapse
    interception, landing on the full verdict page like no-JS).
    """
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id, payload FROM cards"
            " WHERE exercise_type='3'").fetchall()
        if not rows:
            return {"seeded": False, "reason": "no signature cards"}
        pick = None
        for cid, payload in rows:
            try:
                sig = (json.loads(payload or "{}") or {}).get("signature", "")
            except (TypeError, ValueError):
                sig = ""
            if isinstance(sig, str) and sig.strip():
                pick = (cid, sig)
                break
        if not pick:
            return {"seeded": False, "reason": "no signature payload"}
        cid, sig = pick
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (cid,))
        con.commit()
        b64 = base64.b64encode(sig.encode("utf-8")).decode("ascii")
        return {"seeded": True, "card_id": cid, "expected_b64": b64}
    finally:
        con.close()
