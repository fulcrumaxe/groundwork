"""Common-misconceptions callout per lesson (I-111).

Static HTML renderer for one misconception string — no I/O, no DB changes.
"""
from __future__ import annotations

import html


def callout(misconception: str) -> str:
    """Misconception callout box; empty input renders as empty string."""
    if not isinstance(misconception, str) or not misconception.strip():
        return ""
    return (
        "<aside class='misconception' id='misconception'>"
        "<p><strong>Common misconception</strong></p>"
        f"<p>{html.escape(misconception.strip())}</p></aside>"
    )
