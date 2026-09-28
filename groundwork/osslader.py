"""Open-source contributor ladder: newcomer to subsystem owner (F-192).

A single-user study app has no GitHub-issue feed and no external
contributor data, so this ladder is computed only from live owned
proofs (``ownership.owned_map``: a modify/create pass plus a return
visit) and the module's own lesson graph. Four rungs:

- Newcomer: nothing owned yet.
- First patch (the good-first-issue analog): the first owned concept.
- Contributor: at least half the subsystem owned (3+ concepts).
- Subsystem owner: every concept in the module owned.

The suggested next step is the first unowned entry-point concept --
a lesson with no in-module needs -- so it reads as a good first
issue; without graph data it falls back to definition order.

Caller: ``Handler.module_html`` appends ``ladder_html`` beside the
Start-here block; modules with no concepts render "" (legacy bytes).
Jump links reuse the ``lesson-<slug>`` anchors the module page
already renders. Stdlib only (``html``) plus sibling ``lessons`` /
``layerpath`` reads; never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b29-osslader"
BOX_ANCHOR = "oss-ladder"

RUNGS = ("Newcomer", "First patch", "Contributor", "Subsystem owner")


def _str(value) -> str:
    try:
        return value if isinstance(value, str) else ""
    except Exception:  # noqa: BLE001
        return ""


def _cell(row, *keys) -> str:
    """First non-blank string cell; "" when missing/hostile.

    Bracket access covers lesson dicts and sqlite concept rows alike.
    """
    for k in keys:
        try:
            v = row[k]
        except Exception:  # noqa: BLE001
            continue
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def _rows(concepts) -> list:
    """[{cid, node, name}] from concept rows; [] when hostile."""
    try:
        if isinstance(concepts, dict):
            seq = list(concepts.values())
        elif isinstance(concepts, (list, tuple)):
            seq = list(concepts)
        else:
            return []
        out = []
        for r in seq:
            name = _cell(r, "name", "concept")
            if not name:
                continue
            cid = _cell(r, "cid", "concept_id", "id", "node")
            node = cid.split(":", 1)[-1] if ":" in cid else cid
            out.append({"cid": cid, "node": node, "name": name})
        return out
    except Exception:  # noqa: BLE001
        return []


def _done_ids(owned) -> set:
    """Owned ids (+ suffixes) from an owned map or set."""
    try:
        if isinstance(owned, dict):
            ids = {c for c, v in owned.items()
                   if (v[1] if isinstance(v, (list, tuple)) else v)}
        elif isinstance(owned, (set, list, tuple)):
            ids = {str(c) for c in owned}
        else:
            return set()
        out = set(ids)
        for c in ids:
            if isinstance(c, str) and ":" in c:
                out.add(c.split(":", 1)[-1])
        return out
    except Exception:  # noqa: BLE001
        return set()


def rung_for(owned_n, total) -> int:
    """Rung index 0-3 from owned/total counts; 0 when hostile/empty."""
    try:
        n = int(owned_n)
        t = int(total)
    except (TypeError, ValueError):
        return 0
    if t <= 0 or n <= 0:
        return 0
    if n >= t:
        return 3
    if t >= 3 and n >= (t + 1) // 2:
        return 2
    return 1


def _order(lesson_map, rows) -> list:
    """Prereqs-first names from the lesson graph; definition fallback."""
    try:
        from . import layerpath as layerpathmod
        layers = layerpathmod.layers_for(lesson_map)
        if layers:
            return [n for layer in layers for n in layer]
    except Exception:  # noqa: BLE001
        pass
    return [r["name"] for r in rows]


def _good_first(rows, done, lesson_map):
    """First unowned entry-point row; None when everything is owned."""
    try:
        pending = [r for r in rows
                   if not ({r["cid"], r["node"], r["name"]} - {""} & done)]
        if not pending:
            return None
        want = [_str(n).casefold() for n in _order(lesson_map, rows)]
        if want:
            rank = {n: i for i, n in enumerate(want)}
            pend0 = len(rank)
            pending.sort(key=lambda r: rank.get(r["name"].casefold(),
                                               rank.get(r["node"].casefold(), pend0)))
        return pending[0]
    except Exception:  # noqa: BLE001
        return None


def ladder_for(concepts, owned=None, lesson_map=None) -> dict:
    """{rung, rung_name, owned_n, total, rungs, next}: the live ladder.

    ``rungs`` is [{name, reached, current}] for all four rungs;
    ``next`` the good-first-issue step ({name, node} or None).
    """
    try:
        rows = _rows(concepts)
        done = _done_ids(owned)
        owned_n = sum(1 for r in rows
                       if ({r["cid"], r["node"], r["name"]} - {""}) & done)
        total = len(rows)
        rung = rung_for(owned_n, total)
        nxt = _good_first(rows, done, lesson_map)
        return {
            "rung": rung,
            "rung_name": RUNGS[rung],
            "owned_n": owned_n,
            "total": total,
            "rungs": [{"name": name, "reached": i <= rung,
                       "current": i == rung}
                      for i, name in enumerate(RUNGS)],
            "next": ({"name": nxt["name"], "node": nxt["node"]}
                     if nxt else None),
        }
    except Exception:  # noqa: BLE001
        return {"rung": 0, "rung_name": RUNGS[0], "owned_n": 0,
                "total": 0, "rungs": [], "next": None}


def _slug(node_or_name) -> str:
    try:
        from . import lessons as lesmod
        return lesmod.slug(node_or_name)
    except Exception:  # noqa: BLE001
        return ""


def ladder_html(concepts, owned=None, lesson_map=None) -> str:
    """Contributor-ladder block; "" when the module has no concepts.

    Shows the reached rungs plus the good-first-issue next step, so a
    newcomer sees rung 1 of 4 and a subsystem owner sees all four
    reached. Empty or hostile input keeps legacy page bytes.
    """
    try:
        rows = _rows(concepts)
        if not rows:
            return ""
        lad = ladder_for(rows, owned, lesson_map)
        lis = "".join(
            f"<li>{'[x]' if r['reached'] else '[ ]'} "
            f"{'<b>' if r['current'] else ''}{html.escape(r['name'])}"
            f"{'</b>' if r['current'] else ''}</li>"
            for r in lad["rungs"])
        lead = (f"<p>Rung {lad['rung'] + 1} of 4: "
                f"<b>{html.escape(lad['rung_name'])}</b> -- "
                f"{lad['owned_n']}/{lad['total']} concepts owned.</p>")
        nxt = lad["next"]
        if nxt is None:
            tail = ("<p>Every concept proven -- subsystem owned. "
                    "Pick another module to climb again.</p>")
        else:
            slug = _slug(nxt["node"] or nxt["name"])
            ref = (f"<a href='#lesson-{slug}'>{html.escape(nxt['name'])}</a>"
                   if slug else html.escape(nxt["name"]))
            nxt_rung = RUNGS[min(lad["rung"] + 1, 3)]
            tail = (f"<p>Good first issue: start with {ref} -- the next "
                    f"unowned step toward <b>{html.escape(nxt_rung)}</b>.</p>")
        return (f"<section id='{BOX_ANCHOR}'><h2>Contributor ladder</h2>"
                f"{lead}<ul>{lis}</ul>{tail}</section>")
    except Exception:  # noqa: BLE001 -- caller keeps legacy bytes
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch29 home module."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Open-source contributor ladder "
        "<small>(feature)</small></h3>"
        "<p>Each module page gains a contributor ladder -- Newcomer, "
        "First patch, Contributor, Subsystem owner -- computed from "
        "live owned proofs plus the module's own lesson graph via "
        "<code>osslader.rung_for()</code> / "
        "<code>ladder_html()</code>, grafted onto "
        "<code>Handler.module_html</code>. The next step names the "
        "first unowned entry-point concept as a good first issue; "
        "modules without concepts render nothing. "
        "<code>groundwork/osslader.py</code>.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "oss-contributor-ladder",
        "kind": "feature",
        "title": "Open-source contributor ladder",
        "blurb": ("Study modules grow a contributor ladder -- first patch "
                  "to owned subsystem -- computed from your own proofs, "
                  "with the next good first issue named."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
