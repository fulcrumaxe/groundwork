"""Improvement demo: pass/fail verdict stamps (I-77).

Full behavior: result verdicts render as rotated bordered stamps
whose labels stay plain readable words (PASS/FAIL -- never emoji);
the same stamp_html marks History attempts and lesson submissions.
seed_db plants one textarea card as the sole due card plus one
passing and one failing review; Chrome proves the Status samples,
a live Due submit landing on a stamped verdict, and the stamped
History list.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "verdicts",
    "kind": "improvement",
    "batch": 12,
    "item": "I-77",
    "title": "Verdict stamps",
    "blurb": "PASS or FAIL in rotated bordered type -- plain words, never emoji.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Improvement I-77",
         "title": "Verdict stamps",
         "subtitle": "PASS or FAIL in rotated bordered type -- plain words, never emoji."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b12-verdicts",
         "caption": "Status shows live PASS/FAIL samples -- text, never emoji.",
         "assert_js": "() => { const h = document.querySelector('#status-b12-verdicts'); "
                      "if (!h) return 'no-anchor'; const p = h.nextElementSibling; "
                      "return (p && p.querySelector('.stamp-pass') && "
                      "p.querySelector('.stamp-fail')) ? 'both-stamps' : 'missing'; }",
         "assert_want": "both-stamps"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: labels are words, the stamp look is pure CSS.",
         "commands": [
             ["python3", "-c",
              "from groundwork import verdicts as m; "
              "print(m.verdict_stamp(True), '|', m.verdict_stamp(None)); "
              "css = m.verdicts_css(); "
              "print('tokens:', 'var(--pass)' in css, 'var(--fail)' in css, "
              "'| rotate:', 'rotate(' in css.replace(' ', ''))"],
         ]},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "focus": "p.verdict",
         "caption": "Submit a review -- the verdict stamps PASS or FAIL in bordered type.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = 'Lyon'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Next review:",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => { const s = document.querySelector('p.verdict .verdict-stamp'); "
                      "return !!s && /^(PASS|FAIL)$/.test(s.textContent.trim()); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/reviews",
         "focus": "#attempts",
         "caption": "History stamps every attempt -- the same readable words.",
         "assert_js": "() => !!document.querySelector('.stamp-pass') && "
                      "!!document.querySelector('.stamp-fail')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Stamped, still readable.",
         "subtitle": "verdicts.py marks results, history, lessons -- CSS off, words stay."},
    ],
}


def seed_db(db_path: str) -> dict:
    """One textarea card due-now plus a passing and a failing review.

    The submit beat targets the due card's form by exact action URL
    and native-submits (f.submit skips the collapse interception,
    landing on the full verdict page like no-JS). The two planted
    reviews are the newest rows by id, so the History beat's attempt
    list opens with one PASS stamp and one FAIL stamp.
    """
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id FROM cards WHERE exercise_type IN "
            "('5','6','24','25','82','83','84','85','86','90')"
            " ORDER BY due LIMIT 1").fetchone()
        if not card:
            card = con.execute(
                "SELECT id FROM cards ORDER BY due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid = card[0]
        others = con.execute(
            "SELECT id FROM cards WHERE id != ? ORDER BY due LIMIT 2",
            (cid,)).fetchall()
        if len(others) < 2:
            return {"seeded": False, "reason": "need two more cards"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (cid,))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, submission)"
            " VALUES(?, 5, 4, 'verdicts seed: passing answer')",
            (others[0][0],))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, submission)"
            " VALUES(?, 1, 2, 'verdicts seed: failing answer')",
            (others[1][0],))
        con.commit()
        return {"seeded": True, "card_id": cid,
                "pass_card": others[0][0], "fail_card": others[1][0]}
    finally:
        con.close()
