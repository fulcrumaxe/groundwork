"""Visually differentiated hint tiers: nudge, pointer, worked step (I-63).

Card and lesson hints always build [nudge, pointer, worked] but render
every tier identically as bare <details><summary>Hint N</summary>, so
learners cannot tell cheap help from a full worked step. This module
owns the one pure tier map plus tiered renderers: tier_of() maps a
hint position to its tier, tier_class()/tier_label() map tiers (or
positions) to CSS classes and labels, hint_html()/hints_html() render
tiered disclosures with the same progressive-reveal prefix semantics
as cards.hints_html, and hinttiers_css() ships the raw declarations
the parent wires into the head wire. Pure functions, stdlib only
(html), no I/O, no DB changes.
"""
from __future__ import annotations

import html as htmlmod

TIERS = ("nudge", "pointer", "worked")

TIER_CLASS = {
    "nudge": "hint-nudge",
    "pointer": "hint-pointer",
    "worked": "hint-worked",
}

TIER_LABEL = {
    "nudge": "Nudge",
    "pointer": "Pointer",
    "worked": "Worked step",
}

STATUS_ANCHOR = "status-b11-hinttiers"


def _tier_name(value) -> str:
    """Coerce a tier name; unknown or hostile input fails closed to nudge."""
    try:
        if isinstance(value, str):
            key = value.strip().lower()
            if key in TIER_CLASS:
                return key
    except Exception:  # noqa: BLE001 — lookup must never raise
        pass
    return "nudge"


def tier_of(index, total: int = 3) -> str:
    """Tier for a hint position: first is the nudge, last the worked step.

    Out-of-range indices clamp to the nearest end; non-int or hostile
    input fails closed to "nudge"; a degenerate total still answers.
    Never raises.
    """
    try:
        if isinstance(index, bool) or not isinstance(index, int):
            return "nudge"
        try:
            size = int(total)
        except (TypeError, ValueError):
            return "nudge"
        if size <= 1:
            return "nudge" if index <= 0 else "worked"
        if index <= 0:
            return "nudge"
        if index >= size - 1:
            return "worked"
        return "pointer"
    except Exception:  # noqa: BLE001 — mapping must never raise
        return "nudge"


def tier_class(tier_or_index) -> str:
    """CSS class for a tier name or hint position; never raises."""
    try:
        if isinstance(tier_or_index, bool):
            return TIER_CLASS["nudge"]
        if isinstance(tier_or_index, int):
            return TIER_CLASS[tier_of(tier_or_index)]
        return TIER_CLASS[_tier_name(tier_or_index)]
    except Exception:  # noqa: BLE001 — mapping must never raise
        return TIER_CLASS["nudge"]


def tier_label(tier_or_index) -> str:
    """Human label for a tier name or hint position; never raises."""
    try:
        if isinstance(tier_or_index, bool):
            return TIER_LABEL["nudge"]
        if isinstance(tier_or_index, int):
            return TIER_LABEL[tier_of(tier_or_index)]
        return TIER_LABEL[_tier_name(tier_or_index)]
    except Exception:  # noqa: BLE001 — mapping must never raise
        return TIER_LABEL["nudge"]


def hinttiers_css() -> str:
    """Raw CSS declarations for the three hint tiers.

    Parent wires the return value into the head wire (NEVER <style>
    tags here). Tiers differ by border weight/style as well as hue so
    they stay distinguishable without color vision; currentColor
    inheritance keeps dark mode single-sourced; reduced-motion users
    keep the static styling with no transition.
    """
    return (
        ".hint-nudge{border-left:.2em dotted currentColor;"
        "padding-left:.6em}"
        ".hint-pointer{border-left:.3em dashed currentColor;"
        "padding-left:.6em}"
        ".hint-worked{border-left:.4em solid currentColor;"
        "padding-left:.6em;background:color-mix("
        "in srgb,currentColor 6%,transparent)}"
        "details.hint-nudge>summary .hint-tag,"
        "details.hint-pointer>summary .hint-tag,"
        "details.hint-worked>summary .hint-tag{"
        "font-weight:bold}"
        "details[open].hint-nudge>summary .hint-tag,"
        "details[open].hint-pointer>summary .hint-tag,"
        "details[open].hint-worked>summary .hint-tag{"
        "text-decoration:underline}"
        "@media (prefers-reduced-motion:reduce){"
        ".hint-nudge,.hint-pointer,.hint-worked{transition:none}}"
    )


def has_hinttier_rules(css) -> bool:
    """Fail-closed check that the tier rules reached the page CSS.

    True when all three tier class selectors plus an open-state rule
    are present; hostile or partial input -> False, never raises.
    """
    try:
        if not isinstance(css, str) or not css:
            return False
        return (".hint-nudge" in css
                and ".hint-pointer" in css
                and ".hint-worked" in css
                and "details[open]" in css)
    except Exception:  # noqa: BLE001 — audit must never raise
        return False


def hint_html(text, index: int = 0, total: int = 3) -> str:
    """One tiered hint disclosure; empty or None text renders nothing."""
    try:
        if text is None:
            return ""
        body = text if isinstance(text, str) else str(text)
        if not body.strip():
            return ""
        cls = tier_class(index)
        label = tier_label(index)
        _ = total  # accepted for call-site symmetry; tier derives from index
        return (
            f"<details class='{cls}'><summary>"
            f"<span class='hint-tag'>{label}</span></summary>"
            f"{htmlmod.escape(body)}</details>"
        )
    except Exception:  # noqa: BLE001 — renderer must never raise
        return ""


def hints_html(hints, attempts: int = 0) -> str:
    """Progressive tiered reveal mirroring cards.hints_html semantics.

    The visible prefix is 1+attempts hints; empty input renders "";
    the wrapper carries id='hints' so the tour entry has a stable
    target. Never raises.
    """
    try:
        if not isinstance(hints, (list, tuple)) or not hints:
            return ""
        try:
            count = 1 + int(attempts)
        except (TypeError, ValueError):
            count = 1
        shown = list(hints)[:max(0, min(len(hints), count))]
        if not shown:
            return ""
        total = len(hints)
        return ("<div id='hints'>" + "".join(
            hint_html(h, i, total) for i, h in enumerate(shown)) + "</div>")
    except Exception:  # noqa: BLE001 — renderer must never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Hint tiers "
        "<small>(improvement)</small></h3>"
        "<p>Card and lesson hints carry "
        "<code>hint-nudge</code>/<code>hint-pointer</code>/"
        "<code>hint-worked</code> classes driven by one pure tier map, "
        "so the cheapest help looks cheapest; progressive reveal order "
        "is unchanged. <code>groundwork/hinttiers.py</code> provides "
        "<code>tier_class()</code>/<code>tier_label()</code> (web.py "
        "delegates), <code>hinttiers_css()</code> (raw declarations for "
        "the head wire), and <code>has_hinttier_rules()</code> "
        "(fail-closed audit).</p>"
    )
