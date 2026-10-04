"""Feature demo: projects landing (Batch 1).

Full functionality: the / front door groups every module by repo with
owned-progress bars, newest activity first; clicking a card opens that
repo's modules. seed_db splits three modules into a second repo (the
fixture ships only one) and owns one concept with two passing
modify-tier reviews so a progress bar reads nonzero.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "projects-landing",
    "kind": "feature",
    "batch": 1,
    "title": "Projects landing",
    "blurb": "Every repo you are learning, with owned progress — the front door.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Feature projects-landing",
         "title": "Projects landing",
         "subtitle": "Every repo you are learning, with owned progress -- the front door."},
        {"type": "chrome", "duration": 9,
         "url_path": "/#projects",
         "focus": "#projects",
         "caption": "The front door: every repo with modules, newest first, progress on each card.",
         "assert_js": "() => document.querySelectorAll('#projects .modcard').length >= 2 && !!document.querySelector('#projects .bar i')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Grouped by repo in the fixture: hundreds of modules, two repos.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "rows = con.execute('SELECT repo, COUNT(*) FROM modules GROUP BY repo').fetchall(); "
              "print(len(rows), 'repos:', ', '.join(f'{n} modules' for _, n in rows))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/#projects",
         "caption": "Click a project card to open that repo's modules.",
         "js": ["() => { const a = document.querySelector(\"#projects .modcard\"); "
                "if (!a) return 'card-missing'; a.click(); return 'clicked'; }"],
         "poll_js": "() => location.href",
         "poll_want": "/modules?repo=",
         "poll_required": True,
         "poll_timeout": 25,
         "assert_js": "() => location.href.includes('/modules?repo=') && document.querySelectorAll('.modcard').length >= 1",
         "assert_want": "True"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof of progress: two passing modify-tier reviews own one concept.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print(con.execute('SELECT COUNT(*) FROM reviews WHERE grade >= 4').fetchone()[0], 'passing reviews')"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Pick a repo and study it.",
         "subtitle": "projects_html groups every module by repo -- progress included."},
    ],
}

SECOND_REPO = "/home/jp/learncode/SecondProject"


def seed_db(db_path: str) -> dict:
    """Split a second repo off the fixture and own one concept with progress.

    Moves three modules into SECOND_REPO (the fixture ships a single
    repo, so without this the landing shows one card), then owns one
    concept in the first module: its first card becomes exercise type
    19 (refactor-under-test, modify tier, which counts toward
    ownership) with two passing reviews, satisfying owned_map's
    attempts>=2 plus modify/create pass rule.
    """
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute("SELECT id FROM modules ORDER BY rowid").fetchall()
        if not rows:
            return {"seeded": False, "reason": "no modules"}
        repos = {r[0] for r in
                 con.execute("SELECT DISTINCT repo FROM modules").fetchall()}
        if len(repos) < 2 and len(rows) > 1:
            move = [r[0] for r in rows[1:4]]
            con.execute(
                "UPDATE modules SET repo=? WHERE id IN (%s)"
                % ",".join("?" * len(move)),
                [SECOND_REPO] + move)
        card = con.execute(
            "SELECT cards.id FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=? ORDER BY cards.rowid LIMIT 1",
            (rows[0][0],)).fetchone()
        if not card:
            con.commit()
            return {"seeded": True, "repo2": SECOND_REPO, "owned_card": None}
        con.execute("UPDATE cards SET exercise_type='19' WHERE id=?",
                    (card[0],))
        con.execute("DELETE FROM reviews WHERE card_id=?", (card[0],))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, submission)"
            " VALUES(?, 5, 4, 'seeded modify pass')", (card[0],))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, submission)"
            " VALUES(?, 4, 3, 'seeded modify pass 2')", (card[0],))
        con.commit()
        return {"seeded": True, "repo2": SECOND_REPO, "mid": rows[0][0],
                "owned_card": card[0]}
    finally:
        con.close()
