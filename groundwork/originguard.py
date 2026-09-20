"""Origin allowlist guard (I-34).

Fail-closed `?origin` validation for every page added later: structural
sanitisation first (same-origin shape only), then an allowlist check
against the GET page routes `groundwork/web.py` actually serves. Pure
functions, stdlib only (`html`, `urllib.parse`), no I/O, no DB/schema
changes, no `web.py` edits, no groundwork imports.

Route list verified against `Handler.do_GET` dispatch in web.py:
  exact GET pages: /, /due, /reviews, /modules, /debt, /diagnose,
    /styleguide, /tour, /status, /journal, /search
  prefix GET pages: /modules/<mid>  (detail pages under /modules/)
POST-only endpoints (/cards/.../review, /cards/.../snooze,
/cards/.../dispute, /concepts/.../rate, /concepts/.../known,
/modules/.../reset, /reviews/undo, /disputes/.../resolve, /mcp,
/journal, /diagnose) and machine targets (/api/*.json, /export/*,
/badge.svg, /feed.xml, /sitemap.xml, /robots.txt) are deliberately NOT
in the allowlist: an origin is a human return target, so only GET pages
qualify. See WIRES below.
"""
from __future__ import annotations

import html
from urllib.parse import urlsplit

DEFAULT = "/"

# Exact GET page paths served by Handler.do_GET (web.py:388-479).
KNOWN_EXACT = frozenset({
    "/", "/due", "/reviews", "/modules", "/debt", "/diagnose",
    "/styleguide", "/tour", "/status", "/journal", "/search",
})

# Prefix GET pages: /modules/<mid> detail (web.py:496).
KNOWN_PREFIXES = ("/modules/",)

# Modules whose HTML emits a hidden origin field (producers).
ORIGIN_PRODUCERS = (
    ("cards", "answer_widget"),
    ("cards", "snooze_form"),
    ("clarity", "block_html"),
    ("known", "button_html"),
    ("disputes", "dispute_form_html"),
    ("scrollpos", "origin_field"),
)

# web.py call sites that consume origin (file, handler, default).
ORIGIN_CONSUMERS = (
    ("web.py", "_parse_review_form -> /cards/<id>/review", "/due"),
    ("web.py", "/cards/<id>/snooze", "/due"),
    ("web.py", "/cards/<id>/dispute", "/due"),
    ("web.py", "/concepts/<id>/rate", "/modules"),
    ("web.py", "/concepts/<id>/known", "/modules"),
)

_BAD_CHARS = set("\"'<>` \t\r\n")

# WIRES: web.py keeps owning `_safe_origin` + embedding; a later batch
# may call `originguard.safe_origin` inside `_parse_review_form` and the
# four POST handlers, and append `section_html()` / `tour_entry()` to the
# status page and tour.ENTRIES. No wiring is done here.


def _coerce(value, default=DEFAULT) -> str:
    """Coerce input to str; None/non-str fall back, never raises."""
    if value is None:
        return default if isinstance(default, str) else DEFAULT
    if isinstance(value, str):
        return value
    try:
        return str(value)
    except Exception:
        return default if isinstance(default, str) else DEFAULT


def _strip_fragment(text: str) -> str:
    """Drop any #fragment; anchors are scrollpos's job, not origin's."""
    return text.split("#", 1)[0]


def _structurally_safe(path_query: str) -> bool:
    """Same-origin shape: leading /, no scheme, no //, no backslash tricks."""
    v = path_query
    if not v.startswith("/") or v.startswith("//"):
        return False
    if "\\" in v or any(ch in _BAD_CHARS or ch.isspace() for ch in v):
        return False
    low = v.lower()
    if "%2f" in low or "%5c" in low or "%00" in low:
        return False
    head = v[1:].split("/", 1)[0].split("?", 1)[0]
    if ":" in head:  # scheme (javascript:...), port, or userinfo smuggling
        return False
    try:
        parts = urlsplit(v)
    except ValueError:
        return False
    if parts.scheme or parts.netloc:
        return False
    return True


def is_allowed(path: str) -> bool:
    """True when path (no query) names a known GET page."""
    if not isinstance(path, str) or not path.startswith("/"):
        return False
    if path in KNOWN_EXACT:
        return True
    return any(path.startswith(p) and len(path) > len(p)
               for p in KNOWN_PREFIXES)


def known_routes() -> list:
    """Sorted allowlisted origin targets (exact pages + prefix markers)."""
    return sorted(KNOWN_EXACT) + [p + "<mid>" for p in KNOWN_PREFIXES]


def origin_producers() -> tuple:
    """(module, symbol) pairs that emit hidden origin fields."""
    return ORIGIN_PRODUCERS


def origin_consumers() -> tuple:
    """(file, handler, default) sites that consume origin."""
    return ORIGIN_CONSUMERS


def audit_origin(value, default=DEFAULT) -> dict:
    """Explain a verdict: {input, output, allowed, reason}. Never raises."""
    try:
        raw = _coerce(value, default)
        text = _strip_fragment(raw.strip())
        if not text:
            return {"input": raw, "output": default, "allowed": False,
                    "reason": "empty"}
        path, _, query = text.partition("?")
        if query and ("#" in query or any(ch.isspace() for ch in query)):
            return {"input": raw, "output": default, "allowed": False,
                    "reason": "bad-query"}
        if len(path) > 1:
            path = path.rstrip("/")
        text = path + ("?" + query if query else "")
        if not _structurally_safe(text):
            return {"input": raw, "output": default, "allowed": False,
                    "reason": "unsafe-shape"}
        if not is_allowed(path):
            return {"input": raw, "output": default, "allowed": False,
                    "reason": "unknown-route"}
        return {"input": raw, "output": text or default, "allowed": True,
                "reason": "ok"}
    except Exception:
        return {"input": "", "output": default, "allowed": False,
                "reason": "error"}


def safe_origin(value, default=DEFAULT) -> str:
    """Allowlisted origin path; falls back to default on any failure."""
    verdict = audit_origin(value, default)
    if verdict["allowed"]:
        return verdict["output"]
    fb = default if isinstance(default, str) else DEFAULT
    return fb if audit_origin(fb, DEFAULT)["allowed"] else DEFAULT


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "originguard-allowlist", "kind": "improvement",
            "title": "Origin allowlist guard",
            "blurb": "?origin back-links only return to known app pages — "
                     "open-redirect shapes fall back to the queue.",
            "path": "/status", "anchor": "status-b8-originguard"}


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        "<h3 id='status-b8-originguard'>Origin allowlist guard</h3>"
        "<p>Card, clarity, already-know, and dispute forms carry a hidden "
        "<code>?origin</code> return target; <code>safe_origin()</code> keeps "
        "only same-origin paths naming a known app page "
        "(<code>/due</code>, <code>/modules/&lt;id&gt;</code>, …) and falls "
        "back to <code>/</code> otherwise — so every page added later gets "
        "an allowlist test instead of an open redirect. "
        "No DB change. <code>groundwork/originguard.py</code>.</p>"
    )
