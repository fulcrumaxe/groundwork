"""Feature demo: module health (Batch 3, never filed).

Full functionality: the Batch 3 modularity rule rendered and
enforced -- Status shows every capability area with its line count
and ceiling (modularity.status_rows), while check() + sizes() are
the gate the suite holds (tests/test_modularity.py). Code-driven
surface: no fixture rows to manipulate, so the terminal beats call
the live gate instead.
"""
from __future__ import annotations

SCENARIO = {
    "id": "module-health",
    "kind": "feature",
    "batch": 3,
    "title": "Module health",
    "blurb": "Every capability area with its size and ceiling -- web.py never grows.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 3 - Feature",
         "title": "Module health",
         "subtitle": "Every capability area with its size and ceiling -- web.py never grows."},
        {"type": "chrome", "duration": 8,
         "url_path": "/status",
         "focus": "#status-modular",
         "caption": "Status renders the rule itself: every area module with its size and ceiling.",
         "assert_js": "() => !!document.querySelector('#status-modular') && "
                      "document.body.innerText.includes('web.py')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The gate behind the table: zero violations, web.py under its ceiling.",
         "commands": [
             ["python3", "-c",
              "from groundwork import modularity as m; "
              "print('violations:', m.check()); "
              "s = m.sizes(); "
              "print('web.py:', s['web.py'], '/', m.WEB_CEILING); "
              "print(len(m.AREAS), 'areas, cap', m.AREA_CAP); "
              "print('status.py:', s['status.py'])"],
         ]},
        {"type": "terminal", "duration": 8,
         "caption": "The suite enforces it: ceilings hold or the build fails.",
         "commands": [
             ["python3", "-m", "unittest", "discover",
              "-s", "tests", "-p", "test_modularity.py", "-v"],
         ]},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 3",
         "title": "web.py never grows.",
         "subtitle": "modularity.py counts every area; the suite holds the ceilings."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Code-driven surface: the gate reads source lines, not rows."""
    return {"seeded": True, "note": "no fixture rows; beats call the live gate"}
