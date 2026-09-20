"""Character/line counts on code textareas (I-153).

Server-side count helper for writer size feedback. Pure functions
of the textarea text — no I/O, no DB changes.
"""
from __future__ import annotations

import html


def count_meta(text) -> dict:
    """Count chars, lines, and words in textarea text.

    Returns {"chars": int, "lines": int, "words": int}.
    None and non-string inputs are coerced (None -> "").
    """
    if text is None:
        text = ""
    if not isinstance(text, str):
        text = str(text)
    lines = text.splitlines() or ([""] if text == "" else [])
    if text == "":
        return {"chars": 0, "lines": 0, "words": 0}
    return {
        "chars": len(text),
        "lines": len(text.splitlines()),
        "words": len(text.split()),
    }


def textarea_hint(text) -> str:
    """One-line size hint rendered under a code textarea."""
    meta = count_meta(text)
    return (
        f"<span class='charcount'>{meta['chars']} chars · "
        f"{meta['lines']} lines · {meta['words']} words</span>"
    )


def _unused() -> str:  # pragma: no cover - keeps helper import-safe
    return html.escape("")
