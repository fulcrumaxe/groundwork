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


OWNED_MASTERY = 0.85


def _node_of(cid) -> str:
    """Bare node from a concept id (``calc.py:add`` -> ``add``)."""
    try:
        cid = str(cid or "")
        return cid.split(":", 1)[1] if ":" in cid else cid
    except Exception:  # noqa: BLE001 — id split never raises
        return ""


def skills_view(concepts, lesson_map=None, mastery_of=None) -> str:
    """Locked/unlocked skills section from live module data (F-54).

    ``concepts`` rows carry ``cid``/``name`` (sqlite rows or dicts);
    ``lesson_map`` gives each node's ``callees`` as its unlock
    prerequisites (own the dependencies to unlock the dependent) and
    ``mastery_of`` gives live mastery (≥0.85 owns it). Every concept
    renders its quest path with locked/unlocked steps. Empty or
    hostile input renders "". Never raises.
    """
    try:
        rows = list(concepts or [])
    except TypeError:
        return ""
    try:
        lesson_map = lesson_map if isinstance(lesson_map, dict) else {}
        mastery_of = mastery_of if isinstance(mastery_of, dict) else {}
        names: dict = {}
        entries: list = []
        for r in rows:
            try:
                cid = r["cid"]
                name = str(r["name"] or "").strip()
            except (TypeError, KeyError, IndexError):
                continue
            if not name:
                continue
            node = _node_of(cid)
            names[node] = name
            names[name] = name
            try:
                lesson = lesson_map.get(node, {})
                callees = lesson.get("callees", []) if isinstance(lesson, dict) else []
            except Exception:  # noqa: BLE001 — one bad lesson skips
                callees = []
            try:
                mastery = float(mastery_of.get(node, 0.0) or 0.0)
            except (TypeError, ValueError):
                mastery = 0.0
            entries.append((name, list(callees or []), mastery))
        if not entries:
            return ""
        edges: dict = {}
        for name, callees, _m in entries:
            reqs = []
            for c in callees:
                try:
                    key = str(c or "").strip()
                except Exception:  # noqa: BLE001 — bad prereq skips
                    continue
                if key:
                    reqs.append(names.get(key, key))
            edges[name] = reqs
        owned = [name for name, _c, m in entries if m >= OWNED_MASTERY]
        parts = ["<section id='quests'><h2>Unlock quests</h2>",
                 f"<p><small>{len(owned)} of {len(entries)} skills "
                 f"unlocked — own the dependencies to unlock the rest.</small></p>"]
        for name, _c, _m in entries:
            path = quest_path(name, edges, owned)
            state = ("unlocked" if path["unlocked"]
                     else f"locked — next: {path['next']}")
            parts.append(f"<h3>{htmlmod.escape(name)} "
                         f"<small>({htmlmod.escape(str(state))})</small></h3>"
                         + quests_html(path))
        parts.append("</section>")
        return "".join(parts)
    except Exception:  # noqa: BLE001 — section never raises
        return ""


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
