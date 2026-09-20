"""File-map mini-view: where a concept sits in the repo tree (I-128).

One pure helper renders a server-side HTML breadcrumb + sibling
mini-tree from a list of repo-relative paths. No I/O, no DB changes.
"""
from __future__ import annotations

import html


def _norm(path) -> str:
    if not isinstance(path, str):
        return ""
    path = path.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path.strip("/")


def file_map(paths, current: str = "") -> str:
    """Breadcrumb + sibling mini-tree HTML; stable id='filemap' anchor."""
    cur = _norm(current)
    seen = []
    for p in paths or []:
        n = _norm(p)
        if n and n not in seen:
            seen.append(n)
    crumbs = ""
    if cur:
        parts = cur.split("/")
        links = []
        for i, part in enumerate(parts):
            href = "/".join(parts[:i + 1])
            links.append(
                f"<a href='#{html.escape(href, quote=True)}'>"
                f"{html.escape(part)}</a>")
        crumbs = "<nav class='crumbs'>" + " / ".join(links) + "</nav>"
    items = "".join(
        f"<li>{'<strong>' if p == cur else ''}"
        f"{html.escape(p)}{'</strong>' if p == cur else ''}</li>"
        for p in seen)
    return f"<div id='filemap'>{crumbs}<ul class='minitree'>{items}</ul></div>"
