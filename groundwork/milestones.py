"""Milestone moments: first Owned, 10th module, full repo coverage (F-107).

Calm, streak-free milestones computed from the existing tables —
no new storage, no schema change. First Owned is the earliest date
any concept satisfied the owned rule (passing modify/create review
plus a return visit); the 10th module is the date a tenth distinct
module earned its first review; full repo coverage is per repo, dated
when its last module earned its first owned concept. Achieved
milestones render oldest-first with dates; the rest stay unwritten
rather than greyed-out. Pure functions, stdlib only.

Caller path (History page, never a Status demo):
``history.history_html`` appends ``section_html`` in both branches.
The section always renders (anchor-stable for the tour). Never raises.
"""
from __future__ import annotations

from . import db as dbmod
from . import ownership as ownmod
from . import timetag as timetagmod

STATUS_ANCHOR = "status-b22-milestones"

TENTH_MODULE_N = 10


def _pass_rows(db_path: str) -> list:
    """(concept_id, module_id, reviewed_at) passing modify/create reviews."""
    try:
        types = ownmod.ownership_types()
        con = dbmod.connect(db_path)
        try:
            if types:
                placeholders = ",".join("?" * len(types))
                filt = (f"AND cards.exercise_type IN ({placeholders})")
                args: list = list(types)
            else:
                filt, args = "", []
            rows = con.execute(
                "SELECT cards.concept_id AS cid,"
                " concepts.module_id AS mid, reviews.reviewed_at AS wh"
                " FROM reviews JOIN cards ON cards.id = reviews.card_id"
                " JOIN concepts ON concepts.id = cards.concept_id"
                f" WHERE reviews.grade >= 4 {filt}"
                " ORDER BY reviews.reviewed_at", args).fetchall()
        finally:
            con.close()
        return [(r["cid"], r["mid"], str(r["wh"] or "")) for r in rows]
    except Exception:  # noqa: BLE001 -- stats never raise
        return []


def owned_dates(db_path: str) -> dict:
    """{concept_id: first-owned date}; the 2nd passing review dates it."""
    try:
        seen: dict[str, list] = {}
        for cid, _mid, when in _pass_rows(db_path):
            if when:
                seen.setdefault(str(cid), []).append(when)
        return {cid: whens[1] for cid, whens in seen.items()
                if len(whens) >= 2}
    except Exception:  # noqa: BLE001 -- stats never raise
        return {}


def module_first_dates(db_path: str) -> dict:
    """{module_id: first review date} over practiced modules."""
    try:
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT concepts.module_id AS mid,"
                " MIN(reviews.reviewed_at) AS wh FROM reviews"
                " JOIN cards ON cards.id = reviews.card_id"
                " JOIN concepts ON concepts.id = cards.concept_id"
                " GROUP BY concepts.module_id").fetchall()
        finally:
            con.close()
        return {str(r["mid"]): str(r["wh"] or "") for r in rows
                if r["wh"]}
    except Exception:  # noqa: BLE001 -- stats never raise
        return {}


def moments(db_path: str) -> list:
    """Achieved milestones oldest-first: [{kind, label, when}]."""
    try:
        out = []
        owned = owned_dates(db_path)
        if owned:
            out.append({"kind": "first-owned",
                        "label": "First concept owned",
                        "when": min(owned.values())})
        firsts = module_first_dates(db_path)
        if len(firsts) >= TENTH_MODULE_N:
            tenth = sorted(firsts.values())[TENTH_MODULE_N - 1]
            out.append({"kind": "tenth-module",
                        "label": f"{TENTH_MODULE_N}th module practiced",
                        "when": tenth})
        try:
            con = dbmod.connect(db_path)
            try:
                mods = con.execute(
                    "SELECT id, repo FROM modules").fetchall()
            finally:
                con.close()
            by_repo: dict[str, list] = {}
            for m in mods:
                by_repo.setdefault(str(m["repo"] or "shelf"),
                                   []).append(str(m["id"]))
        except Exception:  # noqa: BLE001 -- repos optional
            by_repo = {}
        mod_owned: dict[str, str] = {}
        # Module owned-date = earliest owned date among its concepts.
        try:
            con = dbmod.connect(db_path)
            try:
                cmap = {str(r["id"]): str(r["module_id"])
                        for r in con.execute(
                            "SELECT id, module_id FROM concepts").fetchall()}
            finally:
                con.close()
        except Exception:  # noqa: BLE001 -- mapping optional
            cmap = {}
        for cid, when in owned.items():
            mid = cmap.get(str(cid))
            if mid and (mid not in mod_owned or when < mod_owned[mid]):
                mod_owned[mid] = when
        for repo in sorted(by_repo):
            mids = by_repo[repo]
            if mids and all(m in mod_owned for m in mids):
                out.append({"kind": "full-repo",
                            "label": f"Full coverage: {repo}",
                            "when": max(mod_owned[m] for m in mids)})
        out.sort(key=lambda m: (m["when"], m["kind"]))
        return out
    except Exception:  # noqa: BLE001 -- milestones never raise
        return []


def section_html(db_path: str) -> str:
    """Always-rendered History section; the anchor never moves."""
    try:
        ms = moments(db_path)
        if not ms:
            body = ("<p>No milestones yet — your first owned concept "
                    "writes the first one.</p>")
        else:
            items = "".join(
                f"<li><b>{_esc(m['label'])}</b> — "
                f"<small>{timetagmod.stamp(m['when'])}</small></li>"
                for m in ms)
            body = f"<ul>{items}</ul>"
        return f"<h2 id='milestones'>Milestone moments</h2>{body}"
    except Exception:  # noqa: BLE001 -- history never breaks
        return ("<h2 id='milestones'>Milestone moments</h2>"
                "<p>Milestones temporarily unavailable.</p>")


def _esc(value) -> str:
    import html
    try:
        return html.escape(str(value or ""), quote=True)
    except Exception:  # noqa: BLE001 -- escaping never raises
        return ""


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Milestone moments "
            "<small>(feature)</small></h3>"
            "<p>First Owned, the 10th practiced module, full repo "
            "coverage — <code>groundwork/milestones.py</code> dates each "
            "from the existing tables (no new storage) and lists only "
            "achieved milestones, oldest-first, on the History page.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Milestone moments</h3>"
                "<p>Milestones help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "milestone-moments",
        "kind": "feature",
        "title": "Milestone moments",
        "blurb": ("First Owned, tenth module, full coverage — the dates "
                  "that mattered."),
        "path": "/reviews",
        "anchor": "milestones",
    }
