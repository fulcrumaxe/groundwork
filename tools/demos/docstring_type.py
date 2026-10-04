"""Feature demo: write-the-docstring exercises (docstring-type).

Full functionality: type-25 cards show a signature and grade the
written docstring against a keyword rubric (half the key points
passes). No type-25 card ships in the library DB, so seed_db plants
one -- same front/back/payload shape as gen_docstring -- as the sole
due card; the /due beat frames its explanation box, then a second
beat answers it natively and polls the "Covered n/n" verdict.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-docstring-25"

SCENARIO = {
    "id": "docstring-type",
    "kind": "feature",
    "batch": 1,
    "item": "F-1",
    "title": "Write-the-docstring exercises",
    "blurb": "Docstring exercise cards render an explanation box. Answer one below.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Feature docstring-type",
         "title": "Write-the-docstring exercises",
         "subtitle": "Signature on the front, explanation box below -- rubric-graded."},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: cover half the key points or miss.",
         "commands": [
             ["python3", "-c",
              "from groundwork import exercises as m; "
              "print(m.grade({'type': 25, 'payload': "
              "{'rubric': ['total', 'items', 'return']}}, "
              "'total the items and return the sum'))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "article#card-{seed_card_id} h3",
         "caption": "The docstring card: signature prompt plus the explanation box.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector('textarea[name=answer]') && "
                      "f.textContent.includes('Submit explanation'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 14,
         "url_path": "/due",
         "caption": "Answer from the rubric words -- the verdict counts key points.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector('textarea[name=answer]'); "
                "if (!ta) return 'no-textarea'; ta.value = '{seed_answer}'; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Covered",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Covered')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Half the points passes.",
         "subtitle": "gen_docstring builds the rubric; grade() counts coverage."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-25 card as the sole due card in the fixture.

    Mirrors gen_docstring's shape (signature front, rubric payload);
    everything else is pushed to 2030 so queue ordering cannot bury
    the planted card and it lands first under #up-next. The answer
    covers every rubric word, so the verdict reads "Covered 3/3".
    """
    con = sqlite3.connect(db_path)
    try:
        concept = con.execute(
            "SELECT id, name FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not concept:
            return {"seeded": False, "reason": "no concepts"}
        cname = "".join(
            ch for ch in (concept[1] or "concept") if ch not in "'\"\\`")
        cname = cname.strip() or "concept"
        rubric = [cname, "param", "return"]
        answer = f"{cname} takes param and returns the result."
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        con.execute("DELETE FROM reviews WHERE card_id=?", (CARD_ID,))
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload, due)"
            " VALUES(?, ?, '25', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, concept[0],
             f"Write the docstring for `{cname}` from its signature "
             "alone -- purpose, parameters, what it returns.\n"
             f"```python\ndef {cname}(param):\n```",
             f"Documented: {', '.join(rubric)}.",
             json.dumps({"rubric": rubric,
                         "signature": f"def {cname}(param):",
                         "grounded": True})))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID, "concept": cname,
                "answer": answer}
    finally:
        con.close()
