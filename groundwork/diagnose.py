"""Traceback diagnose page: mentioned symbols link to lessons (F-390).

Pure renderer over a database path — the web Handler delegates here.
"""
from __future__ import annotations

import html
import re

from . import db as dbmod
from . import lessons as lesmod


def _trace_symbols(text: str) -> list[str]:
    """Symbol names mentioned in a pasted Python traceback, most recent last."""
    frames = re.findall(r'File "[^"]+", line \d+, in (\S+)', text)
    names = re.findall(r"(?:NameError|AttributeError)[^:\n]*:?[^'\"]*['\"]([\w_]+)['\"]", text)
    seen = []
    for n in frames + names:
        if n != "<module>" and n not in seen:
            seen.append(n)
    return seen


def diagnose_html(db_path: str, trace: str = "") -> str:
    """Paste-a-traceback bridge: mentioned symbols → their lessons."""
    form = ("<form method='post' action='/diagnose' id='diagnose-form'>"
            "<textarea name='trace' rows='8' cols='70' placeholder='Paste a Python traceback…'>"
            f"{html.escape(trace)}</textarea><br>"
            "<button>Find my lessons</button></form>")
    if not trace.strip():
        return (form + "<p><small>Paste the red text from a crash — "
                "every function it names links to its lesson.</small></p>")
    names = _trace_symbols(trace)
    if not names:
        return form + "<p>No function names found in that text.</p>"
    con = dbmod.connect(db_path)
    try:
        found = []
        missing = []
        for n in names:
            row = con.execute(
                "SELECT concepts.id, concepts.name, concepts.module_id,"
                " modules.task_summary FROM concepts"
                " JOIN modules ON modules.id = concepts.module_id"
                " WHERE concepts.name = ? LIMIT 1", (n,)).fetchone()
            (found if row else missing).append((n, row))
    finally:
        con.close()
    parts = [form, "<h2>Study these, then diagnose</h2>"]
    for n, row in found:
        node = row["id"].split(":", 1)[1] if ":" in row["id"] else row["id"]
        parts.append(
            f"<p><a href='/modules/{row['module_id']}#lesson-{lesmod.slug(node)}'>"
            f"{html.escape(n)}</a> "
            f"<small>in {html.escape(row['task_summary'] or row['module_id'])}</small></p>")
    if missing:
        parts.append("<p><small>Unknown here: "
                     + ", ".join(html.escape(n) for n, _ in missing)
                     + "</small></p>")
    return "".join(parts)
