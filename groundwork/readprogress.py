"""Reading-progress bar per module page (I-120).

Pure server-HTML helper: renders a CSS-inline progress bar for a
0-100 percent value. No I/O, no DB changes. Reduced-motion safe:
static width via inline style, no transitions or animations.
"""
from __future__ import annotations


def _clamp(pct) -> int:
    try:
        v = float(pct)
    except (TypeError, ValueError):
        return 0
    if v != v:  # NaN
        return 0
    return max(0, min(100, int(v)))


def progress_bar(pct) -> str:
    """Progress bar HTML for a 0-100 value; stable id='readprogress'."""
    v = _clamp(pct)
    return (
        f"<div id='readprogress' role='progressbar' "
        f"aria-valuenow='{v}' aria-valuemin='0' aria-valuemax='100'>"
        f"<span style='width:{v}%'></span></div>"
    )
