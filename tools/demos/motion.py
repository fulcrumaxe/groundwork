"""Improvement demo: motion budget (I-98).

Full behavior: every animation ships inside one 300ms budget and
every keyframe is prefers-reduced-motion gated; audit_css pins the
whole head wire, so a 400ms ad-hoc animation fails loudly instead
of shipping.
"""
from __future__ import annotations

SCENARIO = {
    "id": "motion",
    "kind": "improvement",
    "batch": 18,
    "item": "I-98",
    "title": "Motion budget",
    "blurb": "Every animation finishes in 300ms or less, and reduced-motion users always see the still end state.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Improvement I-98",
         "title": "Motion budget",
         "subtitle": "Five shared keyframes, all within 300ms, all reduced-motion gated."},
        {"type": "terminal", "duration": 8,
         "caption": "The budget in one call: shared CSS audits clean, a 400ms plant fails.",
         "commands": [
             ["python3", "-c",
              "from groundwork import motion as m; "
              "print('keyframes:', m.keyframes()); "
              "print('own css audits:', m.audit_css(m.motion_css())); "
              "print('400ms plant:', m.audit_css('.x{animation:spin 400ms}'))"],
         ]},
        {"type": "terminal", "duration": 8,
         "caption": "The enforcement path: the served head wire audits inside budget.",
         "commands": [
             ["python3", "-c",
              "from groundwork import motion as m, web; "
              "print('head carries motion:', m.motion_css() in web.CSS); "
              "print('head audits:', m.audit_css(web.CSS))"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-motion",
         "caption": "Status homes the improvement: one table, one override block, static end state.",
         "assert_js": "() => !!document.querySelector('#status-b18-motion')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "300ms, then still.",
         "subtitle": "motion.py owns the budget -- the audit pins every shipped duration."},
    ],
}
