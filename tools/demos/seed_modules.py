"""Feature demo: Groundwork seed (Batch 2).

Full functionality: export-seed bundles every module under one repo
into a portable seed file; import-seed loads it into any database;
re-imports skip as duplicates; reviews stay private. seed_db plants
one review on the richest module so the source-vs-imported contrast
is real (the served library DB already holds one review; the planted
row pins the count at two).
"""
from __future__ import annotations

import sqlite3
from urllib.parse import quote

SCENARIO = {
    "id": "seed-modules",
    "kind": "feature",
    "batch": 2,
    "title": "Groundwork seed",
    "blurb": "Groundwork itself ships as learnable modules: export one repo's modules to a seed file, import it anywhere.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 2 - Feature seed-modules",
         "title": "Groundwork seed",
         "subtitle": "Groundwork itself ships as learnable modules: export one repo's modules to a seed file, import it anywhere."},
        {"type": "chrome", "duration": 8,
         "url_path": "/status",
         "focus": "#status-seed",
         "caption": "Status documents the seed loop: export one repo out, import-seed in anywhere.",
         "assert_js": "() => !!document.querySelector('#status-seed') && "
                      "document.body.innerText.includes('export-seed')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 14,
         "caption": "Round trip: {seed_n} modules out, {seed_n} in, re-import skips cleanly.",
         "commands": [
             ["bash", "-lc",
              "rm -f /tmp/demo-seed.json /tmp/demo-seed-dest.db && "
              "python3 -m groundwork --db \"$DEMO_DB\" export-seed --repo \"{seed_repo}\" --out /tmp/demo-seed.json && "
              "python3 -m groundwork --db /tmp/demo-seed-dest.db import-seed --in /tmp/demo-seed.json | awk '{print $1}' | sort | uniq -c && "
              "python3 -m groundwork --db /tmp/demo-seed-dest.db import-seed --in /tmp/demo-seed.json | awk '{print $1}' | sort | uniq -c"],
             ["python3", "-c",
              "import os, sqlite3; "
              "s = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "d = sqlite3.connect('/tmp/demo-seed-dest.db'); "
              "src = s.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]; "
              "print('source reviews:', src, '-> imported:', d.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]); "
              "print('dest modules:', d.execute('SELECT COUNT(*) FROM modules').fetchone()[0])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules?repo={seed_repo_q}",
         "caption": "The export unit: every module under one repo, page one of the library.",
         "assert_js": "() => { const c = document.querySelector('.crumbs'); "
                      "return (c ? c.textContent : 'missing') + ' | ' + "
                      "document.querySelectorAll('#library article').length; }",
         "assert_want": "CodeCompanion"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 2",
         "title": "Groundwork, portable.",
         "subtitle": "share.py bundles one repo -- duplicates skip, reviews stay private."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pin the source review count at two; report the repo + module count.

    The export unit is every module sharing one repo prefix. The
    planted review joins the richest module so the privacy beat shows
    a real source-vs-imported contrast (dest imports zero reviews).
    """
    con = sqlite3.connect(db_path)
    try:
        repos = con.execute(
            "SELECT repo, COUNT(*) FROM modules GROUP BY repo"
            " ORDER BY COUNT(*) DESC").fetchall()
        if not repos:
            return {"seeded": False, "reason": "no modules"}
        repo = repos[0][0] or ""
        n = repos[0][1]
        m = con.execute(
            "SELECT concepts.module_id FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " JOIN modules ON modules.id = concepts.module_id"
            " WHERE modules.repo = ? GROUP BY concepts.module_id"
            " ORDER BY COUNT(*) DESC LIMIT 1", (repo,)).fetchone()
        if m:
            card = con.execute(
                "SELECT cards.id FROM cards JOIN concepts"
                " ON concepts.id = cards.concept_id"
                " WHERE concepts.module_id=? LIMIT 1", (m[0],)).fetchone()
            if card:
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence, submission)"
                    " VALUES(?, 4, 3, 'seed privacy probe')", (card[0],))
        con.commit()
        n_cards = con.execute(
            "SELECT COUNT(*) FROM cards JOIN concepts"
            " ON concepts.id = cards.concept_id"
            " JOIN modules ON modules.id = concepts.module_id"
            " WHERE modules.repo = ?", (repo,)).fetchone()[0]
        return {"seeded": True, "repo": repo, "repo_q": quote(repo, safe=""),
                "n": n, "cards": n_cards}
    finally:
        con.close()
