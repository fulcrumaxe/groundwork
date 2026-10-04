"""Improvement demo: inline SVG wordmark in every page header (I-55).

Full behavior: a single inline SVG lockup (rounded-square G monogram
plus the word Groundwork) painted entirely in currentColor ships in
every page h1 -- no image file, no webfont, no network, no emoji.
Heights clamp to 16-32px and bad input fails closed. Chrome proves
the header mark on a live page; the terminal proves the clamp and
the fail-closed word.
"""
from __future__ import annotations

SCENARIO = {
    "id": "wordmark",
    "kind": "improvement",
    "batch": 10,
    "item": "I-55",
    "title": "Wordmark",
    "blurb": "One inline SVG lockup signs every page header -- no files, no fonts.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 10 - Improvement I-55",
         "title": "Wordmark",
         "subtitle": "One inline SVG -- the header signs every page."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b10-wordmark",
         "caption": "Status homes the mark: inline SVG, currentColor, no network.",
         "assert_js": "() => !!document.querySelector('#status-b10-wordmark')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: currentColor throughout, heights clamped, never raises.",
         "commands": [
             ["python3", "-c",
              "from groundwork import wordmark as m; "
              "print('currentColor:', 'currentColor' in m.wordmark_svg()); "
              "print('clamp-hi:', \"height='32'\" in m.wordmark_svg(height=999)); "
              "print('clamp-lo:', \"height='16'\" in m.wordmark_svg(height=2)); "
              "print('fail-closed:', 'Groundwork' in m.wordmark_svg(word=12345))"],
         ]},
        {"type": "chrome", "duration": 12,
         "url_path": "/due",
         "caption": "Every page header signs itself -- the wordmark rides in the h1.",
         "assert_js": "() => !!document.querySelector('h1 svg.wordmark')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 10",
         "title": "Signed, every page.",
         "subtitle": "wordmark.py inlines the lockup -- currentColor adapts for free."},
    ],
}
