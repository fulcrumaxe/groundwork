"""Improvement demo: optimistic UI on review submit (I-82).

Full behavior: submitting a Due card review shows nothing until the
round trip resolves, inviting double clicks -- so the submit guard
disables the form's buttons and appends a spinner plus a Working...
status line, while the submit itself proceeds untouched (grading,
collapse-fetch, and draft-clear all still run). The spinner beat
dispatches a synthetic submit event with fetch held hung (the
in-flight-latency state the guard exists for: listeners fire, no
navigation happens, collapse waits on the hung request); the verdict
beat then native-submits for real to prove grading still lands.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "optimistic",
    "kind": "improvement",
    "batch": 12,
    "item": "I-82",
    "title": "Optimistic submit",
    "blurb": "Submit a card and its buttons lock with a spinner -- no double grades.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Improvement I-82",
         "title": "Optimistic submit",
         "subtitle": "Latency never invites a double click -- lock, spin, Working..."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b12-optimistic",
         "caption": "Status documents the guard: lock buttons, spin 250ms, submit untouched.",
         "assert_js": "() => !!document.querySelector('#status-b12-optimistic')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: guard the review forms, hijack nothing, spin 250ms.",
         "commands": [
             ["python3", "-c",
              "from groundwork import optimistic as m; "
              "j = m.optimistic_js(); "
              "print('targets review forms:', \"action$='/review'\" in j); "
              "print('hijacks submit:', any(k in j for k in "
              "('preventDefault', 'fetch(', 'localStorage'))); "
              "print('idempotent:', j.count('gw-spinner') >= 1)"],
             ["python3", "-c",
              "import re; from groundwork import optimistic as m; "
              "c = m.optimistic_css(); "
              "print('spin:', re.findall(r'\\d+ms', c)); "
              "print('reduced-motion:', 'prefers-reduced-motion' in c); "
              "print('style tags:', '<style' in c.lower())"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "focus": "form[action='/cards/{seed_card_id}/review']",
         "caption": "Grade in flight: buttons lock, the spinner spins, Working... shows.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (ta) { ta.textContent = 'demo answer, still grading'; ta.value = 'demo answer, still grading'; } "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) { Array.prototype.forEach.call(f.querySelectorAll(\"input[name='confidence']\"), function(i){i.removeAttribute('checked');}); conf.checked = true; conf.setAttribute('checked', ''); } "
                "window.fetch = function(){return new Promise(function(){});}; "
                "f.dispatchEvent(new Event('submit')); "
                "const sp = !!f.querySelector('.gw-spinner'); "
                "const st = f.querySelector('.gw-status'); "
                "const dis = f.querySelectorAll('button[disabled]').length; "
                "return 'spinner=' + sp + ' status=' + (st ? st.textContent : 'none') + ' disabled=' + dis; }"],
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && f.querySelector('textarea[name=answer]').value.includes('still grading') && "
                      "!!f.querySelector('.gw-spinner') && "
                      "f.querySelector('.gw-status').textContent === 'Working...' && "
                      "f.querySelector('button').disabled; }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The submit itself is untouched -- grading lands on the verdict page.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = 'demo answer, graded for real'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Calibration banked",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('p.verdict') && "
                      "document.body.innerText.includes('Calibration banked')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Click once, trust it.",
         "subtitle": "optimistic.py guards the wait -- grading runs as today."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Force one textarea-type card due-now for the submit beats.

    The spinner beat fills the real answer field and the verdict
    beat native-submits it (f.submit skips the collapse fetch and
    lands on the full verdict page like no-JS); both target this
    card's form by exact action URL.
    """
    con = sqlite3.connect(db_path)
    try:
        card = con.execute(
            "SELECT id FROM cards WHERE exercise_type IN "
            "('5','6','24','25','82','83','84','85','86','90','26','27','28',"
            "'29','31','32','33','34','35','37','38','39','40')"
            " ORDER BY due LIMIT 1").fetchone()
        if not card:
            card = con.execute(
                "SELECT id FROM cards ORDER BY due LIMIT 1").fetchone()
        if not card:
            return {"seeded": False, "reason": "no cards"}
        cid = card[0]
        con.execute("UPDATE cards SET due='2000-01-01T00:00:00Z' WHERE id=?",
                    (cid,))
        con.commit()
        return {"seeded": True, "card_id": cid}
    finally:
        con.close()
