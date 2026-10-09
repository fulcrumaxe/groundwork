"""Improvement demo: page snapshot goldens (I-95).

Full behavior: core pages render to normalized HTML (timestamps,
relative times, ids, and the October-only seasonal block all
scrubbed) and diff against committed goldens -- unexpected drift
fails the CI gate, while a planted rogue banner trips it on demand.
"""
from __future__ import annotations

SCENARIO = {
    "id": "pagesnap",
    "kind": "improvement",
    "batch": 18,
    "item": "I-95",
    "title": "Page snapshot goldens",
    "blurb": "Core pages diff against committed goldens; drift fails CI. See below.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Improvement I-95",
         "title": "Page snapshot goldens",
         "subtitle": "Rendered pages diff against committed goldens -- drift fails CI."},
        {"type": "terminal", "duration": 9,
         "caption": "Normalize in one call: volatile timestamps, ids, and the seasonal block all scrubbed.",
         "commands": [
             ["python3", "-c",
              "from groundwork import pagesnap as m; "
              "a = \"<p>due 2026-10-09</p>  <b>x</b>\"; b = \"<p>due 2026-10-10</p> <b>x</b>\"; "
              "print('dates scrubbed:', m.normalize(a) == m.normalize(b)); "
              "s = \"<ul></ul><h2 id=\\'seasonal-event\\'>Owntober \\u2014 own 5 concepts</h2><p>n</p><svg></svg>\"; "
              "print('seasonal scrubbed:', m.normalize(s) == m.normalize('<ul></ul><svg></svg>')); "
              "print('fingerprint:', m.fingerprint(a)[:16])"],
         ]},
        {"type": "terminal", "duration": 9,
         "caption": "The gate itself: four pages match goldens, and a planted rogue banner trips it.",
         "commands": [
             ["python3", "-m", "unittest", "discover", "-s", "tests",
              "-p", "test_pagesnap.py"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b18-pagesnap",
         "caption": "Status homes the improvement: refresh with UPDATE_GOLDENS=1, review the diff.",
         "assert_js": "() => !!document.querySelector('#status-b18-pagesnap')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Drift fails loudly.",
         "subtitle": "pagesnap.py normalizes, snapshots, compares -- goldens pin every page."},
    ],
}
