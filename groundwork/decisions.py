"""Decision quotes in lessons (I-110): why the agent chose this way.

Matches MCP-recorded decisions to lesson nodes by symbol and renders
a small quote block per lesson. Lessons without a recorded decision
say so honestly — the anchor stays stable either way.
"""
from __future__ import annotations

import html

from . import db as dbmod


def _matches(node: str, symbol: str) -> bool:
    """A decision motivates a lesson when its symbol names the node."""
    sym = symbol or ""
    return bool(node) and (sym == node or sym.endswith("." + node)
                           or sym.endswith("/" + node)
                           or sym.endswith(":" + node))


def matches_for_module(db_path: str, nodes: list) -> dict:
    """All decisions attached to any of these lesson nodes."""
    con = dbmod.connect(db_path)
    try:
        rows = con.execute(
            "SELECT symbol, chosen, rejected, reason FROM decisions"
            " ORDER BY id").fetchall()
    finally:
        con.close()
    out: dict[str, list] = {n: [] for n in nodes}
    for r in rows:
        for n in nodes:
            if _matches(n, r["symbol"] or ""):
                out[n].append(dict(r))
    return out


def lesson_block(node: str, matches: list, anchor: bool = False) -> str:
    """Quote block for one lesson; honest empty state when none match."""
    mark = " id='decisions'" if anchor else ""
    if not matches:
        return (f"<p{mark}><small>No recorded agent decisions for this "
                f"lesson yet — see <a href='/status'>Status</a> for how "
                f"agents log them.</small></p>")
    quotes = "".join(
        f"<blockquote>Chose <b>{html.escape(m['chosen'] or '')}</b>"
        + (f" over {html.escape(m['rejected'])}" if m["rejected"] else "")
        + (f" — {html.escape(m['reason'])}" if m["reason"] else "")
        + "</blockquote>"
        for m in matches)
    return f"<div{mark}>{quotes}</div>"
