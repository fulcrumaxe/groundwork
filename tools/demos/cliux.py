"""Feature demo: CLI UX review (F-34, type 57).

Full behavior: read a realistic --help output containing exactly
ONE planted usability flaw (five-category taxonomy) and name the
flaw category -- exact match after case/separator normalization.
seed_db plants a static destructive-default card (found mode,
generate() bytes) as the sole due card; /due names it and polls
the exact-category verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-cliux-57"

SCENARIO = {
    "id": "cliux",
    "kind": "feature",
    "batch": 10,
    "item": "F-34",
    "title": "CLI UX review",
    "blurb": "Spot the one usability flaw in a --help screen -- name its category.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Feature F-34",
         "title": "CLI UX review",
         "subtitle": "Five categories, one flaw -- the --help tells on itself."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-cliux",
         "caption": "Status homes the type: five flaw categories, exact-match grading.",
         "assert_js": "() => !!document.querySelector('#status-b10-cliux')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: the planted flaw passes in any case, a wrong category fails.",
         "commands": [
             ["python3", "-c",
              "from groundwork import cliux as m; "
              "ex = {'payload': {'flaw': 'destructive-default'}}; "
              "print(m.grade(ex, 'Destructive default without confirmation')['feedback']); "
              "print(m.grade(ex, 'no-examples')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The review card: the --help output on the front, your verdict below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"input[name='answer']\") && "
                      "document.body.innerText.includes('usability flaw'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Name the flaw -- the verdict checks the exact category.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const inp = f.querySelector(\"input[name='answer']\"); "
                "if (!inp) return 'no-input'; inp.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Correct: Destructive default without confirmation",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Correct: Destructive default without confirmation')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "One flaw, named.",
         "subtitle": "cliux.py grades the category -- exact, normalized, no dumps."},
    ],
}

FRONT = 'Study this --help output. It contains exactly ONE usability flaw. Reply with the flaw category (id or label).\nCategories:\n- inconsistent-flag-naming (Inconsistent flag naming)\n- missing-required-marking (Missing required-argument marking)\n- destructive-default (Destructive default without confirmation)\n- cryptic-error (Cryptic error message)\n- no-examples (No examples section)\n```text\nusage: deploy [--mode MODE] [--confirm] [--output DIR]\n\noptions:\n  --mode MODE   what to do: deploy or wipe (default: wipe)\n  --confirm     ask before applying changes\n  --output DIR  write the report to DIR (default: ./out)\n\nrequired: none. all options are optional.\n\nexamples:\n  deploy --mode deploy\n  deploy --mode wipe --confirm\n```'
BACK = 'Flaw: Destructive default without confirmation (destructive-default). The default mode wipes and confirmation is opt-in, so a bare run destroys data.'
PAYLOAD = {'help': 'usage: deploy [--mode MODE] [--confirm] [--output DIR]\n\noptions:\n  --mode MODE   what to do: deploy or wipe (default: wipe)\n  --confirm     ask before applying changes\n  --output DIR  write the report to DIR (default: ./out)\n\nrequired: none. all options are optional.\n\nexamples:\n  deploy --mode deploy\n  deploy --mode wipe --confirm', 'flaw': 'destructive-default', 'label': 'Destructive default without confirmation', 'mode': 'found', 'grounded': True}
ANSWER = "destructive-default"


def seed_db(db_path: str) -> dict:
    """Plant one type-57 card (generate() bytes) as the sole due card."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '57', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
