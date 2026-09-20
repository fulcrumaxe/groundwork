"""Per-page `data-page` hooks with a coverage registry (I-37).

`web.page()` stamps every response `<body data-page='<id>'>` so CSS/JS can
target pages exactly (`body[data-page=due]{...}`). This module owns the
closed registry of those ids, verified against every `page()` call site in
`groundwork/web.py`, plus the pure helpers a coverage test needs: exact
`valid()` membership, an `extract()` reader for rendered shells, the
supplemental `hooks_css()` (accent rules for the ids web.py CSS does not
cover yet: projects, journal), and `rows()`/`section_html()` for Status.
"""
from __future__ import annotations

import html
import re

DEFAULT_PAGE_ID = "projects"

# (page_id, route, note) — one row per distinct emitted hook.
PAGE_IDS = (
    ("projects", "/", "landing, search, and every default-id confirm screen"),
    ("due", "/due", "spaced queue; also /diagnose result chrome"),
    ("history", "/reviews", "attempt history"),
    ("modules", "/modules", "library, module detail, reset, module 404s"),
    ("debt", "/debt", "comprehension debt meter"),
    ("tour", "/tour", "tour catalog; also /styleguide chrome"),
    ("status", "/status", "machine-room page"),
    ("journal", "/journal", "private weekly journal"),
)

_HOOK_RE = re.compile(r"<body[^>]*\sdata-page='([^']*)'")


def all_ids() -> tuple:
    """Every registered hook id, in registry order."""
    return tuple(pid for pid, _, _ in PAGE_IDS)


def valid(page_id) -> bool:
    """Exact allowlist membership; False for anything not registered."""
    return isinstance(page_id, str) and page_id in all_ids()


def extract(rendered: str) -> str | None:
    """The `data-page` hook stamped on one rendered shell, else None."""
    if not isinstance(rendered, str):
        return None
    m = _HOOK_RE.search(rendered)
    return m.group(1) if m else None


def hooks_css() -> str:
    """Supplemental accent rules for ids web.py CSS leaves unstyled."""
    return ("body[data-page=projects]{--accent:#1f6f5c}"
            "body[data-page=journal]{--accent:#6b4e9b}")


def rows() -> str:
    """Registry table rows for the Status section."""
    return "".join(
        f"<tr><td><code>{html.escape(pid)}</code></td>"
        f"<td><code>{html.escape(route)}</code></td>"
        f"<td>{html.escape(note)}</td></tr>"
        for pid, route, note in PAGE_IDS)


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b8-pageids'>Per-page hooks <small>(improvement)</small></h3>"
        "<p>Every page stamps <code>&lt;body data-page='…'&gt;</code> from a "
        "closed registry of eight hooks, so future pages cannot ship unhooked. "
        "<code>groundwork/pageids.py</code>.</p>"
        "<table class='log'><tr><th>Hook</th><th>Route</th><th>Covers</th></tr>"
        f"{rows()}</table>"
    )
