"""Responsive breakpoints audit (I-90): 360/768/1024/1440 under a lens.

Nobody had ever checked what the app does on a phone: the shipped
stylesheet holds zero width-based ``@media`` rules, so small screens
get the desktop layout untouched. This module owns the audit: the
four breakpoints, ``media_boundaries`` (widths the CSS actually
branches on), ``coverage`` (which breakpoints any shipped rule
reaches), and ``overflow_offenders`` (inline fixed widths at or past
the smallest breakpoint — the classic 360px overflow).

The audit's first driven fix ships here too: ``narrow_css`` trims
phone rendering (smaller table text, tighter main padding under
640px — rules verified safe: no test asserts computed styles, and
``pre`` blocks already scroll via their own ``overflow:auto``).
Tables that need scroll wrappers stay counted, not fixed: that is
I-92's item, and this audit is its evidence. Raw declarations only,
never ``<style>`` tags; stdlib only (``re``), no I/O, no DB changes.
"""
from __future__ import annotations

import re

STATUS_ANCHOR = "status-b13-responsive"

#: Audit widths: phone, tablet, laptop, desktop.
BREAKPOINTS = (360, 768, 1024, 1440)

#: The audit's first driven fix only kicks in at phone widths.
NARROW_MAX = 640

_WIDTH_RE = re.compile(
    r"@media[^{]*?\(\s*(max|min)-width\s*:\s*(\d+)\s*px\s*\)",
    re.IGNORECASE)
_FIXED_RE = re.compile(
    r"(?:style\s*=\s*[\"'][^\"']*?width\s*:\s*(\d+)\s*px"
    r"|\swidth\s*=\s*[\"'](\d+)[\"'])",
    re.IGNORECASE)


def media_boundaries(css: str = "") -> list[int]:
    """Sorted widths from width-based ``@media`` rules; never raises."""
    try:
        if not isinstance(css, str):
            return []
        return sorted({int(m.group(2)) for m in _WIDTH_RE.finditer(css)})
    except Exception:  # noqa: BLE001 -- audit must never raise
        return []


def coverage(css: str = "") -> dict[int, bool]:
    """Per-breakpoint reach: a rule active at that width or not.

    A ``max-width:X`` rule applies at every breakpoint ``<= X``; a
    ``min-width:X`` rule at every breakpoint ``>= X``. Zero width
    rules means zero coverage — the audit says so plainly.
    """
    try:
        text = css if isinstance(css, str) else ""
        rules = [(m.group(1).lower(), int(m.group(2)))
                 for m in _WIDTH_RE.finditer(text)]
    except Exception:  # noqa: BLE001 -- audit must never raise
        rules = []
    out = {}
    for bp in BREAKPOINTS:
        out[bp] = any((kind == "max" and bound >= bp)
                      or (kind == "min" and bound <= bp)
                      for kind, bound in rules)
    return out


def overflow_offenders(html: str = "") -> list[str]:
    """Inline fixed widths at/above 360px: the classic phone overflow.

    Returns short ``"<tag-ish>:<width>px"`` notes (capped at 25);
    global-CSS sizing is out of scope — only inline values count.
    """
    try:
        if not isinstance(html, str):
            return []
        found = []
        for m in _FIXED_RE.finditer(html):
            width = int(m.group(1) or m.group(2))
            if width >= BREAKPOINTS[0]:
                found.append(f"fixed-{width}px")
        return found[:25]
    except Exception:  # noqa: BLE001 -- audit must never raise
        return []


def narrow_css() -> str:
    """Phone-first driven fixes (all <=640px, desktop untouched).

    Small tables, tighter padding, capped fields (the dispute
    form's ``size=50`` input overflowed 360px — and ``max-width`` is
    ignored on inline ``label``s, so form labels stack as blocks), a
    wrapping confidence slider (``inline-flex`` never wraps and
    fieldsets refuse to shrink below min-content, so both are
    overridden), and breakable prose (concept names, dots, and chips
    share one h3 line; unspaced JSON fills card bodies — both
    overflowed 360px until ``overflow-wrap`` gave them break
    opportunities). Verified overflow-free in a real 360px viewport
    during the batch run.
    """
    return (
        f"@media(max-width:{NARROW_MAX}px){{"
        "main{padding:0 .5rem}"
        "table{font-size:var(--fs-small)}"
        "input,select,textarea{max-width:100%;box-sizing:border-box}"
        "form label{display:block;max-width:100%}"
        ".confslider{flex-wrap:wrap;max-width:100%;min-inline-size:0}"
        "p,h1,h2,h3,li,summary,td{overflow-wrap:anywhere}}")


def section_html() -> str:
    """Status-page subsection: the live audit table over shipped CSS."""
    try:
        from . import web as webmod
        css = webmod.CSS
    except Exception:  # noqa: BLE001 -- status must never raise
        css = ""
    try:
        cov = coverage(css)
        bounds = media_boundaries(css)
        rows = "".join(
            f"<tr><td>{bp}px</td>"
            f"<td>{'covered' if cov[bp] else 'uncovered'}</td></tr>"
            for bp in BREAKPOINTS)
        bound_txt = (", ".join(f"{b}px" for b in bounds) or "none yet")
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Responsive audit <small>(improvement)</small></h3>"
            "<p>Four breakpoints under a lens — the table below is the "
            "live audit over the shipped stylesheet, not a snapshot: "
            "<code>groundwork/responsive.py</code> provides "
            "<code>coverage()</code>, <code>media_boundaries()</code>, "
            "and <code>overflow_offenders()</code>, plus "
            "<code>narrow_css()</code>, the audit's driven fixes "
            "(phone table text and padding, capped inputs, a wrapping "
            "confidence slider, breakable prose — the 360px overflows "
            "found in a real viewport, where /due now measures zero "
            "at all four widths). Wide data tables (Status overflows "
            "even at 1440px) belong to I-92's scroll wrappers, not "
            "silently fixed here."
            f" Width branches in the CSS: {bound_txt}.</p>"
            "<table class='log'><tr><th>Breakpoint</th><th>Reach</th></tr>"
            f"{rows}</table>")
    except Exception:  # noqa: BLE001 -- status must never raise
        return (f"<h3 id='{STATUS_ANCHOR}'>Responsive audit</h3>"
                "<p>Audit temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "responsive-audit",
        "kind": "improvement",
        "title": "Responsive audit",
        "blurb": "360/768/1024/1440 audited live over the shipped CSS — phone tables and padding fixed first.",
        "path": "/status",
        "anchor": "status-b13-responsive",
    }
