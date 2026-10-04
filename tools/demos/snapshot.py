"""Improvement demo: shareable session snapshot (I-49).

Full behavior: one module's session state (answered, accuracy)
packs into an HMAC-signed URL token that renders read-only --
counts only, no answer text, no journal -- while forged or expired
links fail closed to 404. The share secret is process-lifetime, so
the camera proves the token design in the terminal (roundtrip,
tamper, sanitize) and the fail-closed /share/ route in Chrome.
"""
from __future__ import annotations

SCENARIO = {
    "id": "snapshot",
    "kind": "improvement",
    "batch": 9,
    "item": "I-49",
    "title": "Shareable session snapshot",
    "blurb": "A signed link shows one module's counts -- read-only, no private data.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Improvement I-49",
         "title": "Shareable session snapshot",
         "subtitle": "Counts travel in a signed link -- private data never leaves."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-snapshot",
         "caption": "Status documents the token: signed counts, fail-closed decode.",
         "assert_js": "() => !!document.querySelector('#status-b9-snapshot')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: signed counts verify, tampering yields None.",
         "commands": [
             ["python3", "-c",
              "from groundwork import snapshot as m; "
              "t = m.encode_snapshot({'module_id': 'm7', 'answered': 10, 'correct': 8}, 's3cret'); "
              "print('token:', t[:32] + '...'); "
              "print('decode:', m.decode_snapshot(t, 's3cret')); "
              "print('tampered:', m.decode_snapshot(t[:-2] + 'xx', 's3cret')); "
              "print('clean:', m.sanitize_snapshot({'module_id': 'm7', 'answered': 10, 'correct': 8, 'submission': 'Paris', 'journal': 'dear diary'}))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/share/{seed_forged}",
         "caption": "A forged token fails closed -- the route 404s instead of guessing.",
         "poll_js": "() => document.body.innerText.slice(0, 12000)",
         "poll_want": "Nothing lives at",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => !!document.querySelector('#not-found') && "
                      "document.body.innerText.includes('Nothing lives at')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 5,
         "caption": "The render: counts and accuracy only, re-sanitized first.",
         "commands": [
             ["python3", "-c",
              "from groundwork import snapshot as m; "
              "print(m.snapshot_html({'module_id': 'm7', 'answered': 10, 'correct': 8}))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Shared, not leaked.",
         "subtitle": "snapshot.py signs counts -- forgeries and expiry fail closed."},
    ],
}


def seed_db(db_path: str) -> dict:
    """No fixture rows needed -- just a forged token for the 404 beat."""
    return {"seeded": True, "forged": "Zm9yZ2Vk.c2ln"}
