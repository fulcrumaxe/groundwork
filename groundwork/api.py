"""Read-only JSON API: modules and due queue (F-451 slices).

Pure renderers over a database path — the web Handler delegates here.
"""
from __future__ import annotations

import json

from . import db as dbmod


def modules_json(db_path: str) -> str:
    """Every module with concept and card counts, newest first."""
    con = dbmod.connect(db_path)
    try:
        mods = con.execute(
            "SELECT id, task_summary, repo, created_at FROM modules"
            " ORDER BY created_at DESC").fetchall()
        out = []
        for m in mods:
            n_concepts = con.execute(
                "SELECT COUNT(*) FROM concepts WHERE module_id=?",
                (m["id"],)).fetchone()[0]
            n_cards = con.execute(
                "SELECT COUNT(*) FROM cards JOIN concepts"
                " ON concepts.id = cards.concept_id"
                " WHERE concepts.module_id=?",
                (m["id"],)).fetchone()[0]
            out.append({"id": m["id"],
                        "task_summary": m["task_summary"] or "",
                        "repo": m["repo"] or "",
                        "created_at": m["created_at"] or "",
                        "concepts": n_concepts, "cards": n_cards})
    finally:
        con.close()
    return json.dumps({"modules": out})


def due_json(db_path: str) -> str:
    """Live due queue, same order as the Due page."""
    from . import mcp as mcplib
    server = mcplib.MCPServer(db_path)
    due = server.tool_list_due_reviews({"limit": 100})["due"]
    slim = [{"id": c.get("id"), "concept": c.get("concept"),
             "front": c.get("front"), "due": c.get("due")}
            for c in due]
    return json.dumps({"due": slim, "count": len(slim)})
