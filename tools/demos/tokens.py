"""Improvement demo: design tokens single table (I-94).

Full behavior: one TOKENS table read from the real palette/radius
emitters feeds both the README design-tokens section (docs regen owns
it) and the styleguide gallery rows, so the two can never drift.
No fixture needed: every beat reads the live emitters.
"""
from __future__ import annotations

SCENARIO = {
    "id": "tokens",
    "kind": "improvement",
    "batch": 18,
    "item": "I-94",
    "title": "Design tokens",
    "blurb": "One token table documents every palette and radius token in the README and the styleguide.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Improvement I-94",
         "title": "Design tokens",
         "subtitle": "One table feeds the README and the gallery -- values read from the real emitters."},
        {"type": "terminal", "duration": 8,
         "caption": "The table in one call: 11 tokens, every value straight from the emitters.",
         "commands": [
             ["python3", "-c",
              "from groundwork import tokens as t, palette as p, radius as r; "
              "print(len(t.TOKENS), 'tokens:'); "
              "by = {x['name']: x['value'] for x in t.TOKENS}; "
              "print('palette parity:', all(by[k] == v for k, v in p.PALETTE.items())); "
              "print('radius parity:', all(by[k] == v for k, v in r.RADII.items())); "
              "print('sample:', [x for x in t.TOKENS if x['name'] == '--r-chip'][0])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/styleguide",
         "focus": "#design-tokens",
         "caption": "The gallery renders the same table live, one row per token with a swatch.",
         "assert_js": "() => { const el = document.querySelector('#design-tokens'); "
                      "return !!el && document.body.innerText.includes('--r-chip'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "Docs regen owns the README section -- regen is clean, rows match the table.",
         "commands": [
             ["python3", "-c",
              "from groundwork import docs as d, tokens as t; "
              "print('regen changed:', d.render_all()); "
              "text = open('README.md').read(); "
              "print('marker present:', '<!-- GW-TOKENS:START -->' in text); "
              "print('rows covered:', sum(1 for x in t.TOKENS if ('`' + x['name'] + '`') in text), '/', len(t.TOKENS))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-tokens",
         "caption": "Status homes the improvement: never copied, a rename breaks parity loudly.",
         "assert_js": "() => !!document.querySelector('#status-b18-tokens')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Read, never copied.",
         "subtitle": "tokens.py feeds docs and gallery -- drift is impossible, renames fail loud."},
    ],
}
