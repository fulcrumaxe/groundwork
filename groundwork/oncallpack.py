"""On-call prep packs (F-185): service-scoped weakest-first recap.

"Explain this service" prep for the on-call rotation: the Due page
gains ``?service=<repo-substring>`` (Batch-27 ramppack precedent),
and the pack recaps that service's shakiest concepts weakest-first
from live mastery. Ordering mirrors interviewprep -- lowest mastery
first, stalest due date breaks ties, concept id breaks the rest --
over the in-service pool only. A service is a case-insensitive
substring of ``modules.repo``; concepts whose module has no recorded
repo cannot prove membership and stay out. Unscoped, unknown-service,
and empty-pool inputs render "" so legacy bytes survive and the
global recap track remains (decision 282). Picking and rendering are
pure functions of passed-in dicts; one lazy repo lookup follows the
ramppack ``_all_files`` pattern. Stdlib only (``html``) plus that
lazy sibling read; no DB/schema changes. Caller: Handler.due_html
beside the serendipity/preptrack join. Never raises; never mutates
inputs.
"""
from __future__ import annotations

import html

from . import whysee as whyseemod

STATUS_ANCHOR = "status-b29-oncallpack"
SECTION_ANCHOR = "oncallpack"
DEFAULT_SIZE = 5
MAX_SIZE = 12
_MISSING_DUE = "\uffff"


def normalize_service(raw) -> str:
    """Canonical service needle; "" when missing/hostile."""
    try:
        if not isinstance(raw, str):
            return ""
        return raw.strip()
    except Exception:  # noqa: BLE001 -- normalize never raises
        return ""


def match_service(service, repo) -> bool:
    """True when the repo contains the service substring.

    Case-insensitive; an empty service never matches, so the pack
    only renders when the page is actually scoped.
    """
    try:
        s = normalize_service(service)
        if not s or not isinstance(repo, str) or not repo:
            return False
        return s.lower() in repo.lower()
    except Exception:  # noqa: BLE001 -- match never raises
        return False


def repos_for(db_path) -> dict:
    """{module_id: repo} for every module; {} on error. Never raises."""
    try:
        from . import db as dbmod
        if not isinstance(db_path, str) or not db_path:
            return {}
        con = dbmod.connect(db_path)
        try:
            rows = con.execute("SELECT id, repo FROM modules").fetchall()
        finally:
            con.close()
        return {r["id"]: r["repo"] or "" for r in rows}
    except Exception:  # noqa: BLE001 -- lookup never raises
        return {}


def _mastery(row) -> float:
    try:
        m = float((row or {}).get("mastery") or 0.0)
        return m if m == m else 0.0  # NaN is weakest, never crashes sort
    except (TypeError, ValueError):
        return 0.0


def _earliest_due(due) -> dict:
    """concept_id -> earliest due iso; hostile cards skipped."""
    out: dict = {}
    try:
        cards = list(due or [])
    except TypeError:
        return {}
    for c in cards:
        if not isinstance(c, dict):
            continue
        cid = c.get("concept_id")
        cid = str(cid).strip() if cid is not None else ""
        d = c.get("due")
        d = d if isinstance(d, str) and d else ""
        if cid and d and d < out.get(cid, _MISSING_DUE):
            out[cid] = d
    return out


def _size_of(size) -> int:
    try:
        return max(0, min(int(size), MAX_SIZE))
    except (TypeError, ValueError):
        return DEFAULT_SIZE


def pick_pack(concepts, due=None, service="", repos_by_module=None,
              size=DEFAULT_SIZE) -> list:
    """Up to `size` in-service concept dicts, weakest mastery first.

    Each pick: {concept_id, name, module_id, mastery, due, reason}.
    Empty or unknown service yields [] (the global recap track
    remains); concepts outside the service or without a repo stay
    out. Empty or hostile input yields []. Never raises; never
    mutates inputs.
    """
    try:
        s = normalize_service(service)
        if not s:
            return []
        repos = repos_by_module if isinstance(repos_by_module, dict) else {}
        if not any(match_service(s, r) for r in repos.values()):
            return []
        want = _size_of(size)
        edue = _earliest_due(due)
        seen: set = set()
        pool = []
        for r in (concepts or []):
            if not isinstance(r, dict):
                continue
            cid = r.get("id", r.get("concept_id"))
            cid = str(cid).strip() if cid is not None else ""
            if not cid or cid in seen:
                continue
            mid = str(r.get("module_id") or "")
            if not match_service(s, repos.get(mid, "")):
                continue
            seen.add(cid)
            m = _mastery(r)
            d = edue.get(cid, "")
            pool.append((m, d or _MISSING_DUE, cid, r))
        pool.sort(key=lambda t: (t[0], t[1], t[2]))
        out = []
        for m, _, cid, r in pool[:want]:
            name = r.get("name") or cid
            d = edue.get(cid, "")
            reason = f"mastery {m:.2f}" + (f" \u00b7 due {d[:10]}" if d else "")
            out.append({"concept_id": cid, "name": str(name),
                        "module_id": str(r.get("module_id") or ""),
                        "mastery": m, "due": d, "reason": reason})
        return out
    except Exception:  # noqa: BLE001 -- picker never raises
        return []


def pack_html(concepts, due=None, service="", repos_by_module=None,
              size=DEFAULT_SIZE) -> str:
    """Pure scoped-pack renderer over passed-in dicts.

    "" unless the page is scoped to a known service with picks
    (legacy fallback). Never raises.
    """
    try:
        picks = pick_pack(concepts, due, service, repos_by_module, size)
        if not picks:
            return ""
        from . import lessons as lesmod
        lis = []
        for p in picks:
            mid, name = p["module_id"], p["name"]
            href = (f"/modules/{mid}#lesson-{lesmod.slug(name)}"
                    if mid else "/modules")
            why = whyseemod.reason_html(whyseemod.reason_for(
                "preptrack", {"mastery": p["mastery"], "due": p["due"]}))
            lis.append(
                f"<li>{html.escape(name)} "
                f"<small>{html.escape(p['reason'])}</small> {why} \u2014 "
                f"<a href='{html.escape(href, True)}'>Study</a></li>")
        n = len(picks)
        label = html.escape(normalize_service(service))
        return (
            f"<section id='{SECTION_ANCHOR}'><h2>On-call prep: {label}</h2>"
            f"<p>{n} shakiest idea{'s' if n != 1 else ''} in this service \u2014 "
            f"recap before the rotation. <a href='/due'>Clear service</a></p>"
            f"<ol>{''.join(lis)}</ol></section>")
    except Exception:  # noqa: BLE001 -- box never breaks Due
        return ""


def prep_html(db_path, service="", concepts=None, due=None,
              size=DEFAULT_SIZE) -> str:
    """Due-page on-call prep box; "" on the legacy no-param path."""
    try:
        if not normalize_service(service):
            return ""
        return pack_html(concepts, due, service, repos_for(db_path), size)
    except Exception:  # noqa: BLE001 -- box never breaks Due
        return ""


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "oncall-prep-pack",
        "kind": "feature",
        "title": "On-call prep packs",
        "blurb": ("Explain this service before the rotation: the shakiest "
                  "ideas in one service first, with study links."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch29.py."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>On-call prep packs "
        "<small>(feature)</small></h3>"
        "<p>Weakest mastery first within one service, stalest due date "
        "breaks ties -- a capped recap with study links beside the Due "
        "queue via <code>?service=&lt;repo-substring&gt;</code>. "
        "<code>groundwork/oncallpack.py</code> provides "
        "<code>pick_pack()</code>, <code>pack_html()</code> and "
        "<code>prep_html()</code> (unscoped or unknown service renders "
        "nothing, legacy bytes survive).</p>")
