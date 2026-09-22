"""Pass/fail verdict stamps: CSS-shape stamps, still text-readable (I-77).

Replaces the result-screen check/cross glyphs (``results.py`` renders
``"PASS"`` / ``"FAIL"`` text stamps inside ``<p class='verdict ok|stale'>``)
with rotated bordered stamps whose labels stay plain readable words
(``PASS`` / ``FAIL`` — never emoji, never glyphs). The words live in
the markup itself, so the verdict reads with CSS disabled; the stamp
look (rotation, double border, letter-spacing, pass/fail color) is
pure CSS. ``verdicts_css()`` returns raw declarations only, never
``<style>`` tags — the parent concatenates it into the head wire next
to ``progbar_css()``/``badge_css()``. Pure functions, stdlib only,
no I/O, no DB or schema changes.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b12-verdicts"

PASS_LABEL = "PASS"
FAIL_LABEL = "FAIL"

PASS_CLS = "verdict-stamp stamp-pass"
FAIL_CLS = "verdict-stamp stamp-fail"


def verdict_stamp(passed: bool) -> dict:
    """Stamp descriptor for a grading outcome; fails closed, never raises.

    Truthy ``passed`` maps to ``{"label": "PASS", "cls": ...pass}``,
    anything else (including unknown, ``None``, or garbage input) maps
    to the ``FAIL`` descriptor — never claim a pass on bad input.
    Labels are plain uppercase words, never emoji or glyphs.
    """
    try:
        if passed:
            return {"label": PASS_LABEL, "cls": PASS_CLS}
        return {"label": FAIL_LABEL, "cls": FAIL_CLS}
    except Exception:  # noqa: BLE001 — verdict lookup must never raise
        return {"label": FAIL_LABEL, "cls": FAIL_CLS}


def stamp_html(passed: bool) -> str:
    """Stamp ``<span>`` carrying the label as element text; never raises.

    The label is real text content (readable with CSS off), the stamp
    look comes from the ``verdicts_css()`` classes. Any failure falls
    back to the FAIL end state, which is always safe to show.
    """
    try:
        stamp = verdict_stamp(passed)
        label = stamp.get("label") or FAIL_LABEL
        cls = stamp.get("cls") or FAIL_CLS
        return (f"<span class='{html.escape(str(cls), quote=True)}'>"
                f"{html.escape(str(label), quote=True)}</span>")
    except Exception:  # noqa: BLE001 — markup must never raise
        return f"<span class='{FAIL_CLS}'>{FAIL_LABEL}</span>"


def verdicts_css() -> str:
    """Raw CSS declarations for the stamp look; NEVER ``<style>`` tags.

    Rotated bordered stamp: double border (``border`` + ``outline``),
    wide ``letter-spacing``, bold uppercase, pass/fail ink from the
    palette tokens (``var(--pass)`` / ``var(--fail)``). A
    ``prefers-reduced-motion`` override renders stamps unrotated.
    ASCII only — no emoji anywhere. Never raises.
    """
    try:
        return (
            ".verdict-stamp{display:inline-block;padding:.1em .6em;"
            "border:.18em solid currentColor;outline:.08em solid "
            "currentColor;outline-offset:.12em;border-radius:.25em;"
            "font-weight:800;letter-spacing:.18em;text-transform:uppercase;"
            "transform:rotate(-4deg)}"
            ".verdict-stamp.stamp-pass{color:var(--pass)}"
            ".verdict-stamp.stamp-fail{color:var(--fail);"
            "transform:rotate(3deg)}"
            "@media(prefers-reduced-motion:reduce){"
            ".verdict-stamp{transform:none}}"
        )
    except Exception:  # noqa: BLE001 — CSS emitter must never raise
        return (".verdict-stamp{display:inline-block;font-weight:800;"
                "letter-spacing:.18em;text-transform:uppercase}"
                ".verdict-stamp.stamp-pass{color:var(--pass)}"
                ".verdict-stamp.stamp-fail{color:var(--fail)}")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        samples = stamp_html(True) + " " + stamp_html(False)
    except Exception:  # noqa: BLE001 — status must never raise
        samples = ("<span class='verdict-stamp stamp-pass'>PASS</span> "
                   "<span class='verdict-stamp stamp-fail'>FAIL</span>")
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Verdict stamps "
        "<small>(improvement)</small></h3>"
        "<p>Result verdicts render as rotated bordered stamps — "
        "double border, wide letter-spacing, palette pass/fail ink — "
        "while the labels stay plain readable words, never emoji. "
        "Reduced-motion users see unrotated stamps. "
        f"Live samples: {samples} "
        "<code>groundwork/verdicts.py</code> provides "
        "<code>verdict_stamp()</code> (label/class descriptor that fails "
        "closed, never raises) and <code>verdicts_css()</code> (raw "
        "declarations only, no <code>&lt;style&gt;</code> tags — the "
        "parent concatenates it into the head wire).</p>"
    )


def tour_entry() -> dict:
    """Tour registry entry for this item; fails closed, never raises."""
    try:
        return {"id": "verdict-stamps", "kind": "improvement",
                "title": "Verdict stamps",
                "blurb": "Result verdicts stamp PASS or FAIL in rotated "
                         "bordered type — plain words, never emoji.",
                "path": "/status", "anchor": STATUS_ANCHOR}
    except Exception:  # noqa: BLE001 — registry must never raise
        return {"id": "verdict-stamps", "kind": "improvement",
                "title": "Verdict stamps",
                "blurb": "Result verdicts stamp PASS or FAIL.",
                "path": "/status", "anchor": "status-b12-verdicts"}
