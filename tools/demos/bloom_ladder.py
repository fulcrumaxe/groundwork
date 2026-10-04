"""Feature demo: Bloom ladder (Batch 1).

Full functionality: six rungs beside each concept on the module page;
lit rungs mark demonstrated skill tiers from passing reviews. seed_db
promotes the first concept's first card to exercise type 8
(predict-output, apply tier) with two passing reviews, so its ladder
lights three rungs (recall, explain, apply) while the next concept's
ladder stays dark.
"""
from __future__ import annotations

import sqlite3


def _slug(text: str) -> str:
    """Anchor slug mirroring groundwork.lessons.slug (stdlib only).

    Scenario modules cannot import groundwork: the film process runs
    as tools/demo_video.py, so only tools/ is on sys.path.
    """
    out = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(filter(None, out.split("-"))) or "lesson"


SCENARIO = {
    "id": "bloom-ladder",
    "kind": "feature",
    "batch": 1,
    "item": "F-53",
    "title": "Bloom ladder",
    "blurb": "Six rungs beside each concept; lit rungs mark demonstrated skill tiers.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Feature bloom-ladder",
         "title": "Bloom ladder",
         "subtitle": "Six rungs beside each concept; lit rungs mark demonstrated skill tiers."},
        {"type": "terminal", "duration": 7,
         "caption": "Pure logic first: six rungs, and reached=2 lights the first three.",
         "commands": [
             ["python3", "-c",
              "from groundwork import debt as m; print(m.BLOOM_RUNGS); "
              "print('reached=2 lights', m.ladder_html(2).count(\"class='on'\"))"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/modules/{seed_mid}#ladder",
         "focus": "#lesson-{seed_slug}",
         "caption": "The seeded concept reached apply: three rungs lit beside its lesson.",
         "assert_js": "() => document.querySelectorAll('#ladder i.on').length",
         "assert_want": "3"},
        {"type": "terminal", "duration": 7,
         "caption": "Live from the fixture: bloom_reached reports rung 2 for the concept.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import db as d, debt as m; "
              "con = d.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print(m.bloom_reached(con, '{seed_mid}'))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules/{seed_mid}",
         "focus": "#lesson-{seed_slug2}",
         "caption": "The next concept has no passing reviews yet -- its ladder stays dark.",
         "assert_js": "() => document.querySelectorAll('#lesson-{seed_slug2} .ladder i.on').length",
         "assert_want": "0"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Climb to create.",
         "subtitle": "bloom_reached reads passing reviews -- the ladder lights what you proved."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Light the first concept's ladder to apply; keep the second dark.

    Picks the first module (rowid order) with at least two concepts
    where the first concept has a card; that card becomes type 8
    (predict-output, apply tier, rung index 2) with two passing
    reviews, so bloom_reached reports 2 and ladder_html lights three
    rungs. Returns the module id plus both lesson slugs for beats.
    """
    con = sqlite3.connect(db_path)
    try:
        mods = con.execute("SELECT id FROM modules ORDER BY rowid").fetchall()
        if not mods:
            return {"seeded": False, "reason": "no modules"}
        for (mid,) in mods:
            cids = con.execute(
                "SELECT id FROM concepts WHERE module_id=? ORDER BY rowid",
                (mid,)).fetchall()
            if len(cids) < 2:
                continue
            card = con.execute(
                "SELECT id FROM cards WHERE concept_id=? ORDER BY rowid LIMIT 1",
                (cids[0][0],)).fetchone()
            if not card:
                continue
            con.execute("UPDATE cards SET exercise_type='8' WHERE id=?",
                        (card[0],))
            con.execute("DELETE FROM reviews WHERE card_id=?", (card[0],))
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, 5, 4, 'seeded apply pass')", (card[0],))
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission)"
                " VALUES(?, 4, 3, 'seeded apply pass 2')", (card[0],))
            con.commit()
            node = cids[0][0].split(":", 1)[1] if ":" in cids[0][0] else cids[0][0]
            node2 = cids[1][0].split(":", 1)[1] if ":" in cids[1][0] else cids[1][0]
            return {"seeded": True, "mid": mid, "concept": cids[0][0],
                    "slug": _slug(node), "slug2": _slug(node2),
                    "bloom": "apply", "lit": 3}
        return {"seeded": False,
                "reason": "no module with 2 concepts and a card"}
    finally:
        con.close()
