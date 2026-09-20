"""Tool-call analytics (F-389): which MCP tools fire, failure rates.

Pure renderer over a database path — dispatch() logs every call and
this Status section aggregates per tool. Always renders (with a
quiet empty state) so the tour anchor never moves.
"""
from __future__ import annotations

from . import db as dbmod


def section_html(db_path: str) -> str:
    """Per-tool calls, failure share and mean latency."""
    con = dbmod.connect(db_path)
    try:
        try:
            rows = con.execute(
                "SELECT method, COUNT(*) AS n,"
                " SUM(CASE WHEN ok = 0 THEN 1 ELSE 0 END) AS bad,"
                " AVG(ms) AS ms FROM tool_calls"
                " GROUP BY method ORDER BY n DESC LIMIT 20").fetchall()
        except Exception:  # noqa: BLE001 — pre-analytics DBs
            rows = []
    finally:
        con.close()
    if not rows:
        return ("<h2 id='status-tools'>Tool calls</h2>"
                "<p>No MCP tool calls logged yet — connect an agent and "
                "they appear here with failure rates.</p>")
    cells = "".join(
        f"<tr><td>{(r['method'] or '')}</td><td>{r['n']}</td>"
        f"<td>{round(100 * (r['bad'] or 0) / r['n'])}%</td>"
        f"<td>{(r['ms'] or 0):.1f} ms</td></tr>" for r in rows)
    return ("<h2 id='status-tools'>Tool calls</h2>"
            "<table class='log'><tr><th>Tool</th><th>Calls</th>"
            "<th>Failed</th><th>Mean</th></tr>" + cells + "</table>")
