"""Whole-card clickable module cards with visible focus rings (I-16).

The library (groundwork/web.py ``modules_html``) renders each module as
``<a class='modcard' href='/modules/<id>'>…inner…</a>`` plus a separate
Resume/Review link *outside* the card. Making the card itself wrap that
second link in a nested ``<a>`` would break HTML validity and keyboard
nav, so this module builds the card the other way round: a
non-interactive container (``<article class='modcard …'>``) holding the
original inner HTML with any nested anchors flattened to text, plus
exactly ONE real link stretched over the card via CSS. A small
``<style>`` block adds a visible ``:focus-visible`` ring driven by the
palette tokens from groundwork/palette.py.

Pure functions, stdlib only (html/re), no DB/schema changes, no web.py
imports. Web wiring lives in web.py (see WIRES); this module only
builds strings the handler embeds.
"""
from __future__ import annotations

import html
import re

CARD_CLASS = "modcard modcard--clickable"
LINK_CLASS = "card-link stretched-link"

ANCHOR_ID = "status-b7-clickcards"

FALLBACK_HREF = "/modules"
FALLBACK_LABEL = "Open module"

_ANCHOR_RE = re.compile(r"<a\b[^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)


def safe_href(value) -> str:
    """Keep only a same-site page path (query kept); else /modules."""
    try:
        v = value if isinstance(value, str) else ("" if value is None else str(value))
    except Exception:
        return FALLBACK_HREF
    v = v.strip().split("#")[0].strip()
    if (v.startswith("/") and not v.startswith("//")
            and "\\" not in v
            and not any(ch.isspace() or ch in "\"'<>`" for ch in v)):
        return v or FALLBACK_HREF
    return FALLBACK_HREF


def strip_nested_links(inner) -> str:
    """Flatten nested <a>…</a> to their inner text; never raises."""
    try:
        text = inner if isinstance(inner, str) else ("" if inner is None else str(inner))
    except Exception:
        return ""
    try:
        return _ANCHOR_RE.sub(r"\1", text)
    except Exception:
        return text


def wrap_card(inner_html="", href="/modules", label="Open module") -> str:
    """Wrap card inner HTML so the whole card is one clickable link.

    Exactly one ``<a>`` is emitted (the stretched link); any anchors
    inside *inner_html* are flattened to text so no nested-interactive
    HTML is produced. Bad input never raises.
    """
    body = strip_nested_links(inner_html)
    target = safe_href(href)
    try:
        text = label if isinstance(label, str) else ("" if label is None else str(label))
    except Exception:
        text = ""
    text = text.strip() or FALLBACK_LABEL
    return (
        f"<article class='{CARD_CLASS}'>{body}"
        f"<a class='{LINK_CLASS}' href='{html.escape(target, quote=True)}'"
        f" aria-label='{html.escape(text, quote=True)}'>"
        f"{html.escape(text)}</a></article>"
    )


def focus_css() -> str:
    """Small <style>: stretched cover link + visible :focus-visible ring."""
    return (
        "<style>"
        ".modcard--clickable{position:relative;}"
        ".stretched-link::after{content:'';position:absolute;inset:0;}"
        ".card-link:focus-visible{outline:3px solid "
        "var(--accent-modules,#8a5a00);outline-offset:3px;}"
        "</style>"
    )


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        "<h3 id='status-b7-clickcards'>Whole-card module links</h3>"
        "<p>Every module card is one clickable target: a single stretched "
        "link covers the card (nested anchors are flattened, never nested) "
        "with a visible <code>:focus-visible</code> ring drawn from "
        "<code>var(--accent-modules)</code>. "
        "<code>groundwork/clickcards.py</code>.</p>"
    )
