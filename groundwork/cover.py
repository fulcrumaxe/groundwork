"""Per-module cover color from repo hash (stable identity) (I-74).

MD5 of the repo string -> hue (0-359) -> hex color via HLS.
Pure function of the repo string — no I/O, no DB changes, stdlib only.
"""
from __future__ import annotations

import colorsys
import hashlib
import html

_SATURATION = 0.55
_LIGHTNESS = 0.45


def cover_color(repo) -> str:
    """Stable hex color for a repo, e.g. '#3fa9c8'."""
    if not isinstance(repo, str) or not repo:
        repo = "groundwork"
    digest = hashlib.md5(repo.encode("utf-8")).hexdigest()
    hue = int(digest[:4], 16) % 360
    r, g, b = colorsys.hls_to_rgb(hue / 360.0, _LIGHTNESS, _SATURATION)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def cover_html(repo) -> str:
    """Cover swatch HTML; stable id='cover' anchor."""
    color = cover_color(repo)
    safe = html.escape(repo if isinstance(repo, str) else "", quote=True)
    return (
        f"<span id='cover' class='cover' style='background:{color}' "
        f"title='{safe}' aria-label='Module cover for {safe}'></span>"
    )
