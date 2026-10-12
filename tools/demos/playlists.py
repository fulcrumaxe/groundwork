"""Feature demo: session playlists, 5/10/20-minute mixes (F-120).

Full behavior: the Due page offers one start row per mix length,
each budgeted from the live queue head by minisession.pick_cards;
an empty queue renders the calm all-clear. seed_db plants 3 due cards.
"""
from __future__ import annotations

import json
import sqlite3

CARD_IDS = ("demo-playlists-120a", "demo-playlists-120b",
            "demo-playlists-120c")

SCENARIO = {
    "id": "playlists",
    "kind": "feature",
    "batch": 24,
    "item": "F-120",
    "title": "Session playlists",
    "blurb": "Pick your minutes -- a mix built from your queue.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 24 - Feature F-120",
         "title": "Session playlists",
         "subtitle": "Five, ten, twenty minutes -- start the mix."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b24-playlists",
         "caption": "Status names the budgeter: queue head, never copied.",
         "assert_js": "() => !!document.querySelector("
                      "'#status-b24-playlists')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Each length maps to picked card ids from the same queue.",
         "commands": [
             ["python3", "-c",
              "from groundwork import playlists as m; "
              "due = [{'id': 'a', 'due': '2000-01-01'}, {'id': 'b', 'due': '2000-01-02'}]; "
              "print(m.mixes_for(due)); "
              "print(m.playlist_html([])[:120])"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/due",
         "focus": "#playlists",
         "caption": "The Due page deals three start rows from the live queue.",
         "assert_js": "() => !!document.querySelector('#playlists') "
                      "&& document.body.innerText.includes("
                      "'Start 5-minute mix')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 24",
         "title": "Press play, practice.",
         "subtitle": "playlists.py budgets the queue -- you pick minutes."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant three cards as the due queue for the mixes."""
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT id FROM concepts ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no concepts"}
        con.execute("UPDATE cards SET due='2030-01-01T00:00:00Z'")
        for i, cid in enumerate(CARD_IDS):
            con.execute("DELETE FROM reviews WHERE card_id=?", (cid,))
            con.execute(
                "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
                " front, back, payload, due)"
                " VALUES(?, ?, '5', ?, ?, ?, '2000-01-01T00:00:00Z')",
                (cid, row[0],
                 f"In your own words: playlist card {i + 1} of 3.",
                 f"Answer {i + 1}: short mixes beat long dread.",
                 json.dumps({"rubric": ["short", "mixes"]})))
        con.commit()
        return {"seeded": True, "cards": len(CARD_IDS)}
    finally:
        con.close()
