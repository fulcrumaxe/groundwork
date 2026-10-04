"""Improvement demo: modules pagination (I-20).

Full behavior: past 50 modules the library splits into server-side
pages -- plain ?page=N links at 50 per page, out-of-range pages
clamping, a "Showing X-Y of Z" line, and existing filters riding
along. The 388-module fixture paginates live; the page-2 beat
asserts the summary and the current-page mark.
"""
from __future__ import annotations

SCENARIO = {
    "id": "modpages",
    "kind": "improvement",
    "batch": 7,
    "item": "I-20",
    "title": "Modules pagination",
    "blurb": "Past 50 modules the library splits into pages -- page links keep your filters.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 7 - Improvement I-20",
         "title": "Modules pagination",
         "subtitle": "Fifty per page, server-rendered -- filters ride along, garbage clamps."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b7-modpages",
         "caption": "Status documents the improvement: ?page=N links, clamped, summarized.",
         "assert_js": "() => !!document.querySelector('#status-b7-modpages')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: 388 modules means 8 pages, and 'abc' means page 1.",
         "commands": [
             ["python3", "-c",
              "from groundwork import modpages as m; "
              "print('pages for 388:', m.total_pages(388)); "
              "print('page 2 shows:', m.paginate(range(388), 2)['start'], 'to', m.paginate(range(388), 2)['end']); "
              "print('garbage page:', m.normalize_page('abc', 8))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/modules",
         "focus": ".pager-summary",
         "caption": "Page one of eight: the summary line plus prev/next and numbered links.",
         "assert_js": "() => { const s = document.querySelector('.pager-summary'); "
                      "return !!s && s.textContent.includes('Showing 1') && "
                      "!!document.querySelector('nav.pager'); }",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/modules?page=2",
         "focus": ".pager-summary",
         "caption": "Page two shows 51-100 -- the current page marks itself.",
         "assert_js": "() => { const s = document.querySelector('.pager-summary'); "
                      "const cur = document.querySelector(\"nav.pager [aria-current='page']\"); "
                      "return !!s && s.textContent.includes('51') && "
                      "!!cur && cur.textContent.trim() === '2'; }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 7",
         "title": "The library scales.",
         "subtitle": "modpages.py slices pure lists -- offline-friendly, no JS build."},
    ],
}
