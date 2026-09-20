"""Empty states with a next action (I-12).

One pure helper for every page that can run dry — no dead ends.
Pure function of the page key — no I/O, no DB changes.
"""
from __future__ import annotations

_NEXT = {
    "due": ("No cards due.", "/modules", "Study the library"),
    "modules": ("No modules yet.", "/status", "Check the machine room"),
    "history": ("No attempts yet.", "/due", "Answer your first card"),
    "journal": ("No entries yet.", "/due", "Review to unlock prompts"),
}


def empty_state(page: str) -> str:
    """Next-action HTML for an empty page; stable id='empty' anchor."""
    msg, href, label = _NEXT.get(page, ("Nothing here yet.", "/", "Home"))
    return (
        f"<p id='empty'>{msg} "
        f"<a href='{href}'>{label}</a>.</p>"
    )
