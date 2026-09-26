"""Team challenges: own a subsystem together, aggregate only (F-129).

Each repo is one fixed local challenge ("own <repo> together"),
computed from existing owned/mastery data. Aggregate counts only —
no members, no ranking, no network, no new tables. Pure reads over
modules/concepts/reviews; never raises. Empty history omits the
section ("" keeps legacy bytes).
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b25-teamchallenge"


def progress(owned: int, total: int) -> int:
    """Aggregate pct 0..100; pure; zero-total is 0, never div-zero."""
    try:
        o, t = int(owned or 0), int(total or 0)
    except (TypeError, ValueError):
        return 0
    if t <= 0 or o <= 0:
        return 0
    return max(0, min(100, round(100 * o / t)))


def challenges(db_path: str) -> list:
    """Per-repo aggregates: [{subsystem, owned, total, attempts, pct, done}]."""
    try:
        from . import db as dbmod
        from . import ownership as ownmod
        con = dbmod.connect(db_path)
        try:
            mods = con.execute(
                "SELECT id, repo FROM modules").fetchall()
            by_repo: dict = {}
            for m in mods:
                mid = str(m["id"])
                repo = str(m["repo"] or "shelf")
                omap = ownmod.owned_map(con, mid)
                tries = con.execute(
                    "SELECT COUNT(*) FROM reviews JOIN cards"
                    " ON cards.id = reviews.card_id JOIN concepts"
                    " ON concepts.id = cards.concept_id"
                    " WHERE concepts.module_id=?", (mid,)).fetchone()[0]
                agg = by_repo.setdefault(
                    repo, {"owned": 0, "total": 0, "attempts": 0})
                agg["owned"] += sum(1 for _, o in omap.values() if o)
                agg["total"] += len(omap)
                agg["attempts"] += tries or 0
        finally:
            con.close()
        out = [{"subsystem": r, "owned": a["owned"], "total": a["total"],
                "attempts": a["attempts"],
                "pct": progress(a["owned"], a["total"]),
                "done": bool(a["total"]) and a["owned"] >= a["total"]}
               for r, a in by_repo.items() if a["total"]]
        return sorted(out, key=lambda c: c["subsystem"])
    except Exception:  # noqa: BLE001 -- proof sections never raise
        return []


def section_html(db_path: str) -> str:
    """Challenge list; "" when no data so the caller keeps legacy bytes."""
    try:
        rows = challenges(db_path)
        if not rows:
            return ""
        items = "".join(
            f"<li><b>{html.escape(c['subsystem'])}</b> — "
            f"{c['owned']}/{c['total']} owned ({c['pct']}%, "
            f"{c['attempts']} attempts)"
            f"{' — <b>Complete</b>' if c['done'] else ''}</li>"
            for c in rows)
        return (f"<h2 id='teamchallenge'>Team challenges</h2>"
                f"<p><small>Own each subsystem together — "
                f"aggregate progress only, no ranking.</small></p>"
                f"<ul>{items}</ul>")
    except Exception:  # noqa: BLE001 -- history never breaks
        return ""


def status_section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Team challenges "
            "<small>(feature)</small></h3>"
            "<p>Own a subsystem together, aggregate only — "
            "<code>groundwork/teamchallenge.py</code> groups owned/total "
            "per repo from the existing tables (no members, no ranking) "
            "on the History page.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Team challenges</h3>"
                "<p>Challenge help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour registry entry for team challenges."""
    return {"id": "team-challenges", "kind": "feature",
            "title": "Team challenges",
            "blurb": ("Own each subsystem together — aggregate "
                      "progress, no ranking."),
            "path": "/reviews", "anchor": "teamchallenge"}
