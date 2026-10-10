"""Feature demo: contract authoring (F-86, type 90).

Full behavior: author requires/ensures one-liners for a real function;
both halves must accept every measured case and reject the planted
mutant. seed_db plants the generated type-90 shout card as the sole
due card; the /due beats film the two-line textarea widget and submit
the passing contract live, polling the Contract-holds verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-b20-contracts"
REQ = "(x != 0 and x != 1 and x != 2 and x != -1 and x != 3.5 and x != None)"
ENS = "(out == 'BOB!' or out == '!' or out == 'ANN!' or out == 'X!')"
ANSWER = REQ + "\n" + ENS
FRONT = (
    "Author the contract for `shout`.\n"
    "```python\n"
    "def shout(text):\n"
    "    return text.upper() + '!'\n"
    "```\n"
    "Measured:\n"
    "shout('bob') -> 'BOB!'\n"
    "shout('') -> '!'\n"
    "shout('ann') -> 'ANN!'\n"
    "shout('x') -> 'X!'\n"
    "Line 1: requires(x) -- when may it be called?\n"
    "Line 2: ensures(x, out) -- what holds after?"
)
BACK = (
    "requires: " + REQ + " -- accepts the measured inputs.\n"
    "ensures: " + ENS + " -- accepts the measured pairs, rejects the mutant."
)
PAYLOAD = {
    "valid": [["bob", "BOB!"], ["", "!"], ["ann", "ANN!"], ["x", "X!"]],
    "invalid": [0, 1, 2, -1, 3.5, None],
    "mutant": ["bob", "BOB!!"],
    "reference": ANSWER,
    "grounded": True,
}

SCENARIO = {
    "id": "contracts",
    "kind": "feature",
    "batch": 20,
    "item": "F-86",
    "title": "Contract authoring",
    "blurb": "Write requires/ensures one-liners for a real function; measured tests grade both halves live.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 20 - Feature F-86",
         "title": "Contract authoring",
         "subtitle": "Two one-liners -- requires(x), ensures(x, out) -- graded against measured tests."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b20-contracts",
         "caption": "Status homes the type: probe pairs measured, one mutant planted, both halves must pass.",
         "assert_js": "() => !!document.querySelector('#status-b20-contracts')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Pure logic: the reference contract holds; a trivial True/True keeps the mutant and fails.",
         "commands": [
             ["python3", "-c",
              "import types; from groundwork import contracts as m; "
              "c = types.SimpleNamespace(name='shout', node_id='app.py:shout', kind='function', file='app.py', line=1); "
              "card = m.generate('ex1', c, ['def shout(text):', '    return text.upper() + \\'!\\''], {}); "
              "ref = card['payload']['reference']; "
              "print('measured:', len(card['payload']['valid']), 'pairs + mutant', card['payload']['mutant']); "
              "print('reference:', m.grade(card, ref)['feedback']); "
              "print('trivial:', m.grade(card, 'True\\nTrue')['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#contract-front",
         "caption": "The contract card: measured pairs on top, a two-line textarea for requires then ensures.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; const p = f.previousElementSibling; "
                "if (!p) return 'no-front'; p.id = 'contract-front'; return 'tagged'; }"],
         "assert_js": "() => { const t = document.querySelector('#contract-front'); "
                      "const ta = document.querySelector(\"form[action='/cards/{seed_card_id}/review'] textarea[name=answer]\"); "
                      "return !!t && t.innerText.includes('Author the contract') && "
                      "!!ta && ta.placeholder.includes('requires(x)'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "caption": "Submit the contract live -- both halves hold, measured cases and mutant agree.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Contract holds",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Contract holds')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 20",
         "title": "Design by contract, drilled.",
         "subtitle": "contracts.py measures, mutates, and grades -- both halves must pass."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant the generated type-90 shout card as the sole due card.

    Hardcoded pipeline shape (no groundwork import: only tools/ is on
    sys.path at seed time). The /due beats target this card's form by
    exact action URL and native-submit (f.submit skips the collapse
    interception, landing on the full verdict page like no-JS).
    """
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
            " VALUES(?, ?, '90', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(ANSWER))[1:-1]}
    finally:
        con.close()
