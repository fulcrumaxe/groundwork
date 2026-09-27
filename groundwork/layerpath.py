"""Layered onboarding path: foundations first, week by week (F-154).

A newcomer opening a module sees lessons in pipeline order, not
learning order. This module computes a Start-here study path from the
module's own lesson graph: lessons declaring ``needs``/``depends_on``
layer by depth (entry points first, then their dependents), unknown
needs ignored, cycles terminating in a deterministic final layer.

Caller: ``Handler.module_html`` appends ``starthere_html`` beside the
onboard countdown; modules whose lessons declare no needs render ""
(legacy bytes). Jump links reuse the ``lesson-<slug>`` anchors the
module page already renders. Stdlib only (``html``) plus sibling
``lessondeps``/``lessons`` reads; never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b27-layerpath"
BOX_ANCHOR = "start-here"


def _str(value) -> str:
    try:
        return value if isinstance(value, str) else ""
    except Exception:  # noqa: BLE001
        return ""


def _lname(lesson, i=0) -> str:
    """Display name of one lesson dict; "" when nameless/hostile."""
    try:
        if isinstance(lesson, dict):
            for k in ("name", "concept"):
                v = lesson.get(k, "")
                if isinstance(v, str) and v.strip():
                    return v.strip()
        return ""
    except Exception:  # noqa: BLE001
        return ""


def _needs(lesson) -> list:
    """Declared in-module dependency names; [] when none/hostile."""
    try:
        from . import lessondeps as lessondepsmod
        return lessondepsmod.needs_of(lesson)
    except Exception:  # noqa: BLE001
        return []


def _items(lessons) -> list:
    """[{node, name, needs}] from a lesson map or list; [] when hostile."""
    try:
        if isinstance(lessons, dict):
            pairs = list(lessons.items())
        elif isinstance(lessons, (list, tuple)):
            pairs = [(None, L) for L in lessons]
        else:
            return []
        out = []
        for i, (node, L) in enumerate(pairs):
            if not isinstance(L, dict):
                continue
            name = _lname(L, i)
            if not name:
                continue
            key = _str(L.get("concept_id", "")).strip()
            out.append({"node": _str(node) or key,
                        "name": name, "key": key,
                        "needs": [n for n in _needs(L) if n]})
        return out
    except Exception:  # noqa: BLE001
        return []


def layers_for(lessons) -> list:
    """Names grouped by dependency depth; entry points first.

    Layer 0 holds lessons with no in-module needs; layer k+1 holds
    lessons whose in-module needs all sit in layers <= k. Leftovers
    (dependency cycles) append as one final layer in lexicographic
    order, so output is deterministic for any input order.
    """
    try:
        items = _items(lessons)
        if not items:
            return []
        fold = {}
        for x in items:
            fold.setdefault(x["name"].casefold(), x["name"])
        indeg = {}
        for x in items:
            indeg.setdefault(x["name"], set())
            for need in x["needs"]:
                hit = fold.get(_str(need).casefold())
                if hit and hit != x["name"]:
                    indeg[x["name"]].add(hit)
        placed = {}
        layers = []
        remaining = {x["name"] for x in items}
        while remaining:
            ready = sorted(n for n in remaining
                           if all(d in placed for d in indeg.get(n, ())))
            if not ready:  # cycle: deterministic final layer
                ready = sorted(remaining)
            depth = len(layers)
            for n in ready:
                placed[n] = depth
            layers.append(ready)
            remaining -= set(ready)
        return layers
    except Exception:  # noqa: BLE001
        return []


def _done_ids(owned) -> set:
    """Owned concept ids (+ suffixes) from an owned map or set."""
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


def layered_path(lessons, owned=None) -> dict:
    """{layers, flat, next}: the ordered path plus the next step.

    ``layers`` is [[{name, node, done}]] prereqs-first; ``flat`` the
    same steps concatenated; ``next`` the first unowned step name (or
    None when everything is owned or nothing is listed).
    """
    try:
        items = _items(lessons)
        by_name = {x["name"]: x for x in items}
        done = _done_ids(owned)
        layers = []
        for names in layers_for(lessons):
            layer = []
            for n in names:
                x = by_name.get(n, {})
                keys = {n, x.get("node", ""), x.get("key", "")} - {""}
                layer.append({"name": n, "node": x.get("node", ""),
                              "done": bool(keys & done)})
            layers.append(layer)
        flat = [s for layer in layers for s in layer]
        nxt = next((s["name"] for s in flat if not s["done"]), None)
        return {"layers": layers, "flat": flat, "next": nxt}
    except Exception:  # noqa: BLE001
        return {"layers": [], "flat": [], "next": None}


def starthere_html(lesson_map, owned=None) -> str:
    """Start-here block with weekly layers; "" when no graph data.

    Renders only when at least one lesson declares needs -- repos
    without dependency data keep legacy page bytes.
    """
    try:
        items = _items(lesson_map)
        if not items or not any(x["needs"] for x in items):
            return ""
        from . import lessons as lesmod
        path = layered_path(lesson_map, owned)
        if not path["flat"]:
            return ""
        groups = []
        for i, layer in enumerate(path["layers"]):
            lis = "".join(
                f"<li>{'[x]' if s['done'] else '[ ]'} "
                f"<a href='#lesson-{lesmod.slug(s['node'] or s['name'])}'>"
                f"{html.escape(s['name'])}</a></li>"
                for s in layer)
            groups.append(f"<h3>Week {i + 1}</h3><ul>{lis}</ul>")
        nxt = path["next"]
        lead = (f"<p>Start with <b>{html.escape(nxt)}</b> -- "
                "foundations first, then their dependents.</p>"
                if nxt else "<p>Every step owned -- path complete.</p>")
        return (f"<section id='{BOX_ANCHOR}'><h2>Start here</h2>"
                f"{lead}{''.join(groups)}</section>")
    except Exception:  # noqa: BLE001 -- caller keeps legacy bytes
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch27 home module."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Layered onboarding path "
        "<small>(feature)</small></h3>"
        "<p>Each module page whose lessons declare needs gains a "
        "Start-here block grouping concepts into weekly layers -- "
        "entry points first, then dependents -- via "
        "<code>layerpath.layers_for()</code> / "
        "<code>starthere_html()</code>, grafted onto "
        "<code>Handler.module_html</code>. Modules without dependency "
        "data render nothing. <code>groundwork/layerpath.py</code>.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "layered-onboarding-path",
        "kind": "feature",
        "title": "Layered onboarding path",
        "blurb": ("Newcomers get a Start-here study path grouped by week: "
                  "foundations first, then their dependents, computed "
                  "from your own module graph."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
