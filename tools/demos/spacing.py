"""Improvement demo: section spacing scale (I-68).

Full behavior: every vertical gap derives from one base and ratio --
--sp-tight through --sp-display -- so rhythm grows in step with the
type scale instead of scattering magic rems. Roles (card, list,
page-head) map to steps; page CSS cites only the variables. Pure
tokens -- no seed data.
"""
from __future__ import annotations

SCENARIO = {
    "id": "spacing",
    "kind": "improvement",
    "batch": 11,
    "item": "I-68",
    "title": "Section spacing",
    "blurb": "One ratio rules vertical rhythm -- gaps grow with type.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 11 - Improvement I-68",
         "title": "Section spacing",
         "subtitle": "Vertical rhythm from one base, one ratio."},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b11-spacing",
         "caption": "Status homes the scale: seven steps, semantic roles, no literals.",
         "assert_js": "() => !!document.querySelector('#status-b11-spacing')",
         "assert_want": "True"},
        {"type": "terminal", "duration": 7,
         "caption": "The rule in one line: steps derive from base times ratio, roles ride steps.",
         "commands": [
             ["python3", "-c",
              "from groundwork import spacing as m; "
              "print('section:', m.rem_for('section'), 'page:', m.rem_for('page')); "
              "print('card role ->', m.rhythm_for('card')); "
              "print(m.spacing_css()[:150])"],
         ]},
        {"type": "chrome", "duration": 8,
         "url_path": "/due",
         "caption": "The live Due page carries the rhythm -- gaps cite only variables.",
         "assert_js": "() => Array.from(document.querySelectorAll('head style')).some("
                      "s => s.textContent.includes('--sp-section:1.0rem'))",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 11",
         "title": "Breathe in ratio.",
         "subtitle": "spacing.py spaces the page -- type and gaps stay proportional."},
    ],
}
