"""Self-assigned study plans: scope, set, deadline, owned-proof tracking (F-164).

A teacher's assignment builder needs rosters and gradebooks this
single-user app will never have. The honest solo slice: assign
YOURSELF a plan -- repo scope, concept set, due date -- traveling
only in the ``?assign=`` URL (bookmark it, nothing persisted), with
completion tracked from your own owned proofs and mastery, never
ranked. Cross-student tracking and teacher roles are explicitly out.

Caller: ``Handler.module_html`` appends ``assign_html``; both new
params None renders "" (legacy bytes). Stdlib only (``html``,
``json``, ``math``, ``datetime``, ``urllib.parse``); no groundwork
imports; never raises.
"""
from __future__ import annotations

import html
import json
import math
from datetime import date
from urllib.parse import quote

STATUS_ANCHOR = "status-b27-selfassign"
BOX_ANCHOR = "selfassign"
FORMAT = "groundwork-assign/1"
OWNED_MASTERY = 0.85


def _name(v) -> str:
    try:
        return v.strip() if isinstance(v, str) and v.strip() else ""
    except Exception:  # noqa: BLE001
        return ""


def parse_spec(value) -> dict:
    """{title, repo, due, steps}; garbage -> empty. Never raises."""
    empty = {"title": "", "repo": "", "due": "", "steps": []}
    try:
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except ValueError:
                return dict(empty)
        if not isinstance(value, dict):
            return dict(empty)
        if value.get("format") not in (FORMAT, None, ""):
            return dict(empty)
        steps, seen = [], set()
        raw = value.get("steps", [])
        if isinstance(raw, (list, tuple)):
            for s in raw:
                n = _name(s)
                if n and n not in seen:
                    seen.add(n)
                    steps.append(n)
        due = _name(value.get("due"))
        if due:
            try:
                date.fromisoformat(due)
            except ValueError:
                due = ""
        return {"title": _name(value.get("title")),
                "repo": _name(value.get("repo")), "due": due, "steps": steps}
    except Exception:  # noqa: BLE001
        return dict(empty)


def build_spec(title, due, steps, repo="") -> dict:
    """Assemble a spec from builder fields; same shape as parse_spec."""
    return parse_spec({"format": FORMAT, "title": title or "",
                       "repo": repo or "", "due": due or "",
                       "steps": list(steps or [])})


def spec_json(spec) -> str:
    """Canonical share-link JSON; "" when hostile."""
    try:
        s = parse_spec(spec)
        if not s["steps"]:
            return ""
        return json.dumps({"format": FORMAT, "title": s["title"],
                           "repo": s["repo"], "due": s["due"],
                           "steps": s["steps"]}, sort_keys=True)
    except Exception:  # noqa: BLE001
        return ""


def _today(now):
    if isinstance(now, date):
        return now
    if isinstance(now, str) and now.strip():
        try:
            return date.fromisoformat(now.strip()[:10])
        except ValueError:
            pass
    return date.today()


def days_left(due, now="") -> int | None:
    """Inclusive working days incl. the due day; None when undated."""
    try:
        d = _name(due)
        if not d:
            return None
        delta = (date.fromisoformat(d) - _today(now)).days
        return delta if delta < 0 else delta + 1
    except Exception:  # noqa: BLE001
        return None


def plan_view(spec, owned=None, mastery_of=None, repo="", now="") -> dict:
    """Completion, countdown, and pace over the spec steps."""
    try:
        p = parse_spec(spec)
        done = set()
        try:
            for o in (owned or []):
                n = _name(o)
                if n:
                    done.add(n)
        except TypeError:
            pass
        m = mastery_of if isinstance(mastery_of, dict) else {}
        for s in p["steps"]:
            try:
                if float(m.get(s, 0.0) or 0.0) >= OWNED_MASTERY:
                    done.add(s)
            except (TypeError, ValueError):
                continue
        rows = [{"name": s, "done": s in done} for s in p["steps"]]
        n = sum(1 for r in rows if r["done"])
        left = days_left(p["due"], now)
        remaining = len(rows) - n
        if left is None or left <= 0 or remaining <= 0:
            pace = None
        else:
            pace = int(math.ceil(remaining / left))
        scope_ok = (not p["repo"]) or (p["repo"] == _name(repo))
        return {"title": p["title"], "repo": p["repo"], "scope_ok": scope_ok,
                "due": p["due"], "days_left": left,
                "overdue": left is not None and left < 0,
                "steps": rows, "done": n, "total": len(rows),
                "complete": bool(rows) and n == len(rows),
                "next": next((r["name"] for r in rows if not r["done"]), None),
                "pace": pace}
    except Exception:  # noqa: BLE001
        return {"title": "", "repo": "", "scope_ok": True, "due": "",
                "days_left": None, "overdue": False, "steps": [],
                "done": 0, "total": 0, "complete": False, "next": None,
                "pace": None}


def plan_html(spec, owned=None, mastery_of=None, repo="", now="",
              share_link="") -> str:
    """Rendered plan section; "" with no steps. Never raises."""
    try:
        v = plan_view(spec, owned, mastery_of, repo, now)
        if not v["steps"]:
            return ""
        items = "".join(
            f"<li class='{'quest-done' if s['done'] else 'quest-todo'}'>"
            f"{html.escape(s['name'])}</li>" for s in v["steps"])
        title = html.escape(v["title"] or "Self-assigned plan")
        flag = " -- complete" if v["complete"] else ""
        if v["due"] and v["days_left"] is not None:
            if v["overdue"]:
                when = f"overdue by {-v['days_left']} days"
            elif v["days_left"] == 1:
                when = "due today"
            else:
                when = f"{v['days_left']} days left (due {v['due']})"
            when = f" -- {html.escape(when)}"
        else:
            when = ""
        pace = (f" -- pace: {v['pace']}/day" if v["pace"] else "")
        scope = ("" if v["scope_ok"] else
                 "<p><small>Scope mismatch: this plan targets another "
                 "repo.</small></p>")
        link = (f"<p><small>Share link: <a href='{html.escape(share_link, quote=True)}'>"
                "plan link</a> (bookmark it -- nothing is stored).</small></p>"
                if share_link else "")
        return (f"<section id='{BOX_ANCHOR}'><h2>{title}</h2>"
                f"<p><small>{v['done']} of {v['total']} steps complete{flag}"
                f"{when}{pace}.</small></p>"
                f"<ol class='quest-steps'>{items}</ol>{scope}{link}</section>")
    except Exception:  # noqa: BLE001
        return ""


def builder_html(names, repo="", mid="") -> str:
    """GET builder form bounded to the page's concepts. Never raises."""
    try:
        boxes = "".join(
            f"<label><input type='checkbox' name='astep' value='{html.escape(n, quote=True)}'> "
            f"{html.escape(n)}</label><br>"
            for n in (names or []) if _name(n))
        if not boxes:
            return ""
        return (
            f"<section id='{BOX_ANCHOR}'><h2>New study plan</h2>"
            f"<form method='get' action='/modules/{html.escape(mid or '', quote=True)}'>"
            "<input type='hidden' name='assign' value='new'>"
            "<label>Title: <input name='atitle' size='30'></label><br>"
            "<label>Due: <input name='adue' placeholder='YYYY-MM-DD' size='12'></label><br>"
            f"{boxes}"
            f"<input type='hidden' name='arepo' value='{html.escape(repo, quote=True)}'>"
            "<button>Build plan</button></form></section>")
    except Exception:  # noqa: BLE001
        return ""


def assign_html(spec, fields, names, owned=None, mastery_of=None,
                repo="", mid="", now="") -> str:
    """Single dispatcher: spec -> plan, fields -> built plan, new -> builder."""
    try:
        if isinstance(spec, str) and spec == "new":
            if isinstance(fields, dict) and fields.get("steps"):
                built = build_spec(fields.get("title", ""),
                                   fields.get("due", ""),
                                   fields.get("steps", []),
                                   fields.get("repo", "") or repo)
                js = spec_json(built)
                link = (f"/modules/{mid}?assign={quote(js)}" if js and mid else "")
                return plan_html(built, owned, mastery_of, repo, now, link)
            return builder_html(names, repo, mid)
        if spec:
            js = spec if isinstance(spec, str) else spec_json(spec)
            link = (f"/modules/{mid}?assign={quote(js)}"
                    if js and mid and isinstance(js, str) else "")
            return plan_html(spec, owned, mastery_of, repo, now, link)
        return ""
    except Exception:  # noqa: BLE001
        return ""


def section_html() -> str:
    """Anchored status subsection with a deterministic demo."""
    try:
        demo = plan_html({"format": FORMAT, "title": "Demo plan",
                          "repo": "", "due": "2026-10-04",
                          "steps": ["add", "total", "append"]},
                         ["add"], {}, "", "2026-09-27")
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Self-assigned study plans "
            "<small>(feature)</small></h3>"
            "<p>Pick your repo scope, concept set, and due date -- "
            "completion tracked from your own owned proofs, never "
            "ranked. The plan travels in a shareable "
            "<code>?assign=</code> link; countdown, pace, and checklist "
            "below (<code>Handler.module_html</code>). "
            "<code>groundwork/selfassign.py</code>.</p>"
            f"{demo}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Self-assigned study plans</h3>"
                "<p>Study plans temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "selfassign-plan",
        "kind": "feature",
        "title": "Self-assigned study plans",
        "blurb": ("Pick your repo scope, concept set, and due date -- "
                  "completion tracked from your own owned proofs, never "
                  "ranked."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
