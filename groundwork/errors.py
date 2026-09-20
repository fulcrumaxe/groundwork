"""Error pages: a 404 with somewhere to go (I-13).

Pure HTML over the unknown path — no HTTP, no page chrome. The web
Handler serves this for every miss instead of plain "not found". The
search box filters the module library by repo, which is a real route
(/modules?repo=), so it always does something honest.
"""
from __future__ import annotations

import html


def not_found_html(path: str, detail: str = "") -> str:
    """Unknown path (plus optional detail) with links and a repo search."""
    safe = html.escape(path or "/")
    extra = f"<p>{html.escape(detail)}</p>" if detail else ""
    return (
        f"<div id='not-found'><p>Nothing lives at <code>{safe}</code>.</p>"
        f"{extra}"
        "<p>Try a project search, or jump somewhere real:</p>"
        "<form method='get' action='/modules'>"
        "<input name='repo' placeholder='project repo path…'>"
        "<button>Find project</button></form>"
        "<p><a href='/'>Projects</a> · <a href='/due'>Due</a> · "
        "<a href='/modules'>Modules</a> · <a href='/reviews'>History</a> · "
        "<a href='/tour'>Tour</a> · <a href='/status'>Status</a></p></div>")
