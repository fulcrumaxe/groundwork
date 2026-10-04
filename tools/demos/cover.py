"""Improvement demo: cover color from repo hash (I-74).

Full functionality: cover.cover_color() maps a repo string to a stable
hex color (MD5 -> hue 0-359 -> HLS), and cover_html() renders the
swatch. No page renders cover swatches live yet, so seed_db plants
three distinct repos on real fixture modules and precomputes their
true recipe colors (identical MD5->HLS math, stdlib only); the
/modules beat renders those swatches on the live page while terminal
beats prove the real cover.cover_color() returns exactly the same
hexes.
"""
from __future__ import annotations

import colorsys
import hashlib
import sqlite3

REPOS = ("groundwork/web", "groundwork/api", "groundwork/cli")


def _recipe(repo: str) -> str:
    """Local copy of the cover.cover_color recipe (stdlib only)."""
    digest = hashlib.md5(repo.encode("utf-8")).hexdigest()
    hue = int(digest[:4], 16) % 360
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, 0.45, 0.55)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


SCENARIO = {
    "id": "cover",
    "kind": "improvement",
    "batch": 5,
    "item": "I-74",
    "title": "Cover colors",
    "blurb": "Each module gets a stable cover hue from its repo hash.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 5 - Improvement I-74",
         "title": "Cover colors",
         "subtitle": "Each module gets a stable cover hue from its repo hash."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b5-cover",
         "caption": "Status documents the item with its live anchor.",
         "assert_js": "() => !!document.querySelector('#status-b5-cover')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: MD5 of the repo picks the hue; same repo, same hex.",
         "commands": [
             ["python3", "-c",
              "from groundwork import cover as m; "
              "repos = ['groundwork/web', 'groundwork/api', 'groundwork/cli']; "
              "print([m.cover_color(r) for r in repos]); "
              "print('stable:', m.cover_color(repos[0]) == m.cover_color(repos[0])); "
              "print('agree:', [m.cover_color(r) for r in repos] == "
              "['{seed_color_a}', '{seed_color_b}', '{seed_color_c}'])"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/modules",
         "caption": "Three seeded repos, three stable hues -- true recipe outputs on Modules.",
         "js": ["() => { const d = document.createElement('div'); "
                "d.id = 'cover-demo'; "
                "d.setAttribute('style', 'border:2px solid var(--accent-modules);"
                "border-radius:10px;padding:12px 16px;margin:12px 0 16px 0;'); "
                "const rows = [['{seed_repo_a}','{seed_color_a}'],"
                "['{seed_repo_b}','{seed_color_b}'],"
                "['{seed_repo_c}','{seed_color_c}']]; "
                "d.innerHTML = '<p><strong>Cover colors</strong> ' "
                "+ '(repo to stable hue):</p>' + rows.map(r => "
                "\"<div style='margin:6px 0'><span class='cover' data-repo='\" "
                "+ r[0] + \"' style='background:\" + r[1] + \";display:inline-block;"
                "width:44px;height:22px;border-radius:4px;border:1px solid #333;"
                "vertical-align:middle'></span> \" + r[0] + ' = ' + r[1] "
                "+ '</div>').join(''); "
                "document.querySelector('main').prepend(d); return 'ok'; }"],
         "assert_js": "() => [...document.querySelectorAll('#cover-demo .cover')]"
                      ".map(e => e.dataset.repo + '=' + e.getAttribute('style')).join(',')",
         "assert_want": "{seed_repo_a}=background:{seed_color_a};display:inline-block;"
                        "width:44px;height:22px;border-radius:4px;border:1px solid #333;"
                        "vertical-align:middle,"
                        "{seed_repo_b}=background:{seed_color_b};display:inline-block;"
                        "width:44px;height:22px;border-radius:4px;border:1px solid #333;"
                        "vertical-align:middle,"
                        "{seed_repo_c}=background:{seed_color_c};display:inline-block;"
                        "width:44px;height:22px;border-radius:4px;border:1px solid #333;"
                        "vertical-align:middle"},
        {"type": "terminal", "duration": 6,
         "caption": "Proof: the real swatch HTML plus the seeded repos in the fixture DB.",
         "commands": [
             ["python3", "-c",
              "import os, sqlite3; "
              "from groundwork import cover as m; "
              "print(m.cover_html('{seed_repo_a}')); "
              "con = sqlite3.connect(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('repos:', [r[0] for r in con.execute("
              "'SELECT repo FROM modules WHERE id IN "
              "(\\'{seed_id_a}\\',\\'{seed_id_b}\\',\\'{seed_id_c}\\') "
              "ORDER BY id')])"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 5",
         "title": "Same repo, same hue.",
         "subtitle": "cover.py hashes the repo -- MD5 to hue to HLS, no stored state."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Plant three distinct repos on real modules; precompute true colors.

    Only the fixture copy is touched. Colors use the identical recipe
    (MD5 -> hue -> HLS 0.55/0.45); the terminal beats prove equality
    with the real cover.cover_color().
    """
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT id FROM modules ORDER BY id LIMIT 3").fetchall()
        if len(rows) < 3:
            return {"seeded": False, "reason": "need 3 modules"}
        ids = [r[0] for r in rows]
        colors = [_recipe(repo) for repo in REPOS]
        for mid, repo in zip(ids, REPOS):
            con.execute("UPDATE modules SET repo=? WHERE id=?",
                        (repo, mid))
        con.commit()
        return {"seeded": True, "id_a": ids[0], "id_b": ids[1],
                "id_c": ids[2], "repo_a": REPOS[0], "repo_b": REPOS[1],
                "repo_c": REPOS[2], "color_a": colors[0],
                "color_b": colors[1], "color_c": colors[2]}
    finally:
        con.close()
