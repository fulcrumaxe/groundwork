"""Classroom quests (F-130): teacher-defined checklists, completion-based.

A quest spec is a shareable JSON doc ({"format": "groundwork-quest/1",
"title": str, "steps": [concept names]}) traveling in the ?quest=
module-page link; completion derives from owned/mastery already in
the DB. Pure functions, stdlib only, no I/O, no DB/schema changes,
never raises. No spec renders "" (legacy bytes); no ranking anywhere.
"""
from __future__ import annotations

import html as htmlmod
import json

STATUS_ANCHOR = "status-b25-classquests"
FORMAT = "groundwork-quest/1"
OWNED_MASTERY = 0.85


def _name(v) -> str:
    try:
        return v.strip() if isinstance(v, str) and v.strip() else ""
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return ""


def parse_spec(value) -> dict:
    """{"title": str, "steps": [...]}; blanks/dupes dropped; garbage -> empty."""
    try:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                return {"title": "", "steps": []}
        if not isinstance(value, dict):
            return {"title": "", "steps": []}
        steps, seen = [], set()
        raw = value.get("steps", [])
        if isinstance(raw, (list, tuple)):
            for s in raw:
                n = _name(s)
                if n and n not in seen:
                    seen.add(n)
                    steps.append(n)
        return {"title": _name(value.get("title")), "steps": steps}
    except Exception:  # noqa: BLE001 -- parse must never raise
        return {"title": "", "steps": []}


def _owned_set(owned, mastery_of, steps) -> set:
    done = set()
    try:
        for o in (owned or []):
            n = _name(o)
            if n:
                done.add(n)
    except TypeError:
        pass
    try:
        m = mastery_of if isinstance(mastery_of, dict) else {}
        for s in steps:
            try:
                if float(m.get(s, 0.0) or 0.0) >= OWNED_MASTERY:
                    done.add(s)
            except (TypeError, ValueError):
                continue
    except Exception:  # noqa: BLE001 -- set build must never raise
        pass
    return done


def quest_view(spec, owned=None, mastery_of=None) -> dict:
    """Completion over teacher order; no ranking. Never raises."""
    try:
        p = parse_spec(spec)
        done = _owned_set(owned, mastery_of, p["steps"])
        rows = [{"name": s, "done": s in done} for s in p["steps"]]
        n = sum(1 for r in rows if r["done"])
        nxt = next((r["name"] for r in rows if not r["done"]), None)
        return {"title": p["title"], "steps": rows, "done": n,
                "total": len(rows),
                "complete": bool(rows) and n == len(rows), "next": nxt}
    except Exception:  # noqa: BLE001 -- view must never raise
        return {"title": "", "steps": [], "done": 0, "total": 0,
                "complete": False, "next": None}


def quest_html(spec, owned=None, mastery_of=None) -> str:
    """Checklist section; "" with no spec/steps. Escaped, no <style>."""
    try:
        v = quest_view(spec, owned, mastery_of)
        if not v["steps"]:
            return ""
        items = "".join(
            f"<li class='{'quest-done' if s['done'] else 'quest-todo'}'>"
            f"{htmlmod.escape(s['name'])}</li>" for s in v["steps"])
        title = htmlmod.escape(v["title"] or "Classroom quest")
        flag = " — quest complete" if v["complete"] else ""
        return (f"<section id='classquests'><h2>{title}</h2>"
                f"<p><small>{v['done']} of {v['total']} steps complete{flag}.</small></p>"
                f"<ol class='quest-steps'>{items}</ol></section>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def tour_entry() -> dict:
    """Tour registry entry for classroom quests."""
    return {"id": "classroom-quests", "kind": "feature",
            "title": "Classroom quests",
            "blurb": ("Teacher-defined checklists graded by what you "
                      "already own — complete, never ranked."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection with live demo; db-free."""
    try:
        demo = quest_html({"format": FORMAT, "title": "Week 3: serving",
                           "steps": ["Read lessons", "Grade cards", "Serve the queue"]},
                          owned={"Read lessons"})
        return (f"<h3 id='{STATUS_ANCHOR}'>Classroom quests <small>(feature)</small></h3>"
                "<p>Teacher-defined ordered checklists; completion derives from owned/mastery, "
                "no ranking, no new tables. <code>groundwork/classquests.py</code> renders on "
                "<code>Handler.module_html</code> with a <code>?quest=</code> spec.</p>" f"{demo}")
    except Exception:  # noqa: BLE001 -- status must always render
        return f"<h3 id='{STATUS_ANCHOR}'>Classroom quests</h3>"
