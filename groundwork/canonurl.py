"""Language-prefix-free canonical URLs; URL contract (I-33).

Every app path has one canonical form: no language prefix, no
trailing slash (except root), query string and fragment preserved
verbatim. Pure functions, stdlib only, no I/O, no DB changes,
no web.py edits, no groundwork imports.

Route table verified against groundwork/web.py Handler.do_GET/do_POST.
``/healthz`` is NOT present in web.py and is deliberately absent here.

Trailing-slash rule: ``/`` stays ``/``; every other canonical path
has no trailing slash (``/due/`` -> ``/due``).

Query preservation note: canonical() normalizes the path part only;
``?query`` and ``#fragment`` are re-attached byte-for-byte, never
reordered or dropped (``/en/due?mode=one`` -> ``/due?mode=one``).

Language prefixes: a leading segment that is exactly a two-letter
code (optionally ``-REGION``, case-insensitive, e.g. ``/en/...``,
``/pt-BR/...``) is stripped. Full-segment match only, so ``/debt``
(segment ``debt``) never strips; bare ``/en`` or ``/en/`` folds home
to ``/``. Unknown paths are still shape-normalized but are not
members of the contract table.

Fail-closed: a leading ``//`` (protocol-relative open-redirect
shape), a scheme, backslashes, whitespace, or quote/bracket
characters anywhere collapse to ``'/'``, mirroring the
``_safe_origin`` convention in web.py and ``originguard``.
"""
from __future__ import annotations

import html
import re

LANGS = frozenset({
    "de", "en", "es", "fr", "it", "ja", "ko", "nl", "pt", "ru", "zh",
})

_LANG_RE = re.compile(r"^[A-Za-z]{2}(-[A-Za-z]{2})?$")

# (canonical path, purpose). ``{name}`` marks a path parameter.
ROUTES = (
    ("/", "Projects landing"),
    ("/due", "Spaced review queue"),
    ("/modules", "Module library"),
    ("/reviews", "Attempt history"),
    ("/debt", "Stale-code debt ledger"),
    ("/diagnose", "Traceback diagnosis form"),
    ("/status", "Machine-room status page"),
    ("/tour", "Feature-tour catalog"),
    ("/journal", "Private journal"),
    ("/styleguide", "Component gallery"),
    ("/search", "Ranked header search"),
    ("/file", "Read-only source viewer"),
    ("/modules/{mid}", "Module detail page"),
    ("/modules/{mid}/reset", "Module reset confirm + action"),
    ("/modules/{mid}/handout/{node}", "Printable lesson handout"),
    ("/export/anki.tsv", "Anki TSV export"),
    ("/export/reviews.csv", "Reviews CSV export"),
    ("/export/me.json", "Personal JSON export"),
    ("/api/modules.json", "Modules JSON API"),
    ("/api/due.json", "Due-queue JSON API"),
    ("/badge.svg", "Owned-concepts badge"),
    ("/feed.xml", "RSS feed of modules"),
    ("/sitemap.xml", "XML sitemap"),
    ("/robots.txt", "Crawler rules"),
    ("/mcp", "Agent JSON-RPC endpoint (POST)"),
    ("/journal", "Save journal entry (POST)"),
    ("/diagnose", "Grade a traceback (POST)"),
    ("/modules/{mid}/reset", "Reset a module (POST)"),
    ("/concepts/{cid}/rate", "Record clarity vote (POST)"),
    ("/concepts/{cid}/known", "Skip known concept (POST)"),
    ("/reviews/undo", "Undo last review (POST)"),
    ("/cards/{cid}/snooze", "Snooze a card (POST)"),
    ("/cards/{cid}/review", "Grade a card (POST)"),
    ("/cards/{cid}/dispute", "File a dispute (POST)"),
    ("/disputes/{did}/resolve", "Resolve a dispute (POST)"),
)


def _unsafe(raw: str) -> bool:
    """True when raw must collapse to '/' (never echoed back)."""
    return (raw.startswith("//") or "\\" in raw or "://" in raw
            or any(ch.isspace() or ch in "\"'<>`" for ch in raw))


def strip_lang_prefix(path: str) -> str:
    """Remove one leading language segment (``/en``); case-insensitive."""
    if not isinstance(path, str) or not path.startswith("/"):
        return path if isinstance(path, str) else ""
    head, _, rest = path[1:].partition("/")
    if _LANG_RE.match(head or "") and head.lower()[:2] in LANGS:
        return "/" + rest if rest else "/"
    return path


def canonical(path) -> str:
    """Canonical URL for an app path: prefix-free, slash-normalized.

    Non-string, empty, or hostile input (leading ``//``, scheme,
    backslash, whitespace, quotes/brackets) falls back to ``'/'``,
    mirroring the ``_safe_origin`` convention in web.py. Query and
    fragment are preserved verbatim.
    """
    if not isinstance(path, str):
        return "/"
    raw = path.strip()
    if not raw or _unsafe(raw):
        return "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    # Split fragment first so a '?' inside # stays put; both parts are
    # re-attached verbatim below.
    frag = ""
    if "#" in raw:
        raw, _, frag = raw.partition("#")
        frag = "#" + frag
    query = ""
    if "?" in raw:
        raw, _, query = raw.partition("?")
        query = "?" + query
    raw = re.sub(r"/{2,}", "/", raw)
    raw = strip_lang_prefix(raw)
    raw = re.sub(r"/{2,}", "/", raw)
    if len(raw) > 1:
        raw = raw.rstrip("/")
    return (raw or "/") + query + frag


def is_canonical(path) -> bool:
    """True when ``path`` is already in canonical form."""
    return isinstance(path, str) and path == canonical(path)


def url_contract() -> list:
    """Route-contract rows: ``[(path, purpose), ...]`` for Status/docs."""
    return [(p, u) for p, u in ROUTES]


def section_html() -> str:
    """Status-page subsection with a stable tour anchor (no DB needed)."""
    rows = "".join(
        f"<tr><td><code>{html.escape(p)}</code></td>"
        f"<td>{html.escape(u)}</td></tr>"
        for p, u in url_contract())
    return (
        "<h3 id='status-b8-canonurl'>Canonical URLs "
        "<small>(improvement)</small></h3>"
        "<p>Every app path has one canonical form: no language prefix "
        "(<code>/en/due</code> &#8594; <code>/due</code>), no trailing "
        "slash except root, query string and fragment preserved verbatim. "
        "Unknown paths still normalize their shape but are not contract "
        "members. <code>groundwork/canonurl.py</code>.</p>"
        f"<table><tr><th>Path</th><th>Purpose</th></tr>{rows}</table>")
