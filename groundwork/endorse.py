"""Skill endorsements by your own delayed tests, not peers (F-110).

A Bloom skill earns its endorsement the day a delayed test proves
it: a passing review at 21+ days stability (the north-star maturity
bar), read off the prev_stability the grading pipeline already
stores. No votes, no peers, no new storage — the endorsement list
is pure computation over the existing reviews table. Each entry
names its proof count and latest proof date so one lucky recall
reads as exactly that.

Caller path (History page, never a Status demo):
``history.history_html`` appends ``section_html`` in both branches.
The section always renders (anchor-stable for the tour); fresh
skills get an endorsements-to-earn line. Never raises.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import exercises as exmod

STATUS_ANCHOR = "status-b22-endorse"

#: Stability at review time that counts as a delayed test.
MATURE_DAYS = 21.0


def _bloom_of(etype) -> str:
    try:
        return exmod.TYPES[int(etype)][1]
    except (ValueError, KeyError, TypeError):
        return "other"


def endorsements(db_path: str) -> list:
    """[{skill, proofs, latest}] one row per delayed-proven skill.

    Empty/hostile DB yields []; never raises.
    """
    try:
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT cards.exercise_type AS etype,"
                " reviews.reviewed_at AS wh FROM reviews"
                " JOIN cards ON cards.id = reviews.card_id"
                " WHERE reviews.grade >= 4"
                " AND reviews.prev_stability >= ?"
                " ORDER BY reviews.reviewed_at",
                (MATURE_DAYS,)).fetchall()
        finally:
            con.close()
    except Exception:  # noqa: BLE001 -- stats never raise
        return []
    try:
        table: dict[str, dict] = {}
        for r in rows:
            skill = _bloom_of(r["etype"])
            cell = table.setdefault(skill, {"proofs": 0, "latest": ""})
            cell["proofs"] += 1
            when = str(r["wh"] or "")
            if when > cell["latest"]:
                cell["latest"] = when
        return [{"skill": s, "proofs": c["proofs"],
                 "latest": c["latest"][:10]}
                for s, c in sorted(table.items())]
    except Exception:  # noqa: BLE001 -- grouping never raises
        return []


def section_html(db_path: str) -> str:
    """Always-rendered History section; the anchor never moves."""
    try:
        rows = endorsements(db_path)
        if not rows:
            body = ("<p>No endorsements yet — a skill earns one when a "
                    "delayed test proves it, not before.</p>")
        else:
            items = []
            for r in rows:
                plural = "" if r["proofs"] == 1 else "s"
                latest = ("", f", latest {html.escape(r['latest'])}")[
                    bool(r["latest"])]
                items.append(
                    f"<li><b>Endorsed: {html.escape(r['skill'])}</b> — "
                    f"{r['proofs']} delayed proof{plural}{latest}. "
                    "No peers were consulted.</li>")
            body = f"<ul>{''.join(items)}</ul>"
        return f"<h2 id='endorsements'>Skill endorsements</h2>{body}"
    except Exception:  # noqa: BLE001 -- history never breaks
        return ("<h2 id='endorsements'>Skill endorsements</h2>"
                "<p>Endorsements temporarily unavailable.</p>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Skill endorsements "
            "<small>(feature)</small></h3>"
            "<p>References from your future self — "
            "<code>groundwork/endorse.py</code> endorses a Bloom skill "
            "only on delayed-test proof (21+ day stability passes, "
            "counted with dates) on the History page. Peers are never "
            "consulted.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Skill endorsements</h3>"
                "<p>Endorsements help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "skill-endorsements",
        "kind": "feature",
        "title": "Skill endorsements",
        "blurb": ("Endorsed by your own delayed tests — references from "
                  "your future self."),
        "path": "/reviews",
        "anchor": "endorsements",
    }
