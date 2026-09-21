"""Segmented 1-5 confidence control replacing the text box (I-64).

Due cards already render five name='confidence' radios defaulting to 3
(cards._confidence); this module owns a drop-in replacement renderer
with the same POST contract — same field name, same values 1-5 — but
as a tappable segmented control: a fieldset/legend radio group with
native arrow-key behavior, screen-reader grouping, and zero-JS
operation. Pure functions, stdlib only (html), no I/O, no DB changes.
"""
from __future__ import annotations

import html as htmlmod

STATUS_ANCHOR = "status-b11-confslider"

LABELS = ("Unsure", "Shaky", "OK", "Solid", "Sure")

_DEFAULT = 3
_MIN = 1
_MAX = 5


def normalize(value) -> int:
    """Clamp a confidence value to 1-5; garbage fails closed to 3."""
    try:
        if isinstance(value, bool):
            return _DEFAULT
        num = int(value)
        if num < _MIN or num > _MAX:
            return _DEFAULT
        return num
    except (TypeError, ValueError):
        return _DEFAULT
    except Exception:  # noqa: BLE001 — coercion must never raise
        return _DEFAULT


def slider_html(value: int = 3, name: str = "confidence", extra: str = "") -> str:
    """Segmented radio group posting the same field as cards._confidence.

    Exactly five radios named `name` with values 1-5, checked on
    normalize(value); a fieldset/legend (not div/span) gives native
    arrow-key radio-group behavior with no JS. Never raises.
    """
    try:
        field = name if isinstance(name, str) and name.strip() else "confidence"
        field = htmlmod.escape(field, quote=True)
        checked = normalize(value)
        tail = extra if isinstance(extra, str) else ""
        segs = "".join(
            f"<label class='confslider-seg'>"
            f"<input type='radio' name='{field}' value='{i}'"
            f"{' checked' if i == checked else ''}>"
            f"<span>{LABELS[i - 1]}</span></label>"
            for i in (_MIN, _MIN + 1, _MIN + 2, _MIN + 3, _MAX))
        return (f"<fieldset class='confslider'{tail}>"
                f"<legend>Confidence</legend>{segs}</fieldset>")
    except Exception:  # noqa: BLE001 — renderer must never raise
        return ("<fieldset class='confslider'><legend>Confidence</legend>"
                "</fieldset>")


def odds_html() -> str:
    """Explicit drill odds per confidence level (Batch 15, F-66).

    One compact line — win/lose at fair odds for 1–5 — rendered where
    confidence is stated, so every bet shows its price. Never raises.
    """
    try:
        from . import calibdrill as drillmod
        bits = []
        for c in (1, 2, 3, 4, 5):
            deal = drillmod.offer(c)
            bits.append(f"{c}→+{deal['win']}/{deal['lose']}")
        return "<small class='odds'>Odds — " + " · ".join(bits) + "</small>"
    except Exception:  # noqa: BLE001 -- display must never raise
        return ""


def css() -> str:
    """Scoped segmented-bar styles; no global resets, outlines kept."""
    return (
        ".confslider{display:inline-flex;gap:0;border:0;padding:0;margin:0}"
        ".confslider legend{padding:0;margin-right:.5em}"
        ".confslider-seg{padding:.4em .7em;min-height:44px;"
        "display:inline-flex;align-items:center;cursor:pointer;"
        "border:1px solid currentColor}"
        ".confslider-seg:first-of-type{border-radius:8px 0 0 8px}"
        ".confslider-seg:last-of-type{border-radius:0 8px 8px 0}"
        ".confslider-seg input{accent-color:currentColor}"
        ".confslider-seg:has(input:checked){"
        "background:color-mix(in srgb,currentColor 14%,transparent)}"
        ".confslider-seg input:focus-visible{"
        "outline:3px solid var(--accent-history);outline-offset:2px}"
        "@media (prefers-reduced-motion:reduce){"
        ".confslider-seg{transition:none}}"
    )


def tour_entry() -> dict:
    """Tour registry entry for the segmented confidence control."""
    return {
        "id": "conf-slider",
        "kind": "improvement",
        "title": "Segmented confidence slider",
        "blurb": ("Rate confidence 1–5 on a tappable segmented control "
                  "with arrow-key support — same rating, no typing."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Confidence slider "
        "<small>(improvement)</small></h3>"
        "<p>Rate confidence 1–5 on a tappable segmented radio group "
        "instead of a text box — fieldset/legend gives arrow-key support "
        "and screen-reader grouping with no JS, and the posted field "
        "name is unchanged. <code>groundwork/confslider.py</code> provides "
        "<code>slider_html()</code> (drop-in for "
        "<code>cards._confidence</code>), <code>normalize()</code> "
        "(clamps to 1–5, fails closed to 3), and <code>css()</code> "
        "(scoped segments, <code>:focus-visible</code> ring kept).</p>"
        f"{slider_html()}"
    )
