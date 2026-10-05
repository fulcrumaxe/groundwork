"""Improvement demo: responsive audit (I-90).

Full behavior: the Status page audits 360/768/1024/1440 live over the
shipped stylesheet (reach per breakpoint, width branches), and the
audit's driven phone fixes (capped fields, stacking labels, wrapping
slider, breakable prose) ship in the head wire. The Due beat proves
the narrow rules ride a real queue page.
"""
from __future__ import annotations

SCENARIO = {
    "id": "responsive",
    "kind": "improvement",
    "batch": 13,
    "item": "I-90",
    "title": "Responsive audit",
    "blurb": "Four breakpoints audited live -- phone tables and padding fixed first.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 13 - Improvement I-90",
         "title": "Responsive audit",
         "subtitle": "360/768/1024/1440 under a lens -- phone fixes ship first."},
        {"type": "chrome", "duration": 8,
         "url_path": "/status",
         "focus": "#status-b13-responsive",
         "caption": "The live audit table: every breakpoint's reach over the shipped stylesheet.",
         "assert_js": "() => { const h = document.querySelector('#status-b13-responsive'); "
                      "if (!h) return false; "
                      "let n = h.nextElementSibling, found = ''; "
                      "while (n && !/^H[23]$/.test(n.tagName)) { found += n.textContent; n = n.nextElementSibling; } "
                      "return found.includes('360px') && found.includes('1440px'); }",
         "assert_want": "True"},
        {"type": "terminal", "duration": 9,
         "caption": "The rule in one line: branch widths audited, offenders named, phones fixed.",
         "commands": [
             ["python3", "-c",
              "from groundwork import responsive as m, web as w; "
              "print('branches:', m.media_boundaries(w.CSS)); "
              "print('reach 360:', m.coverage(w.CSS)[360]); "
              "print('offender:', m.overflow_offenders('<input style=\"width:500px\">')); "
              "print('narrow:', 'max-width:640px' in m.narrow_css().replace(' ', ''))"],
         ]},
        {"type": "chrome", "duration": 9,
         "url_path": "/due",
         "caption": "Due under the phone rules: capped fields, stacking labels, wrapping slider.",
         "assert_js": "() => { const css = [...document.querySelectorAll('style')]"
                      ".map(s => s.textContent).join('\\n'); "
                      "return css.includes('max-width:640px') && css.includes('.confslider'); }",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 13",
         "title": "Zero overflow at 360.",
         "subtitle": "responsive.py -- the audit stays live, wide tables belong to I-92."},
    ],
}
