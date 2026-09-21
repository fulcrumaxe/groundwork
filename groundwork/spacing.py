"""Section spacing scale: one ratio-based source for vertical rhythm (I-68).

Mirrors typescale.py: every step derives from BASE_REM and RATIO (never a
magic literal), and spacing_css() emits a :root block of --sp-* variables
plus .rhythm-* class rules that reference only those variables. Font sizes
stay in typescale.py; fonts in fontstack.py; colors in palette.py; page
wiring stays in web.py. No DB changes.
"""
from __future__ import annotations

import re

BASE_REM = 1.0

# RATIO = 1.25, same as typescale.RATIO, so vertical gaps grow in step
# with the type scale above them — rhythm and type stay proportional.
RATIO = 1.25

_EXPONENTS = {
    "tight": -2,    # dense list items (today: .tour-steps li .6rem)
    "snug": -1,     # cards (today: .modcard .75rem)
    "section": 0,   # default section gap (today: section 1rem 0)
    "roomy": 1,     # separated blocks
    "page": 2,      # page head/foot breaks (today: h2/footer 2rem)
    "airy": 3,      # major landmarks
    "display": 4,   # hero/cover gaps
}

STEPS = {step: round(BASE_REM * (RATIO ** exp), 3)
         for step, exp in _EXPONENTS.items()}

# Section role -> scale step. Roles are semantic (where in the page),
# steps are sizes; the map is the rhythm.
RHYTHM = {
    "section": "section",
    "article": "section",
    "card": "snug",
    "list": "tight",
    "page-head": "page",
    "page-foot": "page",
    "banner": "roomy",
    "hero": "display",
}

STATUS_ANCHOR = "status-b11-spacing"

# Bare <section> opens only: sections already carrying a rhythm-*
# class pass through, and lookalike tags (<sections>) never match.
_SECTION_RE = re.compile(r"<section(?![^>]*\brhythm-)(?=[\s>])")


def rem_for(step) -> float:
    """Rem gap for a scale step; unknown steps fail closed to section."""
    try:
        return STEPS.get(step, STEPS["section"])
    except TypeError:  # unhashable step (e.g. a list): section, never raise
        return STEPS["section"]


def rhythm_for(role) -> str:
    """Scale step for a section role; unknown roles fail closed to section."""
    try:
        key = str(role).strip().lower()
        step = RHYTHM.get(key)
        if step in STEPS:
            return step
        return "section"
    except Exception:  # noqa: BLE001 — lookup must never raise
        return "section"


def spacing_css() -> str:
    """Return a :root block of --sp-* variables plus rhythm class rules.

    The :root block holds every computed gap; the .rhythm-* rules below
    it reference only var(--sp-*) so the scale stays single-sourced.
    """
    decls = "".join(f"--sp-{step}:{STEPS[step]}rem;" for step in STEPS)
    rules = "".join(
        f".rhythm-{step}{{margin-top:var(--sp-{step});"
        f"margin-bottom:var(--sp-{step})}}"
        for step in STEPS)
    return f":root{{{decls}}}{rules}"


def apply_rhythm(markup: str, role: str = "section") -> str:
    """Add the role's rhythm class to bare <section> tags in markup.

    Sections already carrying a rhythm-* class pass through untouched;
    non-string input returns "" instead of raising.
    """
    if not isinstance(markup, str):
        return ""
    cls = f"rhythm-{rhythm_for(role)}"
    return _SECTION_RE.sub(f"<section class='{cls}'", markup)


def audit_sections(markup: str) -> dict:
    """Count <section> tags with vs without a rhythm-* class.

    Returns {"total": n, "rhythmed": n, "bare": n}; non-string input
    yields all zeros instead of raising.
    """
    if not isinstance(markup, str):
        return {"total": 0, "rhythmed": 0, "bare": 0}
    total = len(re.findall(r"<section\b", markup))
    rhythmed = len(re.findall(r"<section[^>]*\brhythm-", markup))
    return {"total": total, "rhythmed": rhythmed, "bare": total - rhythmed}


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    rows = "".join(
        f"<tr><td>{step}</td><td>{STEPS[step]}rem</td>"
        f"<td><code>--sp-{step}</code></td></tr>"
        for step in STEPS)
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Section spacing <small>(improvement)</small></h3>"
        "<p>One ratio-based scale for every vertical gap — section, page, "
        "card, list — so rhythm comes from a single source instead of "
        "scattered literals. <code>groundwork/spacing.py</code> provides "
        "<code>STEPS</code> (ratio-derived gaps), <code>rhythm_for()</code> "
        "(role lookup that fails closed to section), "
        "<code>spacing_css()</code> (:root variables plus rhythm classes "
        "referencing only the variables), <code>apply_rhythm()</code> "
        "(tags bare sections), and <code>audit_sections()</code> "
        "(reports rhythm coverage).</p>"
        f"<table class='log'><tr><th>Step</th><th>Gap</th><th>Token</th></tr>{rows}</table>"
    )
