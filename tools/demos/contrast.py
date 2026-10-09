"""Improvement demo: high-contrast mode (I-99).

Full behavior: a prefers-contrast block strengthens borders on the
existing chip/bar hooks and a forced-colors block maps them to
system colors, wired into the head stylesheet on every page -- so
high-contrast users keep legible chips, badges, and progress fills.
"""
from __future__ import annotations

SCENARIO = {
    "id": "contrast",
    "kind": "improvement",
    "batch": 18,
    "item": "I-99",
    "title": "High-contrast mode",
    "blurb": "Chips, badges, and progress bars stay legible under OS high-contrast and forced-colors -- system colors, not washed-out tints.",
    "beats": [
        {"type": "title", "duration": 5,
         "kicker": "Batch 18 - Improvement I-99",
         "title": "High-contrast mode",
         "subtitle": "System colors for chips and bars when the OS asks for contrast."},
        {"type": "terminal", "duration": 8,
         "caption": "Both override blocks in one call: stronger borders, then Canvas system colors.",
         "commands": [
             ["python3", "-c",
              "from groundwork import contrast as m; css = m.contrast_css(); "
              "print('prefers-contrast:', 'prefers-contrast' in css); "
              "print('forced-colors:', 'forced-colors' in css); "
              "print('system colors:', all(s in css for s in ('Canvas', 'CanvasText', 'Highlight'))); "
              "print('hooks:', m.CHIP_SELECTORS, m.BAR_SELECTORS)"],
         ]},
        {"type": "terminal", "duration": 8,
         "caption": "The wiring path: the overrides ride the head stylesheet on every page.",
         "commands": [
             ["python3", "-c",
              "from groundwork import contrast as m, web; "
              "print('head carries contrast:', m.contrast_css() in web.CSS); "
              "print('no style tags:', '<style' not in m.contrast_css())"],
         ]},
        {"type": "chrome", "duration": 6,
         "url_path": "/status",
         "focus": "#status-b18-contrast",
         "caption": "Status homes the improvement: existing hooks only, fills stay visible.",
         "assert_js": "() => !!document.querySelector('#status-b18-contrast')",
         "assert_want": "True"},
        {"type": "title", "duration": 5,
         "kicker": "Groundwork - Batch 18",
         "title": "Legible in any mode.",
         "subtitle": "contrast.py maps chips and bars to system colors -- fills never flatten."},
    ],
}
