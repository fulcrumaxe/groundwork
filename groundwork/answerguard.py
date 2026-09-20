"""Inline empty-answer validation guard (I-151).

Pure server-side check run before submit: blank answers get an inline
warning instead of a silent submit. No DB, no HTTP, no page chrome.
"""
from __future__ import annotations

import html


def guard(answer, min_chars: int = 1) -> dict:
    """Check an answer for empty/blank input before submit.

    Returns {"ok": bool, "warning": str}: ok=True with warning=""
    when the answer meets min_chars of non-space text.
    """
    try:
        need = max(1, int(min_chars))
    except (TypeError, ValueError):
        need = 1
    text = "" if answer is None else answer if isinstance(answer, str) else str(answer)
    if len(text.strip()) >= need:
        return {"ok": True, "warning": ""}
    return {"ok": False, "warning": "Answer looks empty — write something before submitting."}


def guard_html(warning: str) -> str:
    """Inline warning HTML; empty string when there is no warning."""
    if not warning or not isinstance(warning, str):
        return ""
    return f"<p class='guard-warn' role='alert'>{html.escape(warning)}</p>"
