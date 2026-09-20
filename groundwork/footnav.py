"""Site footer sitemap on every page (I-10).

Grouped footer navigation — Due · Modules · History · About — rendered
by web.page() on every page. Route knowledge reuses sitemap.ROUTES (the
crawler map) plus web.NAV labels via a caller-passed active key; this
module never hardcodes a competing route table.

Pure functions, stdlib only (html), no DB, no I/O.
"""
from __future__ import annotations

import html

from . import sitemap as sitemapmod

TAGLINE = "Groundwork — every session leaves you smarter."

# Group heading -> [(label, href)]. Every href below (except "/") names
# a route present in sitemap.ROUTES, so the footer can never drift from
# the crawler map: _check() enforces it at render time in tests.
SECTIONS: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    ("Due", (
        ("Due queue", "/due"),
        ("Diagnose", "/diagnose"),
    )),
    ("Modules", (
        ("Library", "/modules"),
        ("Debt", "/debt"),
    )),
    ("History", (
        ("Reviews", "/reviews"),
        ("Tour", "/tour"),
    )),
    ("About", (
        ("Projects", "/"),
        ("Status", "/status"),
    )),
)


def _route_of(href: str) -> str:
    """Sitemap route key for an href ("/" -> "", else stripped path)."""
    if href == "/":
        return ""
    return href.strip("/").split("/")[0]


def check() -> list[str]:
    """Hrefs whose first segment is missing from sitemap.ROUTES."""
    known = set(sitemapmod.ROUTES)
    return sorted(
        {href for _, links in SECTIONS for _, href in links
         if _route_of(href) not in known})


def sections() -> tuple[tuple[str, tuple[tuple[str, str], ...]], ...]:
    """Grouped footer data: ((heading, ((label, href), ...)), ...)."""
    return SECTIONS


def _link(label: str, href: str, active: str) -> str:
    """One footer link; the active page carries aria-current."""
    mark = " aria-current='page'" if href == active else ""
    return (f"<a href='{html.escape(href)}'{mark}>"
            f"{html.escape(label)}</a>")


def section_html(heading: str, links: tuple[tuple[str, str], ...],
                 active: str = "") -> str:
    """One footer group: heading plus its links."""
    items = "".join(_link(label, href, active) for label, href in links)
    return (f"<section><h2>{html.escape(heading)}</h2>"
            f"<p>{items}</p></section>")


def footer(active: str = "") -> str:
    """Full <footer> sitemap: tagline plus the four grouped sections."""
    groups = "".join(
        section_html(heading, links, active) for heading, links in SECTIONS)
    return (
        f"<footer class='page-foot' id='site-footer'>"
        f"<p>{html.escape(TAGLINE)}</p>"
        f"<nav aria-label='Site map'>{groups}</nav>"
        f"<p><a href='/status'>Status</a></p>"
        f"</footer>")


def section_html_status() -> str:
    """Status page subsection for this item (anchor id starts status-b6-)."""
    return (
        "<h2 id='status-b6-footnav'>Footer sitemap</h2>"
        "<p>Every page ends in a grouped site map — Due, Modules, "
        "History, About — plus the tagline and a Status link, so no "
        "page is a dead end.</p>")
