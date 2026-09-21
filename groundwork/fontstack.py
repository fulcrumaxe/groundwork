"""Distinctive offline-safe font pairing: headings + body + mono (I-54).

Replaces the system-ui-only stack with three named system-font stacks
behind :root --font-* variables. Every name resolves to a face that
ships with the OS — no webfonts, no downloads, no network — and each
stack ends in its CSS generic family so rendering never falls off a
cliff. This module sets font-family ONLY: sizes stay with
typescale.py (var(--fs-*) references), colors stay in palette.py.
Pure functions, stdlib only, no I/O.
"""
from __future__ import annotations

# Offline-safe: Georgia/Palatino/Book Antiqua ship with Windows and macOS;
# DejaVu Serif covers stock Linux; the serif terminator is the guarantee.
HEADING_STACK = (
    "Georgia",
    "Palatino Linotype",
    "Palatino",
    "Book Antiqua",
    "DejaVu Serif",
    "serif",
)

# Offline-safe: Segoe UI (Windows), Helvetica Neue (macOS), Roboto
# (Android/most Linux desktops), Arial + DejaVu Sans (universal);
# the sans-serif terminator is the guarantee.
BODY_STACK = (
    "Segoe UI",
    "Roboto",
    "Helvetica Neue",
    "Arial",
    "DejaVu Sans",
    "sans-serif",
)

# Offline-safe: SFMono-Regular/Menlo (macOS), Consolas (Windows),
# Liberation Mono/DejaVu Sans Mono (Linux); monospace terminates.
MONO_STACK = (
    "SFMono-Regular",
    "Menlo",
    "Consolas",
    "Liberation Mono",
    "DejaVu Sans Mono",
    "monospace",
)

STACKS = {
    "heading": HEADING_STACK,
    "body": BODY_STACK,
    "mono": MONO_STACK,
}

_ROLES = tuple(STACKS)
STATUS_ANCHOR = "status-b9-fontstack"


def _family(name: str) -> str:
    """Quote one family name for CSS when it contains whitespace."""
    text = str(name)
    if " " in text and not text.startswith('"'):
        return f'"{text}"'
    return text


def stack_for(role) -> tuple:
    """Return the family tuple for a role; never raises.

    Unknown, empty, or non-string roles fail closed to BODY_STACK,
    the most readable face, so a caller typo can never break rendering.
    """
    try:
        key = str(role).strip().lower()
        stack = STACKS.get(key)
        if isinstance(stack, tuple) and stack:
            return stack
        return BODY_STACK
    except Exception:  # noqa: BLE001 — lookup must never raise
        return BODY_STACK


def stack_font(role) -> str:
    """Comma-separated font-family value for one role."""
    return ", ".join(_family(f) for f in stack_for(role))


def stack_css() -> str:
    """Return :root --font-* variables plus font-family element rules.

    Font-family ONLY — no font-size declarations (those belong to
    typescale.py's --fs-* rules, so the scale stays single-sourced).
    """
    root = (":root{--font-heading:" + stack_font("heading") + ";"
            "--font-body:" + stack_font("body") + ";"
            "--font-mono:" + stack_font("mono") + ";}")
    rules = (
        "body{font-family:var(--font-body)}"
        "h1,h2,h3,h4{font-family:var(--font-heading)}"
        ".display{font-family:var(--font-heading)}"
        "code,pre,kbd,samp{font-family:var(--font-mono)}"
    )
    return root + rules


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Font pairing <small>(improvement)</small></h3>"
        "<p>Headings speak serif (Georgia-led), body speaks sans, code speaks "
        "mono — every face ships with the OS, so there are no webfonts and no "
        "downloads. Each stack ends in its generic family, so text always "
        "renders. <code>groundwork/fontstack.py</code> provides "
        "<code>stack_css()</code> (:root <code>--font-*</code> variables plus "
        "font-family rules; sizes stay with <code>typescale.py</code>) and "
        "<code>stack_for()</code> (role lookup "
        "that fails closed to the body stack, never raises).</p>"
    )
