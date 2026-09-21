"""Modular type scale: one ratio-based source for all font sizes (I-53).

Single source for display, h1-h4, body, small, and code sizes. Every
step is computed from BASE_PX and RATIO (never a magic literal), and
scale_css() emits a :root block of --fs-* variables plus element rules
that reference only those variables. Color tokens stay in palette.py;
dark-mode overrides stay in darkmode.py; page wiring stays in web.py.
No DB changes.
"""
from __future__ import annotations

BASE_PX = 16.0

# RATIO = 1.25 (major third): wide enough to separate adjacent heading
# levels, narrow enough to keep display usable — the classic
# modular-scale step.
RATIO = 1.25

_EXPONENTS = {
    "display": 5,
    "h1": 4,
    "h2": 3,
    "h3": 2,
    "h4": 1,
    "body": 0,
    "small": -1,
    "code": -1,
}

STEPS = {step: round(BASE_PX * (RATIO ** exp), 2)
         for step, exp in _EXPONENTS.items()}

_ELEMENTS = (
    ("h1", "h1"),
    ("h2", "h2"),
    ("h3", "h3"),
    ("h4", "h4"),
    ("body", "body"),
    ("small", "small"),
    ("code", "code,pre"),
)

STATUS_ANCHOR = "status-b9-typescale"


def px_for(step) -> float:
    """Pixel size for a scale step; unknown steps fail closed to body."""
    try:
        return STEPS.get(step, STEPS["body"])
    except TypeError:  # unhashable step (e.g. a list): body, never raise
        return STEPS["body"]


def scale_css() -> str:
    """Return a :root block of --fs-* variables plus element rules.

    The :root block holds every computed size; the element rules below
    it reference only var(--fs-*) so the scale stays single-sourced.
    """
    decls = "".join(f"--fs-{step}:{STEPS[step]}px;" for step in STEPS)
    rules = "".join(f"{sel}{{font-size:var(--fs-{step})}}"
                    for step, sel in _ELEMENTS)
    return f":root{{{decls}}}{rules}"


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    rows = "".join(
        f"<tr><td>{step}</td><td>{STEPS[step]}px</td>"
        f"<td><code>--fs-{step}</code></td></tr>"
        for step in STEPS)
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Type scale <small>(improvement)</small></h3>"
        "<p>One ratio-based scale for every font size — display, h1-h4, "
        "body, small, code — so sizes come from a single source instead of "
        "scattered literals. <code>groundwork/typescale.py</code> provides "
        "<code>STEPS</code> (ratio-derived sizes), <code>px_for()</code> "
        "(lookup that fails closed to body), and <code>scale_css()</code> "
        "(:root variables plus element rules referencing only the variables).</p>"
        f"<table class='log'><tr><th>Step</th><th>Size</th><th>Token</th></tr>{rows}</table>"
    )
