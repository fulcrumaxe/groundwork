"""Status page: the machine room with a home for every section.

All Status sections assemble here — CI, hooks, CLI, MCP, exports,
sharing, module health, disputes, API, sitemap, seed, storage. The web
Handler keeps one delegation line; new sections land in this file or in
their own area module's section_html, never in web.py.
"""
from __future__ import annotations

from pathlib import Path

from . import db as dbmod
from . import disputes as dismod
from . import mcp as mcplib
from . import modularity as modularitymod
from . import northstar as northstarmod
from . import sched as schedmod
from . import storage as storagemod


def page_html(db_path: str) -> str:
    """Visible home for the non-page items, plus the area sections."""
    root = Path(__file__).resolve().parent.parent
    ci = root / ".github" / "workflows" / "groundwork.yml"
    hook = root / "hooks" / "pre-commit"
    now = schedmod.iso(schedmod.utcnow())
    con = dbmod.connect(db_path)
    try:
        due = con.execute(
            "SELECT COUNT(*) FROM cards WHERE due <= ? AND stale = 0",
            (now,)).fetchone()[0]
        cards = con.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
        mods = con.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
    finally:
        con.close()
    tools = sorted(m[5:] for m in dir(mcplib.MCPServer)
                   if m.startswith("tool_"))
    ci_mark = ("<span class='status-ok'>present</span>"
               if ci.exists() else "<span class='status-missing'>missing</span>")
    hook_ok = hook.exists() and bool(hook.stat().st_mode & 0o111)
    hook_mark = ("<span class='status-ok'>present, executable</span>"
                 if hook_ok
                 else "<span class='status-missing'>missing or not executable</span>")
    return "".join([
        "<p>Machine-room items that have no page of their own live here, "
        "so the tour can point at them.</p>",
        f"<h2 id='status-ci'>CI workflow</h2><p>{ci_mark} — "
        "<code>.github/workflows/groundwork.yml</code>, runs the test suite on push.</p>",
        f"<h2 id='status-hooks'>Pre-commit hook</h2><p>{hook_mark} — "
        "<code>hooks/pre-commit</code>.</p>",
        f"<h2 id='status-cli'>CLI review</h2><p><code>python3 -m groundwork "
        f"review --limit 20</code> — {due} cards due right now.</p>",
        f"<h2 id='status-mcp'>MCP endpoint</h2><p><code>python3 -m groundwork mcp</code> "
        f"and <code>POST /mcp</code> — tools: {', '.join(tools)}.</p>",
        f"<h2 id='status-exports'>Exports</h2><p>{cards} cards in {mods} modules — "
        "<a href='/export/anki.tsv'>Anki TSV</a> · "
        "<a href='/feed.xml'>RSS feed</a> · "
        "<span id='status-csv'><a href='/export/reviews.csv'>"
        "Review log CSV</a></span>.</p>",
        "<h2 id='status-share'>Module sharing</h2>"
        "<p><code>python3 -m groundwork export-module --module ID --out share.json</code> "
        "downloads a module; <code>python3 -m groundwork import-module --in share.json</code> "
        "loads it into another database. Reviews stay private; scheduling restarts fresh. "
        "<span id='status-badge'><a href='/badge.svg'>README badge</a></span> "
        "embeds your live owned count in any README.</p>",
        "<h2 id='status-modular'>Module health</h2>" +
        modularitymod.status_rows() +
        northstarmod.section_html(db_path) +
        "<h2 id='status-disputes'>Grade disputes</h2>" +
        dismod.queue_html(db_path) +
        storagemod.section_html(db_path) +
        "<h2 id='status-api'>Read-only API</h2>"
        "<p><a href='/api/modules.json'>/api/modules.json</a> lists "
        "every module with concept and card counts — the first slice "
        "of a public read API for dashboards. "
        "<span id='status-api-due'><a href='/api/due.json'>"
        "/api/due.json</a> exposes the live due queue.</span></p>",
        "<h2 id='status-sitemap'>Sitemap</h2>"
        "<p><a href='/sitemap.xml'>sitemap.xml</a> lists every page and "
        "module for self-hosters; <a href='/robots.txt'>robots.txt</a> "
        "points crawlers at it.</p>",
        "<h2 id='status-seed'>Groundwork seed</h2>"
        "<p>Groundwork itself is a learnable project: "
        "<code>python3 -m groundwork export-seed --repo PATH --out seed.json</code> "
        "bundles every module under one repo into a portable seed file, and "
        "<code>python3 -m groundwork import-seed --in seed.json</code> "
        "loads it into any database — duplicates skip cleanly, reviews stay private.</p>",
    ])
