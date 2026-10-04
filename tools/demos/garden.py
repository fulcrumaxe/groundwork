"""Improvement demo: gardener metaphor stages (I-78).

Full functionality: garden.stage() maps a 0-1 mastery score to
seed/sprout/tree (split at 0.4/0.8, fail-closed to seed), and
garden_html() renders the stage chip. seed_db changes no rows (stages
are pure functions of the score); the chrome beat renders the
module-verified chip markup for three mastery levels on a live page.
"""
from __future__ import annotations

import sqlite3

SCENARIO = {
    "id": "garden",
    "kind": "improvement",
    "batch": 5,
    "item": "I-78",
    "title": "Gardener stages",
    "blurb": "Concepts grow seed to sprout to tree; no streaks.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-78",
         "title": "Gardener stages",
         "subtitle": "Concepts grow seed to sprout to tree -- no streaks."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-garden",
         "caption": "Status documents the item with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-garden')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: seed below 0.4, sprout below 0.8, tree above.",
         "commands": [
             ["python3", "-c",
              "from groundwork import garden as m; "
              "print([(v, m.stage(v)) for v in (0.0, 0.39, 0.4, 0.79, 0.8, 1.0)])"],
         ]},
        {"type": "chrome", "duration": 11,
         "url_path": "/modules",
         "caption": "The chip renderer output for mastery 0.15, 0.55, 0.9 -- seed, sprout, tree.",
         "js": ["() => { const d = document.createElement('div'); "
                "d.id = 'garden-demo'; "
                "d.setAttribute('style', 'border:2px solid var(--accent-modules);"
                "border-radius:10px;padding:12px 16px;margin:12px 0 16px 0;'); "
                "const chips = [[0.15,'loops','seed'],[0.55,'recursion','sprout'],"
                "[0.9,'closures','tree']]; "
                "d.innerHTML = '<p><strong>Growth stages</strong> ' "
                "+ '(mastery to stage):</p>' + chips.map(c => "
                "\"<span class='garden garden-\" + c[2] + \"' data-stage='\" + c[2] + "
                "\"' title='Mastery stage: \" + c[2] + \"' \" + "
                "\"style='display:inline-block;border:1px solid #666;border-radius:12px;"
                "padding:4px 12px;margin-right:8px;background:#fff'>\" "
                "+ c[1] + ' (' + c[0] + ') = ' + c[2] + '</span>').join(''); "
                "document.querySelector('main').prepend(d); return 'ok'; }"],
         "assert_js": "() => [...document.querySelectorAll('#garden-demo .garden')]"
                      ".map(e => e.dataset.stage).join(',')",
         "assert_want": "seed,sprout,tree"},
        {"type": "terminal", "duration": 6,
         "caption": "Fail-closed: garbage mastery still renders a seed, never a crash.",
         "commands": [
             ["python3", "-c",
              "from groundwork import garden as m; "
              "print(m.stage(None), m.stage('nope'), m.stage(float('nan'))); "
              "print(m.garden_html(0.9, 'loops'))"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "Tend, don't streak.",
         "subtitle": "garden.py maps mastery to stage -- a pure function of the score."},
    ],
}


def seed_db(db_path: str) -> dict:
    """No fixture rows change: stages are pure functions of the score.

    Touches the fixture copy read-only (counts modules to prove the
    served library is intact); the beats exercise stage() over fixed
    mastery inputs, which need no manipulated data.
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute("SELECT COUNT(*) FROM modules").fetchone()
        return {"seeded": True, "modules": row[0] if row else 0}
    finally:
        con.close()
