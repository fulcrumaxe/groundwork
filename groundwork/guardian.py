"""Guardian view for kids mode (F-170): progress, no surveillance.

`?guardian=1` on the History page swaps the full per-attempt listing
for an aggregate-only summary: project totals, due counts, tries and
passes, owned ideas, and a last-7-day effort band. Per-answer rows,
per-card grades, concept names, and timestamps never render under the
flag, so a parent sees big-picture progress with nothing to surveil.
No identity layer, no profiles, no schema change: the flag only picks
which renderer history_html calls over the same single-learner tables.
Without the flag history_html runs untouched, so legacy pages keep
byte-identical HTML. Caller: history.history_html (entry guard).
Never raises.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import db as dbmod
from . import ownership as ownmod

STATUS_ANCHOR = "status-b28-guardian"
VIEW_ANCHOR = "guardian-view"


def is_guardian(query) -> bool:
    """True only when the parsed query carries guardian=1; never raises.

    Accepts the parse_qs dict history_html already receives (values
    are lists), a bare "1" string, or True; everything else is False.
    """
    try:
        if isinstance(query, dict):
            vals = query.get("guardian", [])
            if isinstance(vals, str):
                vals = [vals]
            for v in vals or []:
                if v is True or str(v).strip() == "1":
                    return True
            return False
        if isinstance(query, str):
            return query.strip() == "1"
        return query is True
    except Exception:  # noqa: BLE001 -- gate must never raise
        return False


def effort_band(tries7) -> str:
    """Last-7-day effort word from a try count; never raises."""
    try:
        n = int(tries7 or 0)
    except Exception:  # noqa: BLE001 -- band must never raise
        return "resting"
    if n <= 0:
        return "resting"
    if n < 5:
        return "light"
    if n < 15:
        return "steady"
    return "strong"


def _counts(db_path: str) -> tuple:
    """Aggregate-only (mods, due, tries, passed, owned, ideas, t7, d7).

    COUNT queries plus the shared owned_map rule; no per-card,
    per-concept, or timestamp rows ever leave the database. Zeros
    on any error.
    """
    try:
        if not db_path:
            return (0, 0, 0, 0, 0, 0, 0, 0)
        now = datetime.now(timezone.utc)
        now_s = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        week_s = (now - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
        con = dbmod.connect(db_path)
        try:
            mods = con.execute("SELECT COUNT(*) FROM modules").fetchone()[0]
            due = con.execute(
                "SELECT COUNT(*) FROM cards WHERE due <= ? AND stale = 0",
                (now_s,)).fetchone()[0]
            row = con.execute(
                "SELECT COUNT(*), COALESCE(SUM(CASE WHEN grade >= 4 "
                "THEN 1 ELSE 0 END), 0) FROM reviews").fetchone()
            wk = con.execute(
                "SELECT COUNT(*), COUNT(DISTINCT substr(reviewed_at, 1, 10))"
                " FROM reviews WHERE reviewed_at >= ?",
                (week_s,)).fetchone()
            owned = 0
            ideas = 0
            for (mid,) in con.execute("SELECT id FROM modules").fetchall():
                omap = ownmod.owned_map(con, mid)
                ideas += len(omap)
                owned += sum(1 for _, o in omap.values() if o)
            return (mods or 0, due or 0, row[0] or 0, row[1] or 0,
                    owned, ideas, wk[0] or 0, wk[1] or 0)
        finally:
            con.close()
    except Exception:  # noqa: BLE001 -- counts must never raise
        return (0, 0, 0, 0, 0, 0, 0, 0)


def view_html(db_path: str = "") -> str:
    """Aggregate-only guardian body; per-answer detail unbuilt, not hidden."""
    try:
        mods, due, tries, passed, owned, ideas, t7, d7 = _counts(db_path)
        return (
            f"<section id='{VIEW_ANCHOR}'><h2>Guardian view</h2>"
            f"<p>{mods} projects | {due} cards due | {tries} tries | "
            f"{passed} passed.</p>"
            f"<p>{owned} of {ideas} ideas owned.</p>"
            f"<p>Last 7 days: {t7} tries across {d7} active days "
            f"({effort_band(t7)} week).</p>"
            "<p><small>Big-picture counts only: no answers, no per-card "
            "scores, no names of missed ideas. "
            "<a href='/reviews'>Back to History</a>.</small></p>"
            "</section>")
    except Exception:  # noqa: BLE001 -- view must never raise
        return ""


def tour_entry() -> dict:
    """Tour registry entry for the guardian view."""
    return {"id": "guardian-view", "kind": "feature",
            "title": "Guardian view",
            "blurb": ("Big-picture progress for parents: add ?guardian=1 "
                      "on History for totals only, never per-answer detail."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection describing the guardian flag."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Guardian view <small>(feature)</small></h3>"
            "<p>Add <code>?guardian=1</code> on the History page for a "
            "parent-safe summary: project totals, tries and passes, owned "
            "ideas, and a last-7-day effort band (resting, light, steady, "
            "strong). <code>groundwork/guardian.py</code> guards "
            "<code>history.history_html</code> at entry, so per-answer rows "
            "are never built under the flag; without it the page renders "
            "byte-identical.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Guardian view</h3>"
                "<p>Guardian help temporarily unavailable.</p>")
