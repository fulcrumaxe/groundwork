"""Unlock animation for newly available lessons (I-148).

A lesson whose prerequisites are all owned, but which is itself
unowned, is newly available — it pops with a calm badge reusing
the shared ``mo-reveal`` keyframe (240ms, reduced-motion gated in
motion_css, so still users keep a static badge). Freshness derives
purely from current state (edges + mastery), never history:
badge_for() builds both from the lesson map. No edges, empty
mastery, or hostile input renders "" (legacy bytes). Pure
functions, stdlib html only; never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b23-unlockfx"

OWNED_MASTERY = 0.85


def _name(value) -> str:
    try:
        if isinstance(value, str) and value.strip():
            return value.strip()
    except Exception:  # noqa: BLE001 -- names must never raise
        pass
    return ""


def is_fresh(name, edges=None, owned=None) -> bool:
    """True when every prereq of ``name`` is owned but ``name`` is not."""
    try:
        target = _name(name)
        if not target:
            return False
        edges = edges if isinstance(edges, dict) else {}
        owned = set(owned) if owned else set()
        if target in owned:
            return False
        prereqs = edges.get(target) or []
        if not isinstance(prereqs, (list, tuple, set)):
            return False
        if not prereqs:
            return False
        return all(p in owned for p in prereqs)
    except Exception:  # noqa: BLE001 -- freshness must never raise
        return False


def fresh_names(edges=None, owned=None) -> list:
    """Every newly-available node; hostile input gives []."""
    try:
        edges = edges if isinstance(edges, dict) else {}
        return [n for n in edges if is_fresh(n, edges, owned)]
    except Exception:  # noqa: BLE001 -- listing must never raise
        return []


def badge_html(name, fresh: bool = False) -> str:
    """Unlock badge when fresh, else "" (legacy fallback)."""
    try:
        if not fresh:
            return ""
        return ("<span class='unlock-fx mo-reveal'>Unlocked — new</span>")
    except Exception:  # noqa: BLE001 -- badge must never raise
        return ""


def badge_for(node, lesson_map=None, mastery_of=None) -> str:
    """Badge for one lesson node from live map + mastery (the caller)."""
    try:
        target = _name(node)
        if not target or not isinstance(lesson_map, dict):
            return ""
        edges = {}
        for key, lesson in lesson_map.items():
            try:
                callees = (lesson or {}).get("callees") or []
                edges[str(key)] = [str(c) for c in callees]
            except (AttributeError, TypeError):
                continue
        owned = set()
        try:
            for key, mastery in (mastery_of or {}).items():
                if (mastery or 0.0) >= OWNED_MASTERY:
                    owned.add(str(key))
        except AttributeError:
            pass
        return badge_html(target, is_fresh(target, edges, owned))
    except Exception:  # noqa: BLE001 -- badge must never raise
        return ""


def badge_css() -> str:
    """Raw declarations for the static badge; parent concats to head."""
    try:
        return (".unlock-fx{display:inline-block;margin-left:.4em;"
                "padding:.05em .5em;border:1px solid currentColor;"
                "border-radius:999px;font-size:.8em;white-space:nowrap}")
    except Exception:  # noqa: BLE001 -- CSS emitter must never raise
        return ".unlock-fx{display:inline-block}"


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Unlock animation "
            "<small>(improvement)</small></h3>"
            "<p>Newly unlocked lessons pop — "
            "<code>groundwork/unlockfx.py</code> badges lessons whose "
            "prerequisites are owned but which are themselves unowned, "
            "reusing the shared 240ms reveal (still when reduced-motion "
            "is set).</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Unlock animation</h3>"
                "<p>Unlock-animation help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "unlock-fx",
        "kind": "improvement",
        "title": "Unlock animation",
        "blurb": ("Newly unlocked lessons pop with a calm badge — still "
                  "when reduced-motion is set."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
