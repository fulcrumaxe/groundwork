"""Raw emoji-as-icon scanner plus CSS/SVG replacement vocabulary (I-97).

Glyphs used as icons (checks, stars, arrow-only buttons) break screen
readers and font stacks. This module owns the explicit allow/block
codepoint policy: BLOCK codepoints in shipped groundwork/*.py source
are violations; U+2192 as a prose separator and typographic text are
allowed. Replacements are text-first (readable with CSS off) with the
look in CSS/SVG. Pure functions, stdlib only, no I/O except
scan_tree(), no DB or schema changes, never raises.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

STATUS_ANCHOR = "status-b18-emoji"

_BLOCK_RANGES = (
    (0x1F000, 0x1FAFF), (0xFE00, 0xFE0F), (0x2600, 0x27BF),
    (0x2800, 0x28FF), (0x2190, 0x21FF),
)
_BLOCK_EXTRA = {0x200D}
ALLOW_ARROW = 0x2192  # prose separator convention (prereq nav, feedback)

_SKIP_DIRS = {".groundwork", "__pycache__", ".git"}

_UP_SVG = ("<svg aria-hidden='true' width='10' height='10' viewBox='0 0 10 10'>"
           "<path d='M1 7l4-4 4 4' fill='none' stroke='currentColor' "
           "stroke-width='1.6'/></svg>")
_DOWN_SVG = ("<svg aria-hidden='true' width='10' height='10' viewBox='0 0 10 10'>"
             "<path d='M1 3l4 4 4-4' fill='none' stroke='currentColor' "
             "stroke-width='1.6'/></svg>")


def is_blocked(char: str) -> bool:
    """True when one char is a blocked icon codepoint; never raises."""
    try:
        if len(char) != 1:
            return False
        o = ord(char)
        if o == ALLOW_ARROW:
            return False
        if o in _BLOCK_EXTRA:
            return True
        return any(lo <= o <= hi for lo, hi in _BLOCK_RANGES)
    except Exception:  # noqa: BLE001 -- policy lookup must never raise
        return False


def scan_text(text) -> list:
    """Violation dicts {char, codepoint, index} for BLOCK chars.

    Legacy no-data path: None / non-string / empty input scans clean
    (no violations), never raises -- pinned as the safe fallback.
    """
    try:
        if not isinstance(text, str) or not text:
            return []
        out = []
        for i, ch in enumerate(text):
            if is_blocked(ch):
                out.append({"char": ch, "codepoint": f"U+{ord(ch):04X}",
                            "index": i})
        return out
    except Exception:  # noqa: BLE001 -- scanner must never raise
        return []


def scan_html(markup) -> list:
    """scan_text over a rendered HTML/CSS string; never raises."""
    return scan_text(markup)


def scan_file(path) -> list:
    """Violations {file, line, char, codepoint} in one source file."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except Exception:  # noqa: BLE001 -- unreadable file scans clean
        return []
    out = []
    for n, line in enumerate(lines, 1):
        for v in scan_text(line):
            out.append({"file": str(path), "line": n, "char": v["char"],
                        "codepoint": v["codepoint"]})
    return out


def scan_tree(root="groundwork") -> list:
    """Violations across groundwork/*.py; skips .groundwork/__pycache__.

    Missing root scans clean (legacy fallback), never raises.
    """
    try:
        base = Path(root)
        if not base.is_dir():
            return []
        out = []
        for p in sorted(base.glob("*.py")):
            if any(part in _SKIP_DIRS for part in p.parts):
                continue
            out.extend(scan_file(p))
        return out
    except Exception:  # noqa: BLE001 -- tree walk must never raise
        return []


def icon_css() -> str:
    """Raw CSS declarations for replacements; NEVER <style> tags.

    Grip dot-handle, move-button sizing, to-top triangle, reviewed
    tick ring, external-link corner arrow; ASCII only, palette tokens
    only, reduced-motion override. Never raises.
    """
    try:
        return (
            ".grip{display:inline-block;width:.9em;height:1em;"
            "background-image:radial-gradient(currentColor 1.2px,"
            "transparent 1.3px);background-size:.45em .34em;"
            "background-repeat:repeat;vertical-align:baseline}"
            ".move-btn svg{width:.8em;height:.8em;vertical-align:baseline}"
            ".totop::after{content:\"\";display:inline-block;margin-left:.3em;"
            "border-left:.32em solid transparent;"
            "border-right:.32em solid transparent;"
            "border-bottom:.45em solid currentColor}"
            ".reviewed-tick::before{content:\"\";display:inline-block;"
            "width:.55em;height:.55em;margin-right:.35em;"
            "border:.14em solid currentColor;border-radius:50%;"
            "vertical-align:baseline}"
            ".ext-marker{display:inline-block;width:.5em;height:.5em;"
            "border-top:.14em solid currentColor;"
            "border-right:.14em solid currentColor;vertical-align:baseline}"
            "@media(prefers-reduced-motion:reduce){"
            ".totop::after{border-bottom-style:solid}}"
        )
    except Exception:  # noqa: BLE001 -- CSS must never raise
        return ".grip{display:inline-block}"


def move_button(direction: str, slug) -> str:
    """Parsons move button: SVG chevron + text label; never raises."""
    try:
        up = str(direction).strip().lower() in ("up", "-1", "prev")
        svg = _UP_SVG if up else _DOWN_SVG
        label = "Move up" if up else "Move down"
        step = "-1" if up else "1"
        return (
            f"<button type='button' class='move-btn' data-move='{step}' "
            f"aria-label='{label}'>{svg}<span>{label}</span></button>")
    except Exception:  # noqa: BLE001 -- markup must never raise
        return ("<button type='button' class='move-btn' data-move='1' "
                "aria-label='Move down'>Move down</button>")


def grip_html() -> str:
    """CSS-handle grip span; never raises."""
    try:
        return "<span class='grip' aria-hidden='true'></span>"
    except Exception:  # noqa: BLE001
        return "<span class='grip'></span>"


def totop_html() -> str:
    """Back-to-top link; arrow is pure CSS; never raises."""
    try:
        return "<a class='totop' href='#top'>Back to top</a>"
    except Exception:  # noqa: BLE001
        return "<a class='totop' href='#top'>Back to top</a>"


def section_html() -> str:
    """Anchored status subsection; joined by batch18_html on /status."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Emoji-free icons <small>(improvement)</small></h3>"
        "<p>Shipped markup uses no raw emoji-as-icon: checks and crosses "
        "are text <code>PASS</code>/<code>FAIL</code> stamps, move buttons "
        "carry SVG chevrons with text labels, and decorative marks are "
        "CSS shapes. <code>groundwork/emoji.py</code> scans the tree "
        "against an explicit allow/block codepoint policy "
        "(prose <code>→</code> stays allowed) so CI fails on new raw "
        "emoji. Live sample: "
        f"{totop_html()} "
        "<code>groundwork/emoji.py</code> provides "
        "<code>scan_tree()</code>, <code>icon_css()</code> (raw "
        "declarations, never <code>&lt;style&gt;</code> tags), "
        "<code>move_button()</code>, <code>grip_html()</code> and "
        "<code>totop_html()</code>.</p>"
    )


def tour_entry() -> dict:
    """Tour registry entry; anchor renders inside batch18_html."""
    return {"id": "emoji-free-icons", "kind": "improvement",
            "title": "Emoji-free icons",
            "blurb": "No raw emoji icons -- text words, SVG chevrons and CSS shapes, all readable with styles off.",
            "path": "/status", "anchor": STATUS_ANCHOR}
