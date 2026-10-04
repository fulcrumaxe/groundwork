"""Improvement demo: quarterly link audit as a test (I-50).

Full behavior: every internal link the app emits is extracted from
rendered HTML, normalized per canonurl rules, and matched against
the canonical route table -- as a CI test, not a quarterly chore.
The terminal beats prove the pure functions on a planted break and
then run the real audit suite green; Chrome shows the Status home
and one audited page.
"""
from __future__ import annotations

SCENARIO = {
    "id": "linkcheck",
    "kind": "improvement",
    "batch": 9,
    "item": "I-50",
    "title": "Link audit",
    "blurb": "Every internal link verified against the route table -- in CI.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 9 - Improvement I-50",
         "title": "Link audit",
         "subtitle": "No 404s, ever -- the audit runs in CI."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b9-linkcheck",
         "caption": "Status documents the audit: extract, normalize, match, report.",
         "assert_js": "() => !!document.querySelector('#status-b9-linkcheck')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: internal links must match a route; planted breaks flag.",
         "commands": [
             ["python3", "-c",
              "from groundwork import canonurl, linkcheck as m; "
              "html = '<a href=\"/due\">D</a><a href=\"/nope\">N</a><a href=\"https://x.example\">E</a>'; "
              "print('links:', m.extract_links(html)); "
              "r = m.audit_links(['/due', '/nope', 'https://x.example'], canonurl.ROUTES); "
              "print(m.audit_report(r))"],
         ]},
        {"type": "terminal", "duration": 10,
         "caption": "The real audit: every served page's links resolve -- the suite stays green.",
         "commands": [
             ["bash", "-lc",
              "python3 -m unittest discover -s tests -p 'test_linkcheck.py' 2>&1 | tail -4"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/modules",
         "caption": "The audit's subject: the internal links on every served page.",
         "assert_js": "() => document.querySelectorAll(\"a[href^='/']\").length > 5",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 9",
         "title": "Every link resolves.",
         "subtitle": "linkcheck.py audits rendered pages -- externals never flagged."},
    ],
}
