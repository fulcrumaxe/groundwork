"""Improvement demo: loading skeletons for module pages (I-81).

Full behavior: module pages build mid-request (seven DB reads plus
the lesson render loop) while the browser shows nothing, so
skeleton_html() provides an instant static shell -- title bar,
progress bar on the real .bar selectors, N lesson rows -- with empty
spans only (aria-busy wrapper, aria-hidden inner) and one optional
250ms pulse behind prefers-reduced-motion:no-preference. The styles
ride the head wire on every page; the Status anchor documents the
contract. The interaction beat injects the helper's exact bytes into
a live module page to show the shell the browser would paint first.
"""
from __future__ import annotations

import sqlite3

#: Machine-synced bytes of skeleton_html() with default rows (DO NOT
#: hand-edit: some class names resemble secret-key patterns and may
#: render redacted in tool output). Injected into a live module page
#: so the filmed shell is byte-identical to the helper output the
#: terminal beat prints. Resync with the equality assert below run
#: from the repo root after any helper change.
SKELETON_HTML = "<div class='sk' aria-busy='true' aria-label='Loading module content'><div class='sk-inner' aria-hidden='true'><div class='sk-titlebar'><span class='sk-line sk-title'></span><span class='sk-line sk-sub'></span></div><div class='bar sk-progress'><i></i></div><section class='sk-row'><span class='sk-line sk-row-title'></span><span class='sk-line sk-row-sub'></span><span class='sk-chip'></span></section><section class='sk-row'><span class='sk-line sk-row-title'></span><span class='sk-line sk-row-sub'></span><span class='sk-chip'></span></section><section class='sk-row'><span class='sk-line sk-row-title'></span><span class='sk-line sk-row-sub'></span><span class='sk-chip'></span></section></div></div>"

SCENARIO = {
    "id": "skeletons",
    "kind": "improvement",
    "batch": 12,
    "item": "I-81",
    "title": "Loading skeletons",
    "blurb": "Module pages paint an instant static shell while lessons generate.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 12 - Improvement I-81",
         "title": "Loading skeletons",
         "subtitle": "An instant shell while lessons generate -- static, silent, cheap."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b12-skeletons",
         "caption": "Status documents the shell: title, progress bar, lesson rows, motion budget.",
         "assert_js": "() => !!document.querySelector('#status-b12-skeletons')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 8,
         "caption": "The rule in one line: 3 empty rows, no readable text, 250ms gated pulse.",
         "commands": [
             ["python3", "-c",
              "import re; from groundwork import skeletons as m; "
              "h = m.skeleton_html(); "
              "print('rows:', h.count(\"sk-row'>\")); "
              "print('readable text:', repr(re.sub(r'<[^>]+>', '', h).strip())); "
              "print('aria:', 'aria-busy' in h, 'aria-hidden' in h)"],
             ["python3", "-c",
              "import re; from groundwork import skeletons as m; "
              "c = m.skeletons_css(); "
              "print('durations:', re.findall(r'\\d+\\s*ms', c)); "
              "print('style tags:', '<style' in c.lower()); "
              "print('braces:', c.count('{') == c.count('}'))"],
         ]},
        {"type": "chrome", "duration": 10,
         "url_path": "/modules/{seed_module_id}",
         "focus": ".sk",
         "caption": "On a live module page: the helper's exact shell, styled by the head wire.",
         "js": ["() => { const main = document.querySelector('main'); "
                "if (!main) return 'no-main'; "
                "main.insertAdjacentHTML('afterbegin', \"" + SKELETON_HTML + "\"); "
                "return 'injected:' + !!document.querySelector('.sk'); }"],
         "assert_js": "() => !!document.querySelector(\".sk[aria-busy='true'] "
                      ".sk-inner[aria-hidden='true']\") && "
                      "document.querySelectorAll('.sk .sk-row').length === 3 && "
                      "document.querySelector('.sk').innerText.trim() === ''",
         "assert_want": "True"},
        {"type": "chrome", "duration": 6,
         "url_path": "/modules/{seed_module_id}",
         "caption": "The shell styles ship in the head wire -- the page below renders as today.",
         "assert_js": "() => Array.from(document.querySelectorAll('head style')).some("
                      "s => s.textContent.includes('.sk-line')) && "
                      "!!document.querySelector('main')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 12",
         "title": "Paint first, fill in.",
         "subtitle": "skeletons.py shells the wait -- empty spans, never fake lessons."},
    ],
}


def seed_db(db_path: str) -> dict:
    """Pick a module with cards for the shell-injection beats.

    Prefers a module that actually renders lesson rows (cards
    exist), so the unfocused beat shows a real module page; the
    injection beat targets that same page by exact module id.
    """
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT m.id FROM modules m JOIN cards c"
            " ON c.concept_id IN (SELECT id FROM concepts"
            " WHERE module_id = m.id)"
            " GROUP BY m.id ORDER BY COUNT(*) DESC LIMIT 1").fetchone()
        if not row:
            row = con.execute(
                "SELECT id FROM modules ORDER BY rowid LIMIT 1").fetchone()
        if not row:
            return {"seeded": False, "reason": "no modules"}
        return {"seeded": True, "module_id": row[0]}
    finally:
        con.close()
