"""Modules-index pagination (I-20): server-side page links, 50 per page.

Choice: plain server-rendered page links (``?page=N``), NOT client-side
virtualization. This app is stdlib-only server-rendered HTML with no JS
build, so page links work offline, preserve filters via a passthrough
params dict (repo / sort / the I-19 status filter), and degrade to
nothing on a single page. No DB or schema changes.

Pure functions over a plain list — the Handler keeps thin delegation
lines (parent wires those later): paginate the card list, render the
summary line, render the nav.
"""
from __future__ import annotations

import html
from urllib.parse import urlencode

PAGE_SIZE = 50
MAX_LINKS = 7  # numbered-link window cap before ellipsis kicks in


def total_pages(total: int, per_page: int = PAGE_SIZE) -> int:
    """Page count for total items; at least 1 so the nav has a home."""
    if not isinstance(per_page, int) or isinstance(per_page, bool) \
            or per_page <= 0:
        per_page = PAGE_SIZE
    if not isinstance(total, int) or isinstance(total, bool) or total < 0:
        total = 0
    return max(1, -(-total // per_page))


def normalize_page(raw, pages: int) -> int:
    """Coerce a raw ?page= value to a clamped int in [1, pages].

    Garbage ("abc", None, "2.5") falls back to 1; 0/negatives clamp
    to the first page, huge values clamp to the last page.
    """
    if not isinstance(pages, int) or isinstance(pages, bool) or pages < 1:
        pages = 1
    try:
        page = int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 1
    if isinstance(raw, bool):
        return 1
    return max(1, min(page, pages))


def paginate(items, page=1, per_page: int = PAGE_SIZE) -> dict:
    """Slice a list into one page; never mutates the input.

    Returns {"page", "per_page", "total", "pages", "start", "end",
    "items"} where start/end are 1-based inclusive bounds (0, 0 when
    the list is empty) backing the "showing X-Y of Z" summary line.
    """
    if not isinstance(per_page, int) or isinstance(per_page, bool) \
            or per_page <= 0:
        per_page = PAGE_SIZE
    seq = list(items) if items else []
    total = len(seq)
    pages = total_pages(total, per_page)
    current = normalize_page(page, pages)
    lo = (current - 1) * per_page
    hi = min(lo + per_page, total)
    return {"page": current, "per_page": per_page, "total": total,
            "pages": pages, "start": lo + 1 if total else 0,
            "end": hi if total else 0, "items": seq[lo:hi]}


def page_url(base: str, params: dict | None, page: int) -> str:
    """URL for one page link; existing filters ride along, page wins.

    ``params`` is the passthrough dict (e.g. {"repo", "sort", "status"}
    from the I-19 status filter); the ``page`` argument always replaces
    any ``page`` key inside it. Values are url-encoded here and
    HTML-escaped by the caller at render time.
    """
    merged = dict(params) if params else {}
    merged["page"] = page
    query = urlencode([(k, "" if v is None else v)
                       for k, v in merged.items()])
    return f"{base}?{query}" if query else base


def _window(pages: int, current: int) -> list:
    """Page numbers to link: all when few, first/last + neighbours."""
    if pages <= MAX_LINKS:
        return list(range(1, pages + 1))
    keep = {1, 2, current - 1, current, current + 1, pages - 1, pages}
    return sorted(p for p in keep if 1 <= p <= pages)


def pager_html(total: int, page=1, base: str = "/modules",
               params: dict | None = None,
               per_page: int = PAGE_SIZE) -> str:
    """Prev/next + numbered page links; "" when everything fits one page.

    Every link preserves ``params`` (status filter et al) and only
    swaps ``page``. The current page carries ``aria-current="page"``.
    """
    pages = total_pages(total, per_page)
    if pages < 2:
        return ""
    current = normalize_page(page, pages)
    bits = []
    if current > 1:
        bits.append(
            f"<a href='{html.escape(page_url(base, params, current - 1), quote=True)}'"
            f" rel='prev'>\u2190 Prev</a>")
    prev_num = 0
    for num in _window(pages, current):
        if num - prev_num > 1:
            bits.append("<span class='pager-gap' aria-hidden='true'>\u2026</span>")
        if num == current:
            bits.append(f"<span aria-current='page'><b>{num}</b></span>")
        else:
            bits.append(
                f"<a href='{html.escape(page_url(base, params, num), quote=True)}'>"
                f"{num}</a>")
        prev_num = num
    if current < pages:
        bits.append(
            f"<a href='{html.escape(page_url(base, params, current + 1), quote=True)}'"
            f" rel='next'>Next \u2192</a>")
    return ("<nav class='pager' aria-label='Module pages'>"
            + " \u00b7 ".join(bits) + "</nav>")


def summary_html(total: int, page=1, per_page: int = PAGE_SIZE) -> str:
    """The "showing X-Y of Z" line; honest zero state when empty."""
    if not isinstance(per_page, int) or isinstance(per_page, bool) \
            or per_page <= 0:
        per_page = PAGE_SIZE
    if not isinstance(total, int) or isinstance(total, bool) or total < 0:
        total = 0
    if not total:
        return ("<p class='pager-summary'><small>Showing 0 of 0 "
                "modules.</small></p>")
    info = paginate(range(total), page, per_page)
    noun = "module" if total == 1 else "modules"
    return (f"<p class='pager-summary'><small>Showing {info['start']}\u2013"
            f"{info['end']} of {total} {noun}.</small></p>")


def section_html(db_path: str = "") -> str:
    """Status section: Modules-index pagination, honestly footnoted."""
    _ = db_path  # no DB read: pagination is a pure view over the list
    return (
        "<h2 id='status-b7-modpages'>Modules pagination</h2>"
        "<p>Past 50 modules the library splits into server-side pages — "
        "plain <code>?page=N</code> links at 50 per page, out-of-range "
        "pages clamping to the first/last page, with a "
        "\u201cShowing X\u2013Y of Z\u201d line. Existing filters ride "
        "along via a passthrough params dict. "
        "<code>groundwork/modpages.py</code>; pure functions, stdlib only "
        "(<code>html</code>/<code>urllib</code>), no schema changes.</p>")
