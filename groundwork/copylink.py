"""Copy-link button per lesson section (I-28).

Server-rendered anchor link helper: one pure function of the section
anchor — no I/O, no DB changes, stdlib HTML only.
"""
from __future__ import annotations

import html


def copy_link(anchor) -> str:
    """Anchor link that carries its own deep-link URL (no external JS)."""
    text = anchor if isinstance(anchor, str) else ""
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    slug = "-".join(p for p in slug.split("-") if p)
    if not slug:
        return ""
    safe = html.escape(slug, quote=True)
    return (
        f"<a class='copylink' href='#{safe}' "
        f"data-copy-anchor='#{safe}' title='Copy link'>#</a>"
    )
