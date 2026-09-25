"""Rendered-page HTML snapshots with golden compare (I-95).

Renders core pages to normalized HTML strings and diffs them against
committed goldens so visual regressions fail the CI gate in
``tests/test_pagesnap.py``. Pure functions, stdlib only (``re``,
``hashlib``); ``web`` is imported lazily inside the render helpers so
this module stays import-safe. Never raises, never touches the DB
beyond what the caller's handler already read, never writes files
(the test, not this module, owns the golden directory).

Update procedure: ``UPDATE_GOLDENS=1 python3 -m unittest
tests.test_pagesnap`` rewrites ``tests/golden/*.html``; review the
``git diff`` before committing. CI never sets the flag.
"""
from __future__ import annotations

import hashlib
import re

STATUS_ANCHOR = "status-b18-pagesnap"

GOLDEN_DIR = "tests/golden"

PAGES = ("due", "status", "modules", "reviews")

_VOLATILE = (
    re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z?"),
    re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?"),
    re.compile(r"\b\d+ (seconds?|minutes?|hours?|days?) ago\b"),
    re.compile(r"\bjust now\b"),
    re.compile(r'data-built="[^"]*"'),
    re.compile(r"/modules/[0-9a-f]{8,128}"),
    re.compile(r"card-[0-9a-f]{8,128}(?:ex\d+)?"),
    re.compile(r"\b[0-9a-f]{12}\b"),
    re.compile(r"/tmp/[A-Za-z0-9_][A-Za-z0-9_.\-]*"),
)

_WS_BETWEEN = re.compile(r">\s+<")
_WS_RUN = re.compile(r"\s+")


def normalize(html_text) -> str:
    """Collapse a rendered page to a comparable string; never raises."""
    try:
        if not isinstance(html_text, str):
            return ""
        out = html_text.strip()
        for pat in _VOLATILE:
            out = pat.sub(" ", out)
        out = _WS_BETWEEN.sub("><", out)
        out = _WS_RUN.sub(" ", out)
        return out.strip()
    except Exception:  # noqa: BLE001 -- normalize never raises
        return ""


def fingerprint(html_text) -> str:
    """SHA-256 hex of the normalized page; "" normalizes first."""
    try:
        return hashlib.sha256(normalize(html_text).encode("utf-8")).hexdigest()
    except Exception:  # noqa: BLE001 -- fingerprint never raises
        return hashlib.sha256(b"").hexdigest()


def render_page(handler, name: str) -> str:
    """Render one core page via a live Handler; unknown fails to ""."""
    try:
        if handler is None or not isinstance(name, str):
            return ""
        if name == "due":
            return str(handler.due_html())
        if name == "status":
            return str(handler.status_html())
        if name == "modules":
            return str(handler.modules_html())
        if name == "reviews":
            return str(handler.history_html())
        if name == "module":
            mid = getattr(handler, "_pagesnap_mid", "") or ""
            if not mid:
                return ""
            return str(handler.module_html(mid))
        return ""
    except Exception:  # noqa: BLE001 -- render never raises
        return ""


def snapshot(handler, names=PAGES) -> dict:
    """Normalized HTML per page name; hostile input fails to {}."""
    try:
        if handler is None:
            return {}
        if not isinstance(names, (list, tuple)):
            return {}
        out = {}
        for name in names:
            if isinstance(name, str) and name:
                out[name] = normalize(render_page(handler, name))
        return out
    except Exception:  # noqa: BLE001 -- snapshot never raises
        return {}


def check_golden(name, html_text, golden: str) -> bool:
    """True when normalized render equals the normalized golden."""
    try:
        return normalize(html_text) == normalize(golden)
    except Exception:  # noqa: BLE001 -- compare never raises
        return False


def compare(snap: dict, goldens: dict) -> dict:
    """Diff a snapshot against goldens; never raises.

    Returns ``{"ok": bool, "drift": [...], "missing": [...],
    "extra": [...]}`` where drift names pages whose normalized HTML
    differs, missing names golden pages absent from the snapshot, and
    extra names snapshot pages with no golden.
    """
    try:
        if not isinstance(snap, dict) or not isinstance(goldens, dict):
            return {"ok": False, "drift": [], "missing": [], "extra": []}
        drift = [k for k in goldens
                 if k in snap and normalize(snap[k]) != normalize(goldens[k])]
        missing = [k for k in goldens if k not in snap]
        extra = [k for k in snap if k not in goldens]
        return {"ok": not drift and not missing and not extra,
                "drift": sorted(drift), "missing": sorted(missing),
                "extra": sorted(extra)}
    except Exception:  # noqa: BLE001 -- compare never raises
        return {"ok": False, "drift": [], "missing": [], "extra": []}


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Page snapshots <small>(improvement)</small></h3>"
        "<p>Core pages render to normalized HTML and diff against committed "
        "goldens under <code>tests/golden/</code>; unexpected drift fails "
        "the <code>tests/test_pagesnap.py</code> gate. "
        "<code>groundwork/pagesnap.py</code> provides "
        "<code>normalize()</code> (whitespace/volatile collapse), "
        "<code>snapshot()</code>, and <code>compare()</code>; refresh with "
        "<code>UPDATE_GOLDENS=1 python3 -m unittest "
        "tests.test_pagesnap</code> and review the diff before committing.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "page-snapshots", "kind": "improvement",
            "title": "Page snapshot goldens",
            "blurb": "Core pages diff against committed goldens; drift fails CI. See below.",
            "path": "/status", "anchor": STATUS_ANCHOR}
