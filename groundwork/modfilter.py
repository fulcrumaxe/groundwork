"""Modules index status filter (I-19): all / in-progress / owned / stale.

Pure helpers over the row-dicts the Modules page already builds —
``{"id": ..., "owned": int, "total": int, "stale": int}`` from
``modules_html`` (owned/total from ``ownership.owned_map``, stale from the
concepts/cards ``stale`` sum). No DB access, no schema change; stdlib only.
"""

from __future__ import annotations

import html
from urllib.parse import quote

STATUSES = ("all", "in-progress", "owned", "stale")

# Predicate order (first match wins):
#   1. stale       — stale > 0 (actionable review debt; wins even when
#                    the module is otherwise fully owned).
#   2. owned       — total > 0 and owned >= total (fully owned, nothing stale).
#   3. in-progress — everything else: partial progress, zero progress
#                    (not-started counts as in-progress so the tab never
#                    hides unstarted work), and empty modules (total == 0,
#                    which must NOT read as owned via 0 >= 0).


def _nums(row: dict) -> tuple[int, int, int]:
    """(owned, total, stale) as ints; missing/bad fields read as 0."""
    def num(key: str) -> int:
        try:
            return max(0, int(row.get(key, 0) or 0))
        except (TypeError, ValueError):
            return 0
    return num("owned"), num("total"), num("stale")


def classify(row: dict) -> str:
    """One of "stale" / "owned" / "in-progress" for a module row-dict."""
    if not isinstance(row, dict):
        return "in-progress"
    owned, total, stale = _nums(row)
    if stale > 0:
        return "stale"
    if total > 0 and owned >= total:
        return "owned"
    return "in-progress"


def normalize(status) -> str:
    """Canonical status key; unknown keys fall back to "all"."""
    return status if status in STATUSES else "all"


def filter_rows(rows: list, status: str) -> list:
    """Rows matching status key; "all" (and any unknown key) returns all."""
    key = normalize(status) if isinstance(status, str) else "all"
    if key == "all":
        return list(rows)
    return [r for r in rows if classify(r) == key]


def counts(rows: list) -> dict:
    """Per-tab counts: {"all": n, "in-progress": n, "owned": n, "stale": n}."""
    out = {"all": len(rows), "in-progress": 0, "owned": 0, "stale": 0}
    for r in rows:
        out[classify(r)] += 1
    return out


def _qs(status: str, sort: str = "newest", repo: str = "") -> str:
    parts = [f"status={quote(status, safe='')}"]
    if sort and sort != "newest":
        parts.append(f"sort={quote(sort, safe='')}")
    if repo:
        parts.append(f"repo={quote(repo, safe='')}")
    return "/modules?" + "&".join(parts)


def tabbar(rows: list, active: str = "all", sort: str = "newest",
           repo: str = "") -> str:
    """Filter-tab bar: one link per status with counts; active tab marked."""
    key = normalize(active) if isinstance(active, str) else "all"
    n = counts(rows)
    labels = {"all": "All", "in-progress": "In progress",
              "owned": "Owned", "stale": "Stale"}
    tabs = []
    for s in STATUSES:
        label = f"{labels[s]} ({n[s]})"
        if s == key:
            tabs.append(f"<b aria-current='page'>{html.escape(label)}</b>")
        else:
            tabs.append(f"<a href='{html.escape(_qs(s, sort, repo))}'>"
                        f"{html.escape(label)}</a>")
    return ("<p id='modfilter-tabs'><small>Filter: "
            + " · ".join(tabs) + "</small></p>")


def section_html() -> str:
    """Anchored Status-page home for this improvement (live demo)."""
    demo = [{"id": "m1", "owned": 0, "total": 3, "stale": 0},
            {"id": "m2", "owned": 3, "total": 3, "stale": 0},
            {"id": "m3", "owned": 1, "total": 4, "stale": 2}]
    return "".join([
        "<section id='status-b7-modfilter'>",
        "<h3>Module status filter <small>(improvement)</small></h3>",
        "<p>The Modules library filters by status: all, in-progress, owned, "
        "stale. Predicate order: stale wins, then fully-owned, else "
        "in-progress (unstarted counts as in-progress). "
        "<code>groundwork/modfilter.py</code>.</p>",
        tabbar(demo, "all"),
        "</section>",
    ])
