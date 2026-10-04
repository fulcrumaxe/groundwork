"""Feature demo: containerize it (F-41, type 64).

Full behavior: write a complete Dockerfile for a small Python
service -- a static build gate checks pinned FROM, WORKDIR, COPY,
matching EXPOSE, exec-form CMD, and USER, and forbids ADD-for-files,
:latest, and ENV secret literals. No partial credit: the gate ships
or it does not. seed_db plants a static port-8714 card (generate()
bytes) as the sole due card; the type-64 textarea takes the
Dockerfile and polls the green gate.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = "demo-containerize-64"

SCENARIO = {
    "id": "containerize",
    "kind": "feature",
    "batch": 10,
    "item": "F-41",
    "title": "Containerize it",
    "blurb": "Write a Dockerfile for a small service -- static build gate, no partial credit.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Feature F-41",
         "title": "Containerize it",
         "subtitle": "The gate ships or it does not -- no partial credit."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-containerize",
         "caption": "Status homes the type: six required points, three forbidden, all or nothing.",
         "assert_js": "() => !!document.querySelector('#status-b10-containerize')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: pinned base ships, :latest fails the gate.",
         "commands": [
             ["python3", "-c",
              "from groundwork import containerize as m; "
              "ex = {'payload': {'port': 8714}}; "
              "good = 'FROM python:3.12-slim\\nWORKDIR /app\\nCOPY . .\\nEXPOSE 8714\\nUSER appuser\\nCMD [\"python\", \"app.py\"]'; "
              "bad = 'FROM python:latest\\nWORKDIR /app\\nCOPY . .\\nEXPOSE 8714\\nUSER appuser\\nCMD [\"python\", \"app.py\"]'; "
              "print(m.grade(ex, good)['feedback']); "
              "print(m.grade(ex, bad)['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The container card: entrypoint, port 8714, and the disclosed checklist.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"textarea[name='answer']\") && "
                      "document.body.innerText.includes('complete Dockerfile'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 13,
         "url_path": "/due",
         "caption": "Submit the Dockerfile -- the gate checks every point at once.",
         "js": ["() => { const f = document.querySelector(\"form[action='/cards/{seed_card_id}/review']\"); "
                "if (!f) return 'seed-form-missing'; "
                "const ta = f.querySelector(\"textarea[name='answer']\"); "
                "if (!ta) return 'no-textarea'; ta.value = {seed_answer_js}; "
                "const conf = f.querySelector(\"input[name='confidence'][value='4']\"); "
                "if (conf) conf.checked = true; "
                "f.submit(); return 'submitted'; }"],
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Build gate green",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('.verdict-stamp') && "
                      "document.body.innerText.includes('Build gate green')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "Gate green.",
         "subtitle": "containerize.py gates the text -- pinned, copied, exposed, launched."},
    ],
}

FRONT = 'Containerize the `checkout` service: a Python app with entrypoint `app.py` listening on port 8714.\nWrite a complete Dockerfile with: a pinned base image (never `:latest`), WORKDIR, COPY (not ADD) for local files, EXPOSE 8714, exec-form CMD/ENTRYPOINT, and a non-root USER.\nNever bake secrets into ENV with literal values.'
BACK = 'Model Dockerfile:\nFROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nEXPOSE 8714\nUSER appuser\nCMD ["python", "app.py"]'
PAYLOAD = {'entrypoint': 'app.py', 'port': 8714, 'service': 'checkout', 'grounded': True}
GOOD = 'FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nEXPOSE 8714\nUSER appuser\nCMD ["python", "app.py"]'


def seed_db(db_path: str) -> dict:
    """Plant one type-64 card (generate() bytes) as the sole due card."""
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
            " VALUES(?, ?, '64', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID,
                "answer_js": json.dumps(json.dumps(GOOD))[1:-1]}
    finally:
        con.close()
