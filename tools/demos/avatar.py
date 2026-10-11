"""Feature demo: duo-tone library identity tile (F-116).

Full behavior: one stable mark per library — two hues plus a shape
derived from the library content, drawn as a small inline SVG tile
beside the History headline. No upload, no account, no network;
the same library always draws the same friend. No fixture needed.
"""
from __future__ import annotations

SCENARIO = {
    "id": "avatar",
    "kind": "feature",
    "batch": 23,
    "item": "F-116",
    "title": "Library identity",
    "blurb": "One stable duo-tone mark per library -- local, playful, no account.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 23 - Feature F-116",
         "title": "Library identity",
         "subtitle": "A mark that is yours -- same colors every visit."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b23-avatar",
         "caption": "Status shows a live sample tile beside the local-only promise.",
         "assert_js": "() => !!document.querySelector("
                      "'#status-b23-avatar') "
                      "&& !!document.querySelector('svg.avatar')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Two hues plus a shape from the content hash -- stable per key.",
         "commands": [
             ["python3", "-c",
              "from groundwork import avatar as m; "
              "a = m.identity_for('groundwork'); b = m.identity_for('groundwork'); "
              "print('stable:', a == b, a); "
              "print('svg:', m.avatar_svg('groundwork')[:60] + '...')"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "focus": "#library-identity",
         "caption": "Every History visit opens beside your library mark.",
         "assert_js": "() => !!document.querySelector("
                      "'#library-identity svg.avatar')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 23",
         "title": "Same friend, every visit.",
         "subtitle": "avatar.py hashes content to color -- no account, no network."},
    ],
}


def seed_db(db_path: str) -> dict:
    """No fixture needed: the mark derives from live library content."""
    return {"seeded": True, "note": "content-addressed, no fixture"}
