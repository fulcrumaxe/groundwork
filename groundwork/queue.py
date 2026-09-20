"""Due queue grouping (I-44): one collapsible section per module.

Pure grouping over the due list — the web Handler iterates groups
instead of a flat list, so multi-module queues stay scannable.
"""
from __future__ import annotations

from . import db as dbmod


def groups(db_path: str, due: list) -> list:
    """Due cards gathered by module, first-seen module order.

    Each group is {"mid": ..., "title": ..., "cards": [...]}.
    Cards whose concept vanished land in an "Unknown module" tail group.
    """
    want = [c.get("concept_id", "") for c in due]
    titles: dict[str, dict] = {}
    if want:
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT concepts.id AS cid, concepts.module_id AS mid,"
                " modules.task_summary AS summary FROM concepts"
                " LEFT JOIN modules ON modules.id = concepts.module_id"
                f" WHERE concepts.id IN ({','.join('?' * len(want))})",
                want).fetchall()
        finally:
            con.close()
        for r in rows:
            titles[r["cid"]] = {"mid": r["mid"] or "",
                                "title": r["summary"] or r["mid"] or ""}
    out: list = []
    by_mid: dict[str, dict] = {}
    for c in due:
        info = titles.get(c.get("concept_id", ""), {"mid": "", "title": ""})
        mid = info["mid"]
        if mid not in by_mid:
            grp = {"mid": mid,
                   "title": info["title"] or "Unknown module",
                   "cards": []}
            by_mid[mid] = grp
            out.append(grp)
        by_mid[mid]["cards"].append(c)
    return out
