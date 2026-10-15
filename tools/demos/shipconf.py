"""Feature demo: ship-it confidence meter (F-133).

Full behavior: release confidence is the owned fraction of the
newest modules' concepts (the "release diff") -- unknown until
proven, never a fake percent. The served library already holds
newest modules with attempts, so the meter renders from live data
and the terminal beat reads the fixture window.
"""
from __future__ import annotations

SCENARIO = {
    "id": "shipconf",
    "kind": "feature",
    "batch": 25,
    "item": "F-133",
    "title": "Ship-it confidence",
    "blurb": "Owned coverage on the latest diff -- unknown until proven.",
    "beats": [
        {"type": "title", "duration": 4,
         "kicker": "Batch 25 - Feature F-133",
         "title": "Ship-it confidence",
         "subtitle": "Can you ship? The newest diff answers in percent."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b25-shipconf",
         "caption": "Status states the honesty rule: thin proof says unknown.",
         "assert_js": "() => !!document.querySelector('#status-b25-shipconf') "
                      "&& document.body.innerText.includes('unknown')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Percent to label: ship it, nearly there, risky, unknown.",
         "commands": [
             ["python3", "-c",
              "import os; from groundwork import shipconf as m; "
              "print('75%:', m.level(m.confidence(3, 4)), '| none:', m.level(m.confidence(0, 0))); "
              "c = m.window_counts(os.environ.get('DEMO_DB', 'groundwork.db')); "
              "print('window:', c['modules'], 'modules,', c['owned'], '/', c['concepts'], 'owned')"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/reviews",
         "focus": "#ship-confidence",
         "caption": "History headlines the release meter over the newest diff.",
         "assert_js": "() => !!document.querySelector('#ship-confidence')",
         "assert_want": "True"},
        {"type": "title", "duration": 4,
         "kicker": "Groundwork - Batch 25",
         "title": "Ship on proof.",
         "subtitle": "shipconf.py counts owned_map -- no tables, no fakes."},
    ],
}
