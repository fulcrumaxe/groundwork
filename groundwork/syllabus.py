"""Syllabus week gates: later weeks unlock only on owned proofs (F-175).

A syllabus is a shareable week plan traveling in the ``?syllabus=`` Due
link as JSON ({"format": "groundwork-syllabus/1", "title": str,
"weeks": [[concept names], ...]}). Week 1 is always open; week k opens
only when every earlier-week concept is owned (an ownership proof or
mastery >= 0.85). Unlike the display-only quest checklists, the gate is
enforced: ``gate_due`` withholds later-week cards from the Due queue
(the ramppack ``scope_due`` one-line precedent) and the banner names the
locked weeks. No spec returns the queue untouched and renders ""
(legacy bytes); unknown names never lock anything. Stdlib only
(``html``, ``json``) plus lazy sibling reads (``db``, ``ownership``);
no groundwork imports at module level; never raises.
"""
from __future__ import annotations

import html as htmlmod
import json

STATUS_ANCHOR = "status-b28-syllabus"
BOX_ANCHOR = "syllabus-gate"
FORMAT = "groundwork-syllabus/1"
OWNED_MASTERY = 0.85


def _name(v) -> str:
    try:
        return v.strip() if isinstance(v, str) and v.strip() else ""
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return ""


def parse_spec(value) -> dict:
    """{"title": str, "weeks": [[names]]}; garbage -> empty. Never raises."""
    try:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                return {"title": "", "weeks": []}
        if not isinstance(value, dict):
            return {"title": "", "weeks": []}
        if value.get("format") not in (FORMAT, None, ""):
            return {"title": "", "weeks": []}
        raw = value.get("weeks", [])
        if not isinstance(raw, (list, tuple)):
            return {"title": _name(value.get("title")), "weeks": []}
        weeks = []
        for wk in raw:
            if not isinstance(wk, (list, tuple)):
                continue
            names, seen = [], set()
            for n in wk:
                c = _name(n)
                if c and c not in seen:
                    seen.add(c)
                    names.append(c)
            weeks.append(names)
        return {"title": _name(value.get("title")), "weeks": weeks}
    except Exception:  # noqa: BLE001 -- parse must never raise
        return {"title": "", "weeks": []}


def _owned_set(owned, mastery_of, names) -> set:
    try:
        done = set()
        try:
            for o in (owned or []):
                n = _name(o)
                if n:
                    done.add(n)
        except TypeError:
            pass
        m = mastery_of if isinstance(mastery_of, dict) else {}
        for s in (names or []):
            try:
                if float(m.get(s, 0.0) or 0.0) >= OWNED_MASTERY:
                    done.add(s)
            except (TypeError, ValueError):
                continue
        return done
    except Exception:  # noqa: BLE001 -- set build must never raise
        return set()


def week_states(spec, owned=None, mastery_of=None, known=None) -> dict:
    """Per-week unlock over owned proofs; week 1 always open. Never raises.

    ``known`` (None = every name counts) bounds the spec to library
    names; unknown names are reported, never lock anything.
    """
    try:
        p = parse_spec(spec)
        try:
            know = {k for k in known} if known is not None else None
        except TypeError:
            know = None
        weeks, unknown = [], []
        for wk in p["weeks"]:
            keep = [n for n in wk if know is None or n in know]
            unknown += [n for n in wk if know is not None and n not in know]
            weeks.append(keep)
        done = _owned_set(owned, mastery_of,
                           [n for wk in weeks for n in wk])
        rows = []
        for i, wk in enumerate(weeks):
            if i == 0:
                unlocked = True
            else:
                earlier = [n for w in weeks[:i] for n in w]
                unlocked = all(n in done for n in earlier)
            d = sum(1 for n in wk if n in done)
            rows.append({"week": i + 1, "names": list(wk), "done": d,
                         "total": len(wk), "unlocked": unlocked,
                         "complete": d == len(wk)})
        open_no = len(rows)
        for r in rows:
            if not r["complete"]:
                open_no = r["week"]
                break
        return {"title": p["title"], "weeks": rows,
                "open": open_no if rows else 0, "total": len(rows),
                "complete": bool(rows) and all(r["complete"] for r in rows),
                "unknown": unknown}
    except Exception:  # noqa: BLE001 -- view must never raise
        return {"title": "", "weeks": [], "open": 0, "total": 0,
                "complete": False, "unknown": []}


def locked_names(spec, owned=None, mastery_of=None, known=None) -> set:
    """Known names in locked weeks; empty when all open. Never raises."""
    try:
        st = week_states(spec, owned, mastery_of, known)
        return {n for w in st["weeks"] if not w["unlocked"]
                for n in w["names"]}
    except Exception:  # noqa: BLE001 -- lookup must never raise
        return set()


def _library(db_path):
    """(names_by_id, mastery_by_name, owned_names); empties on error."""
    try:
        from . import db as dbmod
        from . import ownership as ownmod
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT id, module_id, name, mastery FROM concepts").fetchall()
            names, mastery, mids = {}, {}, set()
            for r in rows:
                try:
                    nm = str(r["name"] or "").strip()
                except (TypeError, KeyError, IndexError):
                    continue
                if not nm:
                    continue
                names[r["id"]] = nm
                try:
                    mastery[nm] = float(r["mastery"] or 0.0)
                except (TypeError, ValueError):
                    mastery[nm] = 0.0
                mids.add(r["module_id"])
            owned = set()
            for mid in mids:
                try:
                    omap = ownmod.owned_map(con, mid)
                except Exception:  # noqa: BLE001 -- one bad module skips
                    continue
                for cid, (_a, o) in omap.items():
                    if o and cid in names:
                        owned.add(names[cid])
            return names, mastery, owned
        finally:
            con.close()
    except Exception:  # noqa: BLE001 -- library lookup must never raise
        return {}, {}, set()


def _card_name(card, names_by_id) -> str:
    try:
        if isinstance(card, dict):
            cid = card.get("concept_id", "")
        else:
            cid = card["concept_id"]
        return names_by_id.get(cid, "")
    except Exception:  # noqa: BLE001 -- unmapped cards pass through
        return ""


def gate_due(db_path, due, spec):
    """Due rows minus locked-week cards; the same list with no spec."""
    try:
        if not parse_spec(spec)["weeks"]:
            return due
        if not isinstance(due, list):
            return due
        names_by_id, mastery, owned = _library(db_path)
        if not names_by_id:
            return due
        locked = locked_names(spec, owned, mastery,
                               set(names_by_id.values()))
        if not locked:
            return due
        return [c for c in due
                if _card_name(c, names_by_id) not in locked]
    except Exception:  # noqa: BLE001 -- gate must never raise
        return due


def states_html(states) -> str:
    """Week-gate banner over week_states(); "" when empty. Never raises."""
    try:
        if not isinstance(states, dict) or not states.get("weeks"):
            return ""
        title = htmlmod.escape(states.get("title") or "Syllabus weeks")
        try:
            open_no, total = int(states.get("open", 0)), len(states["weeks"])
        except (TypeError, ValueError):
            open_no, total = 0, len(states["weeks"])
        rows = states["weeks"]
        hidden = sum(len(w.get("names", [])) for w in rows
                     if not w.get("unlocked"))
        items = []
        for w in rows:
            try:
                names = [n for n in w.get("names", []) if _name(n)]
                d, t, k = int(w.get("done", 0)), len(names), int(w.get("week", 0))
            except (TypeError, ValueError):
                continue
            if w.get("unlocked"):
                items.append(f"<li>Week {k}: {d}/{t} owned (open)</li>")
            else:
                need = ", ".join(htmlmod.escape(n) for n in names[:6])
                more = f" +{len(names) - 6} more" if len(names) > 6 else ""
                items.append(f"<li>Week {k}: {d}/{t} owned "
                             f"(locked -- needs: {need}{more})</li>")
        head = (f"<section id='{BOX_ANCHOR}'><h2>{title}</h2>"
                f"<p><small>Week {open_no} of {total} open -- "
                f"{hidden} later-week concepts withheld until earlier weeks "
                f"are owned (a modify/create pass plus a return visit, or "
                f"mastery 0.85).</small></p>"
                f"<ol class='syllabus-weeks'>{''.join(items)}</ol>")
        unknown = [n for n in (states.get("unknown") or []) if _name(n)]
        tail = ""
        if unknown:
            names = ", ".join(htmlmod.escape(n) for n in unknown[:6])
            tail += ("<p><small>Unknown syllabus names ignored "
                     f"(never locking): {names}.</small></p>")
        tail += "<p><small><a href='/due'>Clear syllabus</a></small></p></section>"
        return head + tail
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def banner_html(db_path, spec) -> str:
    """Week-gate banner for the Due queue; "" with no spec. Never raises."""
    try:
        if not parse_spec(spec)["weeks"]:
            return ""
        names_by_id, mastery, owned = _library(db_path)
        if not names_by_id:
            return ""
        return states_html(week_states(spec, owned, mastery,
                                        set(names_by_id.values())))
    except Exception:  # noqa: BLE001 -- banner must never raise
        return ""


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "syllabus-gates",
        "kind": "feature",
        "title": "Syllabus week gates",
        "blurb": ("Later syllabus weeks stay locked until earlier weeks are "
                  "owned -- the Due queue withholds locked-week cards."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }


def section_html() -> str:
    """Anchored status subsection with a deterministic demo."""
    try:
        demo = states_html(week_states(
            {"format": FORMAT, "title": "Demo syllabus",
             "weeks": [["Read lessons"], ["Grade cards"],
                       ["Serve the queue"]]},
            owned={"Read lessons"}))
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Syllabus week gates "
            "<small>(feature)</small></h3>"
            "<p>Week plans travel in a shareable <code>?syllabus=</code> Due "
            "link; each later week opens only when every earlier-week "
            "concept is owned. The gate is enforced: "
            "<code>Handler.due_html</code> withholds locked-week cards "
            "(<code>groundwork/syllabus.py</code>).</p>"
            f"{demo}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Syllabus week gates</h3>"
                "<p>Week gates temporarily unavailable.</p>")
