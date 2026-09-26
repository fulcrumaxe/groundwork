"""Onboarding countdown (F-135): day N of 30 + core-flow checklist.

A new hire opening a module sees which day of their first 30 they are
on (counted from their first review in this module) and which core
flows to own first: entry-point lessons, then most-depended-upon
concepts from the lessons' needs graph. Gentle, no streaks.
Caller: Handler.module_html (beside the owned-progress bar), fed only
by already-fetched history/owned/lesson_map. Inactive (no history,
day > 30) returns "" so pages keep legacy bytes. No DB/schema changes.
"""
from __future__ import annotations

import html
from datetime import date

STATUS_ANCHOR = "status-b25-onboard"
BOX_ANCHOR = "onboard"
WINDOW_DAYS = 30
FLOW_N = 5
_NEED_KEYS = ("needs", "depends_on")


def _str(v):
    try:
        return v if isinstance(v, str) else ("" if v is None else str(v))
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return ""


def _day(v):
    try:
        t = _str(v).strip()
        return date.fromisoformat(t[:10]) if len(t) >= 10 else None
    except (ValueError, TypeError):
        return None


def _end(now):
    if isinstance(now, date):
        return now
    if isinstance(now, str) and now.strip():
        return _day(now)
    if now is None or now == "":
        return date.today()
    return None


def first_seen_from(rows) -> str:
    """Earliest reviewed_at across history rows, or ""."""
    try:
        best = ""
        if isinstance(rows, dict):
            rows = [r for rs in rows.values() for r in (rs or [])]
        for r in rows or []:
            try:
                w = r.get("reviewed_at", r.get("when", "")) if isinstance(r, dict) else r[0]
            except (TypeError, IndexError, KeyError):
                continue
            s = _str(w).strip()
            if _day(s) is not None and (not best or s < best):
                best = s
        return best
    except Exception:  # noqa: BLE001 -- scan must never raise
        return ""


def day_of(first_seen, now=""):
    """1-based day in window from first_seen; None when unknown."""
    try:
        s, e = _day(first_seen), _end(now)
        if s is None or e is None:
            return None
        return max(1, (e - s).days + 1)
    except Exception:  # noqa: BLE001 -- math must never raise
        return None


def is_active(first_seen, now="") -> bool:
    try:
        d = day_of(first_seen, now)
        return d is not None and 1 <= d <= WINDOW_DAYS
    except Exception:  # noqa: BLE001 -- gate must never raise
        return False


def _needs(lesson) -> list:
    try:
        if not isinstance(lesson, dict):
            return []
        out = []
        for k in _NEED_KEYS:
            raw = lesson.get(k, [])
            if isinstance(raw, str):
                raw = [raw]
            for n in (raw if isinstance(raw, (list, tuple)) else []):
                if isinstance(n, str) and n.strip() and n.strip() not in out:
                    out.append(n.strip())
        return out
    except Exception:  # noqa: BLE001 -- read must never raise
        return []


def _lname(lesson, i=0) -> str:
    try:
        if isinstance(lesson, dict):
            for k in ("name", "concept"):
                v = lesson.get(k, "")
                if isinstance(v, str) and v.strip():
                    return v.strip()
        return _str(lesson) or f"lesson-{i}"
    except Exception:  # noqa: BLE001 -- read must never raise
        return f"lesson-{i}"


def _key(lesson) -> str:
    try:
        c = lesson.get("concept_id", "") if isinstance(lesson, dict) else ""
        return _str(c).strip()
    except Exception:  # noqa: BLE001 -- read must never raise
        return ""


def core_flows(lessons, limit=FLOW_N) -> list:
    """[{name,key}] entry points first, then most-depended-upon."""
    try:
        n = int(limit)
    except (TypeError, ValueError):
        n = FLOW_N
    if n <= 0:
        return []
    try:
        items = [{"name": _lname(L, i), "key": _key(L),
                  "needs": _needs(L)} for i, L in enumerate(lessons or [])]
        items = [x for x in items if x["name"]]
        if not items:
            return []
        fold = {x["name"].casefold(): x["name"] for x in items}
        indeg = {x["name"]: 0 for x in items}
        for x in items:
            for need in x["needs"]:
                hit = fold.get(need.casefold())
                if hit and hit != x["name"]:
                    indeg[hit] += 1
        entry = [x for x in items if not x["needs"]]
        rest = sorted((x for x in items if x["needs"]),
                      key=lambda x: -indeg[x["name"]])
        return [{"name": x["name"], "key": x["key"]} for x in (entry + rest)[:n]]
    except Exception:  # noqa: BLE001 -- ranking must never raise
        return []


def _owned_ids(owned) -> set:
    ids = set()
    try:
        it = owned.items() if isinstance(owned, dict) else [(v, True) for v in (owned or [])]
        for k, v in it:
            ok = v[1] if isinstance(v, (list, tuple)) and len(v) > 1 else v
            if ok:
                s = _str(k).strip()
                if s:
                    ids.add(s)
                    ids.add(s.split(":", 1)[-1])
    except Exception:  # noqa: BLE001 -- set build must never raise
        pass
    return ids


def checklist(flows, owned) -> list:
    """Flows annotated with done from owned-map/set; never raises."""
    try:
        ids = _owned_ids(owned)
        out = []
        for f in flows or []:
            nm = f.get("name", "") if isinstance(f, dict) else _str(f)
            key = f.get("key", "") if isinstance(f, dict) else ""
            keys = {nm, key, key.split(":", 1)[-1]} - {""}
            out.append({"name": nm, "done": bool(keys & ids)})
        return [x for x in out if x["name"]]
    except Exception:  # noqa: BLE001 -- annotate must never raise
        return []


def countdown_box_html(first_seen=None, lessons=(), owned=None,
                       rows=None, now="") -> str:
    """Day-N-of-30 banner + checklist; "" when inactive/unknown."""
    try:
        seen = _str(first_seen).strip() or (first_seen_from(rows) if rows is not None else "")
        d = day_of(seen, now)
        if d is None or d > WINDOW_DAYS:
            return ""
        flows = checklist(core_flows(lessons), owned)
        lis = "".join(f"<li>{'[x]' if f['done'] else '[ ]'} {html.escape(f['name'])}</li>" for f in flows)
        left = WINDOW_DAYS - d
        tail = "last day — finish gently" if left == 0 else f"{left} days left — no rush, no streaks"
        return (f"<section id='{BOX_ANCHOR}'><h2>Day {d} of {WINDOW_DAYS}</h2>"
                f"<p>{tail}. Own these core flows first:</p>"
                + (f"<ul>{lis}</ul>" if lis else "") + "</section>")
    except Exception:  # noqa: BLE001 -- banner must never raise
        return ""


def tour_entry() -> dict:
    """Tour registry entry for the onboarding countdown."""
    return {"id": "onboard-countdown", "kind": "feature",
            "title": "Onboarding countdown",
            "blurb": ("Day N of 30 from your first review, with the core "
                      "flows to own first — gentle, no streaks."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    return (f"<h3 id='{STATUS_ANCHOR}'>Onboarding countdown <small>(feature)</small></h3>"
            "<p>Each module shows day N of 30 from the learner's first review "
            "plus a core-flow checklist (entry points, then most-depended-upon "
            "concepts). <code>groundwork/onboard.py</code> provides "
            "<code>day_of()</code>, <code>core_flows()</code> and "
            "<code>countdown_box_html()</code>, grafted onto "
            "<code>Handler.module_html</code>; outside the window it renders nothing.</p>")
