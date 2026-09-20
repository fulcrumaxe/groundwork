"""One-question exit ticket per lesson (ungraded retrieval) (I-113).

Pure HTML renderer for a single lesson-closing prompt. Ungraded by
design: no grade handling, no POST to review endpoints, no DB writes.
"""
from __future__ import annotations

import html


def ticket_html(concept, prompt) -> str:
    """Ungraded exit-ticket form; stable id='exitticket' anchor."""
    name = concept if isinstance(concept, str) else ""
    text = prompt if isinstance(prompt, str) else ""
    if not name.strip() and not text.strip():
        return ""
    return (
        "<form id='exitticket' class='exit-ticket'>"
        f"<p>Exit ticket — {html.escape(name)} (ungraded)</p>"
        f"<p>{html.escape(text)}</p>"
        "<textarea name='exit-answer' rows='3'></textarea>"
        "</form>"
    )
