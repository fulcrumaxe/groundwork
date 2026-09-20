"""Persist the `?level=` explainer choice via query carry-over (I-4).

The `?level=` tabs already exist in lessons.render_levels (which emits
`base_path?level=<n>` links); this module builds on that instead of
duplicating it. It appends the active explicit level (1-4) to every
other internal link on a rendered page, so the choice rides the URL:
per-browser, bookmarkable, no cookies, no DB/schema changes.

Pure functions, stdlib only. web.py keeps one delegation point
(normalize in do_GET, carry_html over rendered HTML); all HTML here.
"""
from __future__ import annotations

import html
import re

LEVELS = ("auto", "1", "2", "3", "4")

_HREF_RE = re.compile(r"""href=(['"])(.*?)\1""")

_SKIP_PREFIXES = ("#", "http://", "https://", "//", "mailto:",
                  "data:", "javascript:", "tel:")


def normalize(level) -> str:
    """Canonical level string; anything unknown falls back to "auto"."""
    s = level.strip() if isinstance(level, str) else ""
    return s if s in LEVELS else "auto"


def is_explicit(level) -> bool:
    """Only 1-4 need carrying; "auto" is the default and stays clean."""
    return normalize(level) in ("1", "2", "3", "4")


def _split_fragment(href: str) -> tuple[str, str]:
    """Split off a #fragment (fragment may be empty)."""
    head, sep, tail = href.partition("#")
    return head, (sep + tail)


def carry(href, level: str) -> str:
    """Return href with `?level=<n>` appended, or unchanged.

    Unchanged when: level is "auto"/invalid, href is not a string,
    href is empty, external (http/https/protocol-relative), a
    non-navigating scheme (mailto:/data:/...), a pure #fragment, or
    the query already carries a level= parameter (never doubled).
    Anchors and other query params are preserved in place.
    """
    if not is_explicit(level):
        return href
    if not isinstance(href, str) or not href:
        return href
    low = href.lower()
    if href.startswith(_SKIP_PREFIXES) or low.startswith(_SKIP_PREFIXES):
        return href
    head, frag = _split_fragment(href)
    base, sep, qs = head.partition("?")
    if sep:
        params = qs.split("&")
        if any(p == "level" or p.startswith("level=") for p in params):
            return href
        return f"{base}?{qs}&level={normalize(level)}{frag}"
    return f"{base}?level={normalize(level)}{frag}"


def carry_html(html_text, level: str) -> str:
    """Rewrite every internal href in a rendered page via carry()."""
    if not is_explicit(level):
        return html_text
    if not isinstance(html_text, str) or "href=" not in html_text:
        return html_text
    lvl = normalize(level)

    def _one(m: "re.Match") -> str:
        q, href = m.group(1), m.group(2)
        return f"href={q}{carry(href, lvl)}{q}"

    return _HREF_RE.sub(_one, html_text)


def section_html() -> str:
    """Status subsection: the carry-over, inspectable with no page."""
    demo = html.escape(carry("/modules/abc", "2"))
    return ("<h2 id='status-b6-levelcarry'>Explainer level carry-over</h2>"
            "<p>Pick Plain words once and every link keeps it: the active "
            "explainer level rides the URL as <code>?level=1..4</code> "
            f"(e.g. <code>{demo}</code>). Per-browser, bookmarkable, "
            "no cookies, no database. Tabs still come from "
            "<code>lessons.render_levels</code>.</p>")
