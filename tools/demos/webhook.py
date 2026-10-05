"""Feature demo: webhook verification exercise (F-49, type 72).

Full behavior: the learner implements verify_signature(secret, body,
timestamp, signature, now) -- recompute HMAC-SHA256 over
timestamp.body, constant-time compare, enforce a 300s replay window.
The grader runs four fixed vectors: valid passes; tampered body,
wrong secret, and replayed timestamp all rejected. No partial credit.
"""
from __future__ import annotations

import json
import sqlite3

CARD_ID = 'demo-webhook-72'
FRONT = 'Verify this HMAC-signed webhook delivery. Shared-secret fixture `ab140132\u2026` (full secret travels with the vectors, never in your reply). Write `verify_signature(secret, body, timestamp, signature, now) -> bool`: recompute HMAC-SHA256 over `f"{timestamp}.{body}"`, compare in constant time, and reject timestamps outside a 300s window.\nSample body: `{"event":"push"}` (`hmac` and `hashlib` are pre-imported).'
BACK = 'def verify_signature(secret, body, timestamp, signature, now):\n    try:\n        ts = int(timestamp)\n        moment = int(now)\n    except (TypeError, ValueError):\n        return False\n    if abs(moment - ts) > 300:\n        return False\n    expected = hmac.new(str(secret).encode(),\n                        f"{ts}.{body}".encode(),\n                        hashlib.sha256).hexdigest()\n    try:\n        return hmac.compare_digest(expected, str(signature))\n    except (TypeError, ValueError):\n        return False\n'
PAYLOAD = {'secret': 'ab1401327efacf8609bd5fd9099d90a3', 'body': '{"event":"push"}', 'ts': 1700484081, 'now': 1700484081, 'valid': {'ts': 1700484081, 'sig': 'faf2c1afdf06abaf1a7d5697ff3b48807f6cf8e1e46e0e0dbce7e453ee3bed9b'}, 'tampered': {'body': '{"event":"push"} ', 'ts': 1700484081, 'sig': 'faf2c1afdf06abaf1a7d5697ff3b48807f6cf8e1e46e0e0dbce7e453ee3bed9b'}, 'wrong_secret': {'ts': 1700484081, 'sig': 'e46c6df5bc8d9279192722700a4bacc298d0f1b5721f944ad6ec74259786a399'}, 'replay': {'ts': 1700483181, 'sig': 'faf2c1afdf06abaf1a7d5697ff3b48807f6cf8e1e46e0e0dbce7e453ee3bed9b'}, 'tolerance': 300, 'reference': 'def verify_signature(secret, body, timestamp, signature, now):\n    try:\n        ts = int(timestamp)\n        moment = int(now)\n    except (TypeError, ValueError):\n        return False\n    if abs(moment - ts) > 300:\n        return False\n    expected = hmac.new(str(secret).encode(),\n                        f"{ts}.{body}".encode(),\n                        hashlib.sha256).hexdigest()\n    try:\n        return hmac.compare_digest(expected, str(signature))\n    except (TypeError, ValueError):\n        return False\n', 'grounded': True}
ANSWER = 'def verify_signature(secret, body, timestamp, signature, now):\n    try:\n        ts = int(timestamp)\n        moment = int(now)\n    except (TypeError, ValueError):\n        return False\n    if abs(moment - ts) > 300:\n        return False\n    expected = hmac.new(str(secret).encode(),\n                        f"{ts}.{body}".encode(),\n                        hashlib.sha256).hexdigest()\n    try:\n        return hmac.compare_digest(expected, str(signature))\n    except (TypeError, ValueError):\n        return False\n'

SCENARIO = {
    "id": "webhook",
    "kind": "feature",
    "batch": 11,
    "item": "F-49",
    "title": "Webhook verify",
    "blurb": "Sign, compare, window -- four vectors, zero forgeries.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Feature F-49",
         "title": "Webhook verify",
         "subtitle": "One forgery admitted is total failure."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-webhook",
         "caption": "Status homes the type: HMAC, constant-time, 300s replay window.",
         "assert_js": "() => !!document.querySelector('#status-b11-webhook')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: the reference clears all vectors, return-True admits forgeries.",
         "commands": [
             ["python3", "-c",
              "import sys; sys.path.insert(0, 'tools'); "
              "from demos.webhook import PAYLOAD, ANSWER; "
              "from groundwork import webhook as m; "
              "ex = {'payload': PAYLOAD}; "
              "ok = m.grade(ex, ANSWER); "
              "bad = m.grade(ex, 'def verify_signature(secret, body, timestamp, signature, now):\\n    return True\\n'); "
              "print('good:', ok['pass'], '-', ok['feedback']); "
              "print('bad:', bad['pass'], '-', bad['feedback'])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "focus": "#card-{seed_card_id}",
         "caption": "The webhook card: signed delivery on top, verifier below.",
         "assert_js": "() => { const f = document.querySelector("
                      "\"form[action='/cards/{seed_card_id}/review']\"); "
                      "return !!f && !!f.querySelector(\"[name='answer']\") && "
                      "document.body.innerText.includes('verify_signature'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Trust, verified.",
         "subtitle": "webhook.py runs four vectors -- tamper, secret, replay all fail."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant one type-72 card (generated shape) as the sole due card."""
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
            " VALUES(?, ?, '72', ?, ?, ?, '2000-01-01T00:00:00Z')",
            (CARD_ID, row[0], FRONT, BACK, json.dumps(PAYLOAD)))
        con.commit()
        return {"seeded": True, "card_id": CARD_ID}
    finally:
        con.close()
