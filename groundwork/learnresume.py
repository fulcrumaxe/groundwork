"""Learning resume: verified skills per repo, portable (F-109).

One table per repo: every Bloom skill the learner has proven, the
concepts proving it, and whether the proof survived delay (a pass at
21+ days stability, the north-star maturity bar). Only owned
concepts verify a skill — attempts alone never appear. Pure
computation over the existing tables (prev_stability rides on the
reviews rows Batch 15 added); no schema change, no new storage.
Portable means self-contained: one div with plain tables that print
cleanly, no scripts, no page chrome required.

Caller path (History page, never a Status demo):
``history.history_html`` appends ``section_html`` in both branches.
The section always renders (anchor-stable for the tour); empty
libraries get a resume-to-build line. Never raises.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import exercises as exmod
from . import milestones as momentsmod

STATUS_ANCHOR = "status-b22-learnresume"

#: Stability at review time that counts as delayed proof (north-star bar).
MATURE_DAYS = 21.0


def _bloom_of(etype) -> str:
    try:
        return exmod.TYPES[int(etype)][1]
    except (ValueError, KeyError, TypeError):
        return "other"


def skills(db_path: str) -> dict:
    """{repo: [{skill, concepts, delayed, first}]} verified skills.

    A skill verifies per repo when at least one owned concept has a
    passing review of that Bloom tier; delayed is True when any such
    pass came at mature stability. Empty/hostile DB yields {};
    never raises.
    """
    try:
        owned = set(momentsmod.owned_dates(db_path))
        if not owned:
            return {}
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT concepts.id AS cid, concepts.name AS name,"
                " modules.repo AS repo, cards.exercise_type AS etype,"
                " reviews.reviewed_at AS wh,"
                " reviews.prev_stability AS stab FROM reviews"
                " JOIN cards ON cards.id = reviews.card_id"
                " JOIN concepts ON concepts.id = cards.concept_id"
                " JOIN modules ON modules.id = concepts.module_id"
                " WHERE reviews.grade >= 4").fetchall()
        finally:
            con.close()
    except Exception:  # noqa: BLE001 -- stats never raise
        return {}
    try:
        table: dict[tuple, dict] = {}
        for r in rows:
            cid = str(r["cid"] or "")
            if cid not in owned:
                continue
            key = (str(r["repo"] or "shelf"), _bloom_of(r["etype"]))
            cell = table.setdefault(key, {"concepts": set(), "delayed": False,
                                          "first": None})
            if r["name"]:
                cell["concepts"].add(str(r["name"]))
            try:
                if float(r["stab"] or 0) >= MATURE_DAYS:
                    cell["delayed"] = True
            except (TypeError, ValueError):
                pass
            when = str(r["wh"] or "")
            if when and (cell["first"] is None or when < cell["first"]):
                cell["first"] = when
        out: dict[str, list] = {}
        for (repo, skill), cell in sorted(table.items()):
            out.setdefault(repo, []).append({
                "skill": skill,
                "concepts": sorted(cell["concepts"]),
                "delayed": cell["delayed"],
                "first": (cell["first"] or "")[:10],
            })
        return out
    except Exception:  # noqa: BLE001 -- grouping never raises
        return {}


def section_html(db_path: str) -> str:
    """Always-rendered History section; the anchor never moves."""
    try:
        table = skills(db_path)
        if not table:
            body = ("<p>No verified skills yet — own a concept and it "
                    "writes its own reference.</p>")
        else:
            parts = []
            for repo in table:
                rows = "".join(
                    f"<tr><td>{html.escape(s['skill'])}</td>"
                    f"<td>{html.escape(', '.join(s['concepts']))}</td>"
                    f"<td>{'delayed-proof' if s['delayed'] else 'fresh'}</td>"
                    f"<td>{html.escape(s['first'])}</td></tr>"
                    for s in table[repo])
                parts.append(
                    f"<h3>{html.escape(repo)}</h3>"
                    "<table class='log'><tr><th>Skill</th><th>Proven by</th>"
                    "<th>Held up?</th><th>Since</th></tr>"
                    f"{rows}</table>")
            body = ("<div class='resume'>" + "".join(parts) + "</div>")
        return f"<h2 id='learning-resume'>Learning resume</h2>{body}"
    except Exception:  # noqa: BLE001 -- history never breaks
        return ("<h2 id='learning-resume'>Learning resume</h2>"
                "<p>Resume temporarily unavailable.</p>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Learning resume "
            "<small>(feature)</small></h3>"
            "<p>Verified skills per repo — "
            "<code>groundwork/learnresume.py</code> lists only owned "
            "concepts as proof, flags delayed (21+ day stability) holds, "
            "and renders printable tables on the History page. Attempts "
            "alone never verify.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Learning resume</h3>"
                "<p>Resume help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "learning-resume",
        "kind": "feature",
        "title": "Learning resume",
        "blurb": ("Your verified skills per repo — references written "
                  "by your own proof."),
        "path": "/reviews",
        "anchor": "learning-resume",
    }
