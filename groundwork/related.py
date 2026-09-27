"""Related modules (I-23): same repo or shared concept names.

Pure renderer over a database path + module id — the module page
calls related_html at the bottom. Always renders (with an honest
empty state) so the tour anchor never moves.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import whysee as whyseemod


def related_html(db_path: str, mid: str) -> str:
    """Other modules from the same repo or teaching the same concepts."""
    con = dbmod.connect(db_path)
    try:
        me = con.execute("SELECT repo FROM modules WHERE id=?",
                         (mid,)).fetchone()
        if me is None:
            return ""
        names = [r[0] for r in con.execute(
            "SELECT name FROM concepts WHERE module_id=?", (mid,)).fetchall()]
        same_repo = con.execute(
            "SELECT id, task_summary FROM modules WHERE repo = ? AND id != ?"
            " ORDER BY created_at DESC LIMIT 10",
            (me["repo"] or "", mid)).fetchall()
        shared: list = []
        if names:
            shared = con.execute(
                "SELECT DISTINCT modules.id, modules.task_summary FROM concepts"
                " JOIN modules ON modules.id = concepts.module_id"
                f" WHERE concepts.name IN ({','.join('?' * len(names))})"
                " AND concepts.module_id != ? LIMIT 10",
                (*names, mid)).fetchall()
        shared_names: dict = {}
        found = [r["id"] for r in list(same_repo) + list(shared)]
        if names and found:
            for mod_id, cname in con.execute(
                    "SELECT concepts.module_id, concepts.name FROM concepts"
                    f" WHERE concepts.module_id IN ({','.join('?' * len(found))})"
                    f" AND concepts.name IN ({','.join('?' * len(names))})",
                    (*found, *names)).fetchall():
                shared_names.setdefault(mod_id, [])
                if cname and cname not in shared_names[mod_id]:
                    shared_names[mod_id].append(cname)
    finally:
        con.close()
    seen = {mid}
    repo_ids = {r["id"] for r in same_repo}
    items = []
    for r in list(same_repo) + list(shared):
        if r["id"] in seen:
            continue
        seen.add(r["id"])
        why = whyseemod.reason_html(whyseemod.reason_for(
            "related", {"same_repo": r["id"] in repo_ids,
                        "shared": shared_names.get(r["id"], [])}))
        items.append(
            f"<li><a href='/modules/{r['id']}'>"
            f"{html.escape(r['task_summary'] or r['id'])}</a>"
            f" {why}</li>")
    if not items:
        return ("<h2 id='related'>Related modules</h2><p>No related "
                "modules yet — related means the same repo or shared "
                "concept names.</p>")
    return ("<h2 id='related'>Related modules</h2><ul>"
            + "".join(items) + "</ul>")
