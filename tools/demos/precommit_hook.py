"""Feature demo: pre-commit hook (precommit-hook).

Full functionality: `hooks/pre-commit` warns when staged Python files
touch concepts nobody has proven (grade >= 4) yet -- and always exits
0, never blocking the commit. Status carries a live present-plus-
executable check. The beats show the Status gate, the hook on disk
with its contract header, and the repo tests proving warn-not-block.
"""
from __future__ import annotations

SCENARIO = {
    "id": "precommit-hook",
    "kind": "feature",
    "batch": 1,
    "item": "F-362",
    "title": "Pre-commit hook",
    "blurb": "hooks/pre-commit keeps bad commits out; presence shown below.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Feature precommit-hook",
         "title": "Pre-commit hook",
         "subtitle": "Warns on unproven concepts -- never blocks a commit."},
        {"type": "chrome", "duration": 8,
         "url_path": "/status#status-hooks",
         "focus": "#status-hooks",
         "caption": "Status reports the hook state live from the repo checkout.",
         "assert_js": "() => !!document.querySelector('#status-hooks') && "
                      "document.body.innerText.includes('hooks/pre-commit')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 11,
         "caption": "The gate on disk: presence, docs, warn-never-block contract.",
         "commands": [
             ["bash", "-lc",
              "ls -l hooks/pre-commit && sed -n '1,6p' hooks/pre-commit"],
         ]},
        {"type": "terminal", "duration": 9,
         "caption": "The repo tests for the gate: warns loudly, exits zero.",
         "commands": [
             ["bash", "-lc",
              "python3 -m unittest tests.test_integrations.HookTest 2>&1 | tail -3"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Nudges, not roadblocks.",
         "subtitle": "The hook queries grades live; Status checks it is executable."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Stateless feature: nothing to plant, the gate reads the repo.

    Returns seeded True so the pipeline logs the no-op honestly;
    no tables are touched, so empty DBs are safe by construction.
    """
    return {"seeded": True, "note": "stateless: hook file plus status gate"}
