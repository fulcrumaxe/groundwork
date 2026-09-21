"""Dark mode overrides + WCAG contrast helpers (I-52).

Dark-mode palette driven by prefers-color-scheme, reusing the
palette.py token source (never forked: DARK_OVERRIDES keys must match
PALETTE keys exactly). dark_css() emits one @media block that only
re-assigns the :root variables, so every styleguide component follows
with no selector duplication. luminance()/contrast_ratio() implement
WCAG relative-luminance math; AA_PAIRS lists the (fg, bg) token pairs
that must reach AA (>= 4.5) for body text, and check_contrast()
returns the failures. Pure functions, stdlib only, no I/O.
"""
from __future__ import annotations

from . import palette as palettemod

AA_MIN = 4.5
STATUS_ANCHOR = "status-b9-darkmode"

DARK_OVERRIDES = {
    "--ink": "#ececec",
    "--paper": "#121212",
    "--accent-due": "#5fd6ab",
    "--accent-modules": "#e3b34d",
    "--accent-history": "#93b8e8",
    "--pass": "#5fd6ab",
    "--fail": "#f08a91",
    "--stale": "#bdbdbd",
}

AA_PAIRS = (
    ("--ink", "--paper"),
    ("--paper", "--ink"),
    ("--accent-due", "--paper"),
    ("--accent-modules", "--paper"),
    ("--accent-history", "--paper"),
    ("--pass", "--paper"),
    ("--fail", "--paper"),
    ("--stale", "--paper"),
)


def _linearize(channel: float) -> float:
    """sRGB channel (0-1) to linear light."""
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _channels(hex_color: str) -> tuple:
    """Parse #rgb or #rrggbb into a (r, g, b) float triple."""
    h = (hex_color or "").strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(f"bad hex color: {hex_color!r}")
    try:
        return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        raise ValueError(f"bad hex color: {hex_color!r}")


def luminance(hex_color: str) -> float:
    """WCAG relative luminance of a hex color (0-1)."""
    r, g, b = _channels(hex_color)
    return (0.2126 * _linearize(r) + 0.7152 * _linearize(g)
            + 0.0722 * _linearize(b))


def _resolve(token: str) -> str:
    """Dark value for a token; falls back to the light palette."""
    if token in DARK_OVERRIDES:
        return DARK_OVERRIDES[token]
    return palettemod.PALETTE[token]


def contrast_ratio(fg: str, bg: str) -> float:
    """WCAG contrast ratio of two hex colors (1-21)."""
    lighter = max(luminance(fg), luminance(bg))
    darker = min(luminance(fg), luminance(bg))
    return (lighter + 0.05) / (darker + 0.05)


def check_contrast(pairs=AA_PAIRS, minimum: float = AA_MIN) -> list:
    """Failures as (fg_token, bg_token, ratio) below minimum; [] = AA pass."""
    failures = []
    for fg_token, bg_token in pairs:
        ratio = contrast_ratio(_resolve(fg_token), _resolve(bg_token))
        if ratio < minimum:
            failures.append((fg_token, bg_token, round(ratio, 2)))
    return failures


def dark_css() -> str:
    """One @media block re-assigning only the :root variables."""
    decls = "".join(f"{k}:{DARK_OVERRIDES[k]};"
                    for k in palettemod.PALETTE)
    return "@media (prefers-color-scheme: dark){:root{" + decls + "}}"


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    worst = min(
        (contrast_ratio(_resolve(fg), _resolve(bg)), fg, bg)
        for fg, bg in AA_PAIRS)
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Dark mode <small>(improvement)</small></h3>"
        "<p>Dark palette via <code>@media (prefers-color-scheme: dark)</code> "
        "re-assigning only the <code>:root</code> tokens from "
        "<code>groundwork/darkmode.py</code>; all "
        f"{len(AA_PAIRS)} AA body-text pairs pass >= 4.5 "
        f"(weakest {worst[1]} on {worst[2]}: {worst[0]:.2f}).</p>"
    )
