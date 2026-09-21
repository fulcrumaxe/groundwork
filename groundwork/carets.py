"""Consistent custom carets for every details/summary disclosure (I-60).

All hint and grading disclosures render bare <details><summary>, whose
native marker looks different in each browser. carets_css() gives them
one shared CSS-drawn chevron that rotates on [open]. Pure CSS only —
no JS, no role/tabindex changes — so native keyboard handling and
screen-reader expanded-state announcements keep working as the
browser built them. Pure functions, stdlib only, no I/O.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b10-carets"


def _str(value) -> str:
    """Fail-closed string coercion; None -> "", never raises."""
    try:
        if value is None:
            return ""
        return value if isinstance(value, str) else str(value)
    except Exception:  # noqa: BLE001 — coercion must never raise
        return ""


def carets_css() -> str:
    """Raw CSS declarations for one consistent disclosure caret.

    Parent wires the return value into the head wire (NEVER <style>
    tags here). Closed caret points right; details[open] rotates it
    down. currentColor inherits the palette (incl. dark mode) with
    no color fork; reduced-motion users get no rotation animation.
    """
    return (
        "summary{list-style:none;cursor:pointer}"
        "summary::-webkit-details-marker{display:none}"
        "summary::marker{content:\"\"}"
        "summary::before{content:\"\";display:inline-block;width:.55em;"
        "height:.55em;margin-right:.45em;vertical-align:baseline;"
        "border-right:.14em solid currentColor;"
        "border-bottom:.14em solid currentColor;"
        "transform:rotate(-45deg) translateY(-.1em);"
        "transition:transform .15s ease-in-out}"
        "details[open]>summary::before{"
        "transform:rotate(45deg) translateY(-.1em)}"
        "@media (prefers-reduced-motion:reduce){"
        "summary::before{transition:none}}"
    )


def has_caret_rules(css) -> bool:
    """Fail-closed check that the caret rules reached the page CSS.

    True when both the marker-suppression and open-state rotation
    rules are present; hostile or partial input -> False, never raises.
    """
    try:
        text = _str(css)
        if not text:
            return False
        return ("summary::before" in text
                and "details[open]>summary::before" in text
                and "::-webkit-details-marker" in text)
    except Exception:  # noqa: BLE001 — audit must never raise
        return False


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Disclosure carets "
        "<small>(improvement)</small></h3>"
        "<p>Every hint and grading <code>details/summary</code> disclosure "
        "shares one CSS-drawn chevron: the native marker is suppressed, "
        "<code>summary::before</code> draws the caret, and "
        "<code>details[open]</code> rotates it down. Pure CSS — no JS, no "
        "role changes — so keyboard and screen-reader disclosure semantics "
        "stay native. <code>groundwork/carets.py</code> provides "
        "<code>carets_css()</code> (raw declarations the parent wires into "
        "the head wire) and <code>has_caret_rules()</code> (fail-closed "
        "wire audit, never raises).</p>"
    )
