"""Prerequisite unlock quests: own X to unlock Y, shown as a path (F-54).

A quest is the existing Understand-X-first chain plus unlock state —
never a competing chain format: ``quest_path()`` linearises the
prerequisite edges from ``groundwork/prereq.py`` into an ordered
``chain`` (earliest first, target last) and derives ``unlocked``/``next``
from the owned set, while ``quests_html()`` renders that path as a small
ordered list with locked/unlocked classes. Pure functions, stdlib only
(``html``), no groundwork imports, no I/O, no DB/schema changes.
All entry points fail closed and never raise.
"""
from __future__ import annotations

import html as htmlmod

STATUS_ANCHOR = "status-b12-quests"

QUEST_ID = "unlock-quests"


def _name(value) -> str:
    """Coerce a node name; unusable input becomes ""."""
    try:
        if isinstance(value, str) and value.strip():
            return value.strip()
    except Exception:  # noqa: BLE001 — coercion must never raise
        pass
    return ""


def _prereqs(edges, node: str) -> list:
    """Prerequisite names for one node; hostile shapes fail closed to []."""
    try:
        if not isinstance(edges, dict):
            return []
        reqs = edges.get(node, [])
        if not isinstance(reqs, (list, tuple)):
            return []
        return [r.strip() for r in reqs
                if isinstance(r, str) and r.strip()]
    except Exception:  # noqa: BLE001 — lookup must never raise
        return []


def _owned_set(owned) -> set:
    """Coerce the owned collection to a set of names; never raises."""
    try:
        if isinstance(owned, (set, frozenset, list, tuple)):
            return {o.strip() for o in owned
                    if isinstance(o, str) and o.strip()}
    except Exception:  # noqa: BLE001 — coercion must never raise
        pass
    return set()


def quest_path(target, edges=None, owned=None) -> dict:
    """Unlock path for ``target`` over ``edges`` given ``owned``.

    ``edges`` maps a node to its prerequisites (``{Y: [X]}`` means own
    X to unlock Y). Returns ``{"chain": [...], "unlocked": bool,
    "next": str | None}`` where ``chain`` runs earliest-prereq first
    and ends at ``target``, ``unlocked`` is True when every step is
    owned, and ``next`` is the first unowned step (None when unlocked).
    Unknown/missing nodes fail closed to the single-step path
    ``[target]``; cycles terminate via a visited set. Never raises.
    """
    try:
        name = _name(target)
        if not name:
            return {"chain": [], "unlocked": False, "next": None}
        owned_set = _owned_set(owned)
        order: list = []
        visited: set = set()

        def visit(node: str) -> None:
            if node in visited:
                return
            visited.add(node)  # added before recursing: cycles terminate
            for req in _prereqs(edges, node):
                if req not in visited:
                    visit(req)
            order.append(node)

        visit(name)
        try:
            nxt = next((c for c in order if c not in owned_set), None)
        except Exception:  # noqa: BLE001 — scan must never raise
            nxt = order[0] if order else None
        try:
            unlocked = all(c in owned_set for c in order) and bool(order)
        except Exception:  # noqa: BLE001 — check must never raise
            unlocked = False
        return {"chain": order, "unlocked": unlocked, "next": nxt}
    except Exception:  # noqa: BLE001 — path builder must never raise
        try:
            name = _name(target)
            return {"chain": [name] if name else [], "unlocked": False,
                    "next": name or None}
        except Exception:  # noqa: BLE001 — fallback must never raise
            return {"chain": [], "unlocked": False, "next": None}


def quests_html(path) -> str:
    """Ordered-list unlock path with locked/unlocked classes.

    Steps before ``path["next"]`` render ``quest-unlocked``, ``next``
    and later render ``quest-locked`` (all unlocked when ``next`` is
    None). Names are escaped; emits no ``<style>`` tags. Empty or
    hostile input renders "". Never raises.
    """
    try:
        if not isinstance(path, dict):
            return ""
        chain = path.get("chain", [])
        if not isinstance(chain, (list, tuple)) or not chain:
            return ""
        names = [_name(c) for c in chain]
        names = [n for n in names if n]
        if not names:
            return ""
        nxt = path.get("next", None)
        nxt = nxt.strip() if isinstance(nxt, str) and nxt.strip() else None
        try:
            cut = names.index(nxt) if nxt in names else len(names)
        except Exception:  # noqa: BLE001 — index must never raise
            cut = len(names)
        items = []
        for i, step in enumerate(names):
            cls = "quest-unlocked" if i < cut else "quest-locked"
            items.append(f"<li class='{cls}'>"
                         f"{htmlmod.escape(step)}</li>")
        return "<ol class='quest-path'>" + "".join(items) + "</ol>"
    except Exception:  # noqa: BLE001 — renderer must never raise
        return ""


def tour_entry() -> dict:
    """Feature-tour registry entry for the parent to append."""
    return {"id": QUEST_ID, "kind": "feature",
            "title": "Unlock quests",
            "blurb": "Own X to unlock Y — each locked skill shows its "
                     "unlock path, step by step.",
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection with a live quest demo; db-free."""
    try:
        demo = quests_html(quest_path(
            "Serve the queue",
            {"Serve the queue": ["Grade cards", "Read lessons"],
             "Grade cards": ["Read lessons"], "Read lessons": []},
            owned={"Read lessons"}))
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Unlock quests "
            "<small>(feature)</small></h3>"
            "<p>Prerequisite chains become unlock quests: own X to unlock "
            "Y, shown as a path with locked and unlocked steps. "
            f"{demo} "
            "<code>groundwork/quests.py</code> provides "
            "<code>quest_path()</code> (pure chain + unlock state over the "
            "Understand-X-first edges — missing nodes fail closed to a "
            "single step, cycles terminate via a visited set) and "
            "<code>quests_html()</code> (escaped "
            "<code>&lt;ol&gt;</code> markup, no "
            "<code>&lt;style&gt;</code> tags); both never raise.</p>"
        )
    except Exception:  # noqa: BLE001 — status must always render
        return f"<h3 id='{STATUS_ANCHOR}'>Unlock quests</h3>"
