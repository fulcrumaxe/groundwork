"""Improvement demo: module status filter (I-19).

Full behavior: the Modules library filters by status -- all,
in-progress, owned, stale -- with per-tab counts and the active tab
marked. Predicate order: stale wins, then fully-owned, else
in-progress (unstarted counts as in-progress). The filtered beat
visits ?status=owned and asserts the marked tab.
"""
from __future__ import annotations

SCENARIO = {
    "id": "modfilter",
    "kind": "improvement",
    "batch": 7,
    "item": "I-19",
    "title": "Module status filter",
    "blurb": "The Modules library filters by status -- all, in-progress, owned, stale.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Improvement I-19",
         "title": "Module status filter",
         "subtitle": "Stale wins, then owned, else in-progress -- unstarted stays visible."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-modfilter",
         "caption": "Status documents the predicates with a live three-module demo.",
         "assert_js": "() => !!document.querySelector('#status-b7-modfilter')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: stale debt first, full ownership second, rest in-progress.",
         "commands": [
             ["python3", "-c",
              "from groundwork import modfilter as m; "
              "rows = [{'id': 'm1', 'owned': 0, 'total': 3, 'stale': 0}, {'id': 'm2', 'owned': 3, 'total': 3, 'stale': 0}, {'id': 'm3', 'owned': 1, 'total': 4, 'stale': 2}]; "
              "print([m.classify(r) for r in rows]); print(m.counts(rows))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/modules",
         "focus": "#modfilter-tabs",
         "caption": "Four tabs with live counts ride above the library.",
         "assert_js": "() => { const t = document.querySelectorAll('#modfilter-tabs a, #modfilter-tabs b'); "
                      "return t.length === 4 && !!document.querySelector(\"#modfilter-tabs [aria-current='page']\"); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules?status=owned",
         "focus": "#modfilter-tabs",
         "caption": "Owned only -- the tab marks itself current and the list obeys.",
         "assert_js": "() => { const cur = document.querySelector(\"#modfilter-tabs [aria-current='page']\"); "
                      "return !!cur && cur.textContent.includes('Owned'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "Find your debt.",
         "subtitle": "modfilter.py classifies pure row dicts -- no DB, no schema change."},
    ],
}
