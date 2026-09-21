"""Quarterly internal-link audit: extraction + verification + report (I-50).

Collects every internal link the app emits, verifies each resolves to a
known route (no 404s), and reports breaks — as a reusable module plus test
so the audit runs in CI, not once a quarter by hand.

Typical CI use::

    from groundwork import canonurl, linkcheck
    links = linkcheck.extract_links(page_html)
    result = linkcheck.audit_links(links, canonurl.ROUTES)
    print(linkcheck.audit_report(result))
    assert not result["broken"]

Boundary: this module owns ONLY extraction + audit + report. The route
contract stays owned by ``canonurl.py`` (consumed here as a parameter —
never a second hardcoded table), and external-link marking stays with
``extlinks.py``. Pure functions, stdlib only (``re`` + ``html.parser``),
no I/O, no DB/schema changes, no web.py edits, no groundwork imports.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser

# Attributed mirror of canonurl.LANGS (prefix rules per canonurl): a
# leading segment that is exactly a two-letter code (optionally
# -REGION, case-insensitive) is stripped. This is a prefix set, not a
# route table — the routes themselves always come from canonurl.ROUTES
# via the ``routes`` parameter. Pinned in sync by test_langs_mirror.
LANGS = frozenset({
    "de", "en", "es", "fr", "it", "ja", "ko", "nl", "pt", "ru", "zh",
})

_LANG_RE = re.compile(r"^[A-Za-z]{2}(-[A-Za-z]{2})?$")
_PARAM_RE = re.compile(r"\{[^/{}]+\}")

_SKIP_PREFIXES = ("#", "mailto:", "tel:", "data:", "javascript:")
_EXTERNAL_PREFIXES = ("http://", "https://", "//")


def _kind(href) -> str:
    """'skip' | 'external' | 'internal' for one raw href value."""
    if not isinstance(href, str):
        return "skip"
    text = href.strip()
    if not text:
        return "skip"
    low = text.lower()
    if low.startswith(_SKIP_PREFIXES):
        return "skip"
    if low.startswith(_EXTERNAL_PREFIXES):
        return "external"
    return "internal"


class _HrefParser(HTMLParser):
    """Collects raw href values from <a> tags; never raises to the caller."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list = []

    def handle_starttag(self, tag, attrs) -> None:
        if tag.lower() != "a":
            return
        for name, value in attrs:
            if name.lower() == "href":
                self.hrefs.append(value)


def extract_links(html_text) -> list:
    """Internal app hrefs found in HTML, as-written and in document order.

    Skips external URLs, mailto:/tel:/data:/javascript: links, and
    anchors-only hrefs. Never raises: non-string input yields ``[]`` and
    malformed HTML yields whatever links parsed before the damage.
    """
    if not isinstance(html_text, str) or "a" not in html_text.lower():
        return []
    parser = _HrefParser()
    try:
        parser.feed(html_text)
    except Exception:  # noqa: BLE001 — malformed HTML never breaks the audit
        pass
    try:
        parser.close()
    except Exception:  # noqa: BLE001 — same tolerance at stream end
        pass
    return [h for h in parser.hrefs if _kind(h) == "internal"]


def normalize_path(href: str) -> str:
    """Audit shape of one internal href: query/fragment stripped, one
    language prefix removed, slashes collapsed, trailing slash dropped
    (root stays ``/``). Relative hrefs gain a leading ``/``.

    Unlike ``canonurl.canonical()`` this never collapses hostile input to
    ``'/'``: anything that does not shape-match a route stays unmatched
    (broken) rather than passing as home.
    """
    text = href.strip()
    text = text.split("#", 1)[0].split("?", 1)[0].strip()
    if not text.startswith("/"):
        text = "/" + text
    text = re.sub(r"/{2,}", "/", text)
    head, _, rest = text[1:].partition("/")
    if _LANG_RE.match(head or "") and head.lower()[:2] in LANGS:
        text = "/" + rest if rest else "/"
    text = re.sub(r"/{2,}", "/", text)
    if len(text) > 1:
        text = text.rstrip("/")
    return text or "/"


def _route_re(route: str) -> "re.Pattern":
    """Regex for one route pattern; ``{name}`` matches one segment."""
    parts = [
        r"[^/]+" if _PARAM_RE.fullmatch(seg) else re.escape(seg)
        for seg in route.split("/")
    ]
    return re.compile("/".join(parts) + r"\Z")


def _route_paths(routes) -> list:
    """Plain path patterns from ROUTES rows or bare path strings."""
    paths = []
    try:
        items = list(routes or ())
    except TypeError:
        return []
    for item in items:
        if isinstance(item, str):
            paths.append(item)
        elif isinstance(item, (tuple, list)) and item and isinstance(item[0], str):
            paths.append(item[0])
    return paths


def audit_links(links, routes=None) -> dict:
    """Check internal hrefs against the route table.

    ``links`` may mix internal, external, and skippable hrefs (e.g. raw
    parser output); externals are counted, skips are ignored. ``routes``
    is the canonical table (pass ``canonurl.ROUTES``) as ``(path,
    purpose)`` rows or plain paths. Returns ``{"ok": [...], "broken":
    [...], "external_skipped": n}`` with normalized paths, deduplicated
    in first-seen order. Deterministic, no network, tolerant of bad
    input (``None`` links audit as empty; ``None`` routes match nothing).
    """
    if isinstance(links, str):
        links = [links]
    try:
        items = list(links or ())
    except TypeError:
        items = []
    patterns = [_route_re(p) for p in _route_paths(routes)]
    ok: list = []
    broken: list = []
    skipped = 0
    for href in items:
        kind = _kind(href)
        if kind == "skip":
            continue
        if kind == "external":
            skipped += 1
            continue
        path = normalize_path(href)
        bucket = ok if any(rx.match(path) for rx in patterns) else broken
        if path not in bucket:
            bucket.append(path)
    return {"ok": ok, "broken": broken, "external_skipped": skipped}


def audit_report(result) -> str:
    """One-line human summary of an audit_links() result, e.g.
    ``Link audit: 12 ok, 2 broken (/nope, /old), 1 external skipped.``.
    Never raises; malformed input reports zero counts.
    """
    try:
        ok = list((result or {}).get("ok", []) or [])
        broken = list((result or {}).get("broken", []) or [])
        skipped = int((result or {}).get("external_skipped", 0) or 0)
    except (TypeError, ValueError, AttributeError):
        ok, broken, skipped = [], [], 0
    line = (f"Link audit: {len(ok)} ok, {len(broken)} broken, "
            f"{skipped} external skipped.")
    if broken:
        line = (f"Link audit: {len(ok)} ok, {len(broken)} broken "
                f"({', '.join(str(p) for p in broken)}), "
                f"{skipped} external skipped.")
    return line


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b9-linkcheck'>Link audit <small>(improvement)</small></h3>"
        "<p>Every internal link the app emits is extracted from rendered "
        "HTML, normalized (query/fragment stripped, language prefix and "
        "trailing slash folded per <code>canonurl</code> rules), and matched "
        "against the canonical route table — parameterized segments like "
        "<code>/modules/{mid}</code> accept any single segment. Breaks are "
        "reported as one line, e.g. "
        "<code>Link audit: 12 ok, 2 broken (/nope, /old), "
        "1 external skipped.</code> Runs in CI via "
        "<code>groundwork/linkcheck.py</code>; externals, mailto:, and "
        "fragment-only links are never flagged.</p>"
    )
