"""Improvement demo: canonical URL contract (I-33).

Full behavior: canonurl.canonical() strips one language prefix,
folds slashes, drops trailing slashes, preserves query/fragment,
and fails closed on hostile shapes; ROUTES is the single table
linkcheck audits served HTML against. No seed_db (modpages
precedent): Status shows the contract, terminal beats run the
normalizer + the real link audit, /reviews proves a member live.
"""
from __future__ import annotations

SCENARIO = {
    "id": "canonurl",
    "kind": "improvement",
    "batch": 8,
    "item": "I-33",
    "title": "Canonical URL contract",
    "blurb": ("One language-prefix-free URL per page -- the full route "
              "table lives on Status."),
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 8 - Improvement I-33",
         "title": "Canonical URL contract",
         "subtitle": ("One URL per page -- no language prefix, no trailing "
                      "slash, query kept verbatim.")},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b8-canonurl",
         "caption": ("Status carries the contract: every route, one path, "
                     "one purpose."),
         "assert_js": "() => !!document.querySelector('#status-b8-canonurl') && "
                      "document.body.innerText.includes('/mcp')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": ("The rule in one line: prefixes strip, slashes fold, "
                     "debt survives, hostile falls home."),
         "commands": [
             ["python3", "-c",
              "from groundwork import canonurl as m; "
              "print(m.canonical('/en/due?mode=one')); "
              "print(m.canonical('/due/')); "
              "print(m.canonical('/debt')); "
              "print(m.canonical('//evil/x')); "
              "print(m.is_canonical('/en/due'), m.is_canonical('/due'))"],
         ]},
        {"type": "terminal", "duration": 7,
         "caption": ("The real caller: the link audit checks served HTML "
                     "against this table."),
         "commands": [
             ["python3", "-c",
              "from groundwork import canonurl, linkcheck; "
              "links = ['/due', '/en/modules?page=2', '/nope', "
              "'https://example.com/x']; "
              "r = linkcheck.audit_links(links, canonurl.ROUTES); "
              "print(linkcheck.audit_report(r))"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/reviews",
         "caption": "Contract members resolve: /reviews serves the attempt history.",
         "assert_js": "() => document.body.innerText.length > 200",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 8",
         "title": "One page, one URL.",
         "subtitle": ("canonurl.py owns the table -- linkcheck enforces it "
                      "in CI.")},
    ],
}
