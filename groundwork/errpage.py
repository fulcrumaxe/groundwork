"""Error pages with full page chrome (I-83): no naked stack traces.

Today an unhandled exception inside the request handler propagates out
of ``BaseHTTPRequestHandler`` and the browser gets a dropped
connection — no header, no footer, no next step. This module owns the
500 body the handler renders instead: the same nav links and footer
arrive via ``web.page`` chrome (the caller wraps this body exactly
like the 404 path), so a crash still offers Projects, Due, Modules,
History, and Status.

``server_error_html`` never echoes exception text, file paths, or line
numbers: only the exception *type name* (letters/dots, everything else
falls back to "Error") is shown, so tracebacks cannot leak. Pure
functions, stdlib only (``html``, ``re``), no I/O, no DB changes.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b13-errpage"

#: Exception type names only: dotted identifiers, nothing else.
_TYPE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")

#: Fragments that must never reach the browser (traceback anatomy).
_FORBIDDEN = ("Traceback", "File \"", ", line ", ".py")


def safe_kind(value) -> str:
    """Exception type name safe for display; garbage fails closed."""
    try:
        if isinstance(value, str):
            name = value
        elif isinstance(value, BaseException):
            name = type(value).__name__
        else:
            return "Error"
        name = (name or "").strip()
        if _TYPE_RE.match(name) and len(name) <= 80:
            return name
        return "Error"
    except Exception:  # noqa: BLE001 -- error page must never raise
        return "Error"


def server_error_html(kind: str = "", ref: str = "") -> str:
    """500 body: apology, safe kind, and somewhere real to go.

    ``ref`` is an opaque server-side correlation id (never a path);
    non-matching values are dropped, never echoed raw.
    """
    try:
        label = safe_kind(kind) if kind else "Error"
        try:
            ok_ref = bool(re.fullmatch(r"[A-Za-z0-9-]{1,32}", ref or ""))
        except Exception:  # noqa: BLE001 -- never raise
            ok_ref = False
        ref_line = (f"<p><small>Reference: "
                    f"{html.escape(ref)}</small></p>" if ok_ref else "")
        return (
            "<div id='server-error'>"
            "<p>Something broke on our side "
            f"(<code>{html.escape(label)}</code>) — nothing you typed "
            "caused it, and nothing was graded.</p>"
            f"{ref_line}"
            "<p>Keep going somewhere real:</p>"
            "<p><a class='btn' href='/due'>Back to queue</a> "
            "<a href='/'>Projects</a> · <a href='/modules'>Modules</a> · "
            "<a href='/reviews'>History</a> · "
            "<a href='/status'>Status</a></p></div>")
    except Exception:  # noqa: BLE001 -- error page must never raise
        return ("<div id='server-error'><p>Something broke on our side.</p>"
                "<p><a href='/due'>Back to queue</a></p></div>")


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Chrome error pages <small>(improvement)</small></h3>"
        "<p>Unhandled handler exceptions now render inside the normal "
        "page chrome instead of dropping the connection: "
        "<code>groundwork/errpage.py</code> provides "
        "<code>server_error_html()</code> (safe exception-type label, "
        "optional correlation ref, links back to the queue), the handler "
        "delegates to it on any <code>Exception</code>, and traceback "
        "anatomy — frames, file paths, line numbers — never reaches the "
        "browser. Helpers fail closed, never raise.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "error-pages",
        "kind": "improvement",
        "title": "Chrome error pages",
        "blurb": "Server errors render inside the normal header and footer with a safe label and a way back — never a naked dropped connection.",
        "path": "/status",
        "anchor": "status-b13-errpage",
    }
