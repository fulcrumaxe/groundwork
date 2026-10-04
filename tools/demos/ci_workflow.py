"""Feature demo: CI workflow (ci-workflow).

Full functionality: `.github/workflows/groundwork.yml` runs the test
suite plus the end-to-end learning loop on every push, and Status
carries a live present/missing check on the file. Stateless on the
DB side -- the beats show the Status gate, the workflow's trigger
and proof steps, and the repo test that guards the file.
"""
from __future__ import annotations

SCENARIO = {
    "id": "ci-workflow",
    "kind": "feature",
    "batch": 1,
    "title": "CI workflow",
    "blurb": "Tests run on every push; status surfaced below.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 1 - Feature ci-workflow",
         "title": "CI workflow",
         "subtitle": "Every push runs the suite plus the learning loop."},
        {"type": "chrome", "duration": 8,
         "url_path": "/status#status-ci",
         "focus": "#status-ci",
         "caption": "Status shows the live check: workflow file present.",
         "assert_js": "() => !!document.querySelector('#status-ci') && "
                      "document.body.innerText.includes('groundwork.yml')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 11,
         "caption": "The workflow itself: name, triggers, and the two proof steps.",
         "commands": [
             ["bash", "-lc",
              "grep -E '^(name|on|jobs)|run: python' .github/workflows/groundwork.yml"],
         ]},
        {"type": "terminal", "duration": 9,
         "caption": "The repo test that guards the workflow file: green.",
         "commands": [
             ["bash", "-lc",
              "python3 -m unittest tests.test_integrations.WorkflowTest 2>&1 | tail -3"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 1",
         "title": "Pushed code proves itself.",
         "subtitle": "status.py reads the workflow path live -- no cached badge."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Stateless feature: nothing to plant, the gate reads the repo.

    Returns seeded True so the pipeline logs the no-op honestly;
    no tables are touched, so empty DBs are safe by construction.
    """
    return {"seeded": True, "note": "stateless: workflow file plus status gate"}
