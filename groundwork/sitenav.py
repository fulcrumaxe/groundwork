"""Merged header + footer nav (I-39).

Single source of truth for the site nav: one NAV item table
(key, href, label) plus two pure renderers — header_nav() with
optional count badges, footer_nav() as the flat footer variant.
The grouped footer sitemap stays owned by footnav.py (I-10);
this module removes the second copy of the header item table
that used to live inline in web.page(). Stdlib only (html),
no DB, no I/O, no groundwork imports.

Quote note: header_nav() emits aria-current="page" (double quotes)
to stay byte-identical with the web.page() header it replaces
(pinned by tests/test_web.py); footer_nav() uses aria-current='page'
matching the footer convention (pinned by tests/test_footnav.py).
"""
from __future__ import annotations

import html

# Verified verbatim against web.NAV (groundwork/web.py): (key, href, label).
NAV: tuple[tuple[str, str, str], ...] = (
    ("projects", "/", "Projects"),
    ("due", "/due", "Due"),
    ("modules", "/modules", "Modules"),
    ("history", "/reviews", "History"),
    ("debt", "/debt", "Debt"),
    ("tour", "/tour", "Tour"),
)


def items() -> tuple[tuple[str, str, str], ...]:
    """The nav item table: ((key, href, label), ...)."""
    return NAV


def href_of(key: str, default: str = "") -> str:
    """Href for an item key, or default when the key is unknown."""
    for k, href, _ in NAV:
        if k == key:
            return href
    return default


def _label(key: str, label: str, counts: dict | None) -> str:
    """Label with an optional count badge (header only)."""
    if counts and counts.get(key) is not None:
        return f"{label} ({html.escape(str(counts[key]))})"
    return label


def _header_link(key: str, href: str, label: str, active: str,
                 counts: dict | None = None) -> str:
    """One header nav link; the active item key carries aria-current."""
    mark = ' aria-current="page"' if key == active else ""
    return (f"<a href='{html.escape(href, quote=True)}'{mark}>"
            f"{html.escape(_label(key, label, counts))}</a>")


def _footer_link(key: str, href: str, label: str, active: str) -> str:
    """One flat footer nav link; the active item key carries aria-current."""
    mark = " aria-current='page'" if key == active else ""
    return (f"<a href='{html.escape(href, quote=True)}'{mark}>"
            f"{html.escape(label)}</a>")


def header_nav(active: str = "projects", counts: dict | None = None) -> str:
    """Header nav links joined with middots; counts add `(n)` badges."""
    return " · ".join(
        _header_link(key, href, label, active, counts)
        for key, href, label in NAV)


def footer_nav(active: str = "projects") -> str:
    """Flat footer nav over the same NAV table (no count badges)."""
    links = " · ".join(
        _footer_link(key, href, label, active) for key, href, label in NAV)
    return (f"<footer class='page-foot' id='site-footer'>"
            f"<nav aria-label='Site'>{links}</nav>"
            f"<p><a href='/status'>Status</a></p>"
            f"</footer>")


def section_html() -> str:
    """Anchored status subsection with a demo nav (no db_path arg)."""
    demo = header_nav("due", {"due": 3, "modules": 12})
    return (
        "<h3 id='status-b8-sitenav'>Merged site nav <small>(improvement)</small></h3>"
        "<p>Header and footer render from one NAV table — "
        "<code>groundwork/sitenav.py</code> — with "
        "<code>aria-current</code> on the active item and count badges "
        "in the header only.</p>"
        f"<p><nav id='sitenav-demo'>{demo}</nav></p>"
    )
