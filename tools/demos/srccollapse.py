"""Improvement demo: long source blocks collapse (I-108).

Full behavior: source past twelve lines hides behind a Show full
file context expander -- short snippets read on, the full text
stays in the DOM for no-JS readers. Db-free: both chrome beats
work the live Status sample, opening the expander on the second.
"""
from __future__ import annotations

SCENARIO = {
    "id": "srccollapse",
    "kind": "improvement",
    "batch": 19,
    "item": "I-108",
    "title": "Long source blocks collapse",
    "blurb": "Long lesson source hides behind an expander -- short snippets read on.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 19 - Improvement I-108",
         "title": "Long source blocks collapse",
         "subtitle": "Twelve lines read on -- longer hides behind one click."},
        {"type": "terminal", "duration": 8,
         "caption": "Twenty lines collapse, two lines read on, empty input renders nothing.",
         "commands": [
             ["python3", "-c",
              "from groundwork import srccollapse as m; "
              "long = '\\n'.join(f'def f{i}():\\n    return {i}' for i in range(10)); "
              "print('long collapses:', 'srccollapse' in m.block_html(long)); "
              "print('short reads on:', 'srccollapse' not in m.block_html('x = 1')); "
              "print('empty renders:', repr(m.block_html('')))"],
         ]},
        {"type": "chrome", "duration": 7,
         "url_path": "/status",
         "focus": "#status-b19-srccollapse",
         "caption": "Status carries a live sample: twenty lines behind the expander.",
         "assert_js": "() => !!document.querySelector('#status-b19-srccollapse') && "
                      "document.body.innerText.includes('Show full file context') && "
                      "document.body.innerText.includes('(20 lines)')",
         "assert_want": "True"},
        {"type": "chrome", "duration": 8,
         "url_path": "/status",
         "focus": "#status-b19-srccollapse",
         "caption": "One click opens it -- the full text was in the DOM all along.",
         "js": ["() => { const d = document.querySelector('details.srccollapse'); "
               "if (!d) return 'missing'; d.open = true; return 'opened'; }"],
         "assert_js": "() => document.body.innerText.includes('def f9')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 19",
         "title": "Skim first, expand later.",
         "subtitle": "srccollapse.py gates on line count -- short markup byte-identical."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Db-free improvement: the Status sample is the fixture."""
    return {"seeded": True, "note": "status sample, no fixture"}
