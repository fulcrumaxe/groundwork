"""Interview loop: study plan plus proof-of-understanding report (F-161).

A candidate ramping for an interview loop needs two things: what to
study next, and proof of what they already understand. This module
builds both from the learner's OWN data -- the scoped repo's modules
ordered weakest-owned first (the plan), and per-module owned counts,
attempts, interview/transfer passes, and owned dates (the proof).
Honestly scoped: your own attempts only -- no interviewer role, no
external verification.

Caller: ``history.history_html`` lead block. Empty histories render
an anchor-stable "No interview loop yet" line. Stdlib only
(``html``) plus lazy sibling reads (``db``, ``ownership``,
``milestones``); never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b27-interviewloop"
BOX_ANCHOR = "interview-loop"
PLAN_CAP = 12


def scope_repo(db_path) -> str:
    """The loop's repo: most-reviewed; ties by modules then name."""
    try:
        from . import db as dbmod
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT modules.repo AS repo, COUNT(reviews.id) AS n,"
                " COUNT(DISTINCT modules.id) AS m"
                " FROM modules LEFT JOIN concepts"
                " ON concepts.module_id = modules.id"
                " LEFT JOIN cards ON cards.concept_id = concepts.id"
                " LEFT JOIN reviews ON reviews.card_id = cards.id"
                " GROUP BY modules.repo").fetchall()
        finally:
            con.close()
        scored = [((r["n"] or 0, r["m"] or 0, str(r["repo"] or ""))
                   for r in rows if r["repo"])]
        if not scored:
            return ""
        scored.sort(key=lambda t: (-t[0], -t[1], t[2]))
        best = scored[0]
        if best[0] == 0:
            # No reviews anywhere: most-studied repo is meaningless;
            # still return the deterministic top repo so the plan shows.
            pass
        return best[2]
    except Exception:  # noqa: BLE001
        return ""


def _modules_of(db_path, repo):
    """[(mid, summary)] for the repo (all modules when repo is "")."""
    from . import db as dbmod
    con = dbmod.connect(db_path)
    try:
        if repo:
            rows = con.execute(
                "SELECT id, task_summary FROM modules WHERE repo=?"
                " ORDER BY created_at DESC", (repo,)).fetchall()
        else:
            rows = con.execute(
                "SELECT id, task_summary FROM modules"
                " ORDER BY created_at DESC").fetchall()
        return [(r["id"], r["task_summary"] or r["id"]) for r in rows]
    finally:
        con.close()


def plan_for(db_path, repo=None, size=6) -> dict:
    """Weakest-owned-first study plan for the scoped repo."""
    try:
        from . import db as dbmod
        from . import ownership as ownmod
        if repo is None:
            repo = scope_repo(db_path)
        try:
            n = int(size)
        except (TypeError, ValueError):
            n = 6
        n = max(0, min(PLAN_CAP, n))
        con = dbmod.connect(db_path)
        try:
            mods = _modules_of(db_path, repo)
            steps = []
            for mid, summary in mods:
                omap = ownmod.owned_map(con, mid)
                total = len(omap)
                owned_n = sum(1 for _, o in omap.values() if o)
                attempts = con.execute(
                    "SELECT COUNT(*) FROM reviews JOIN cards"
                    " ON cards.id = reviews.card_id JOIN concepts"
                    " ON concepts.id = cards.concept_id"
                    " WHERE concepts.module_id=?", (mid,)).fetchone()[0]
                coverage = (owned_n / total) if total else 0.0
                reason = ("weakest coverage -- start here" if coverage < 1.0
                          else "fully owned -- maintain")
                steps.append({"module_id": mid, "summary": summary,
                              "owned": owned_n, "total": total,
                              "coverage": coverage, "attempts": attempts,
                              "reason": reason,
                              "href": f"/modules/{mid}"})
        finally:
            con.close()
        steps.sort(key=lambda s: (s["coverage"], s["attempts"],
                                  s["module_id"]))
        return {"repo": repo, "steps": steps[:n]}
    except Exception:  # noqa: BLE001
        return {"repo": repo or "", "steps": []}


def proof_for(db_path, repo=None) -> dict:
    """Proof-of-understanding from the learner's own attempts."""
    try:
        from . import db as dbmod
        from . import milestones as milesmod
        from . import ownership as ownmod
        if repo is None:
            repo = scope_repo(db_path)
        dates = milesmod.owned_dates(db_path)
        con = dbmod.connect(db_path)
        try:
            mods = _modules_of(db_path, repo)
            rows = []
            for mid, summary in mods:
                omap = ownmod.owned_map(con, mid)
                total = len(omap)
                owned_n = sum(1 for _, o in omap.values() if o)
                agg = con.execute(
                    "SELECT COUNT(*) AS n,"
                    " SUM(CASE WHEN reviews.grade >= 4 THEN 1 ELSE 0 END)"
                    " AS ok FROM reviews JOIN cards"
                    " ON cards.id = reviews.card_id JOIN concepts"
                    " ON concepts.id = cards.concept_id"
                    " WHERE concepts.module_id=?", (mid,)).fetchone()
                interviews = con.execute(
                    "SELECT COUNT(*) FROM reviews JOIN cards"
                    " ON cards.id = reviews.card_id JOIN concepts"
                    " ON concepts.id = cards.concept_id"
                    " WHERE concepts.module_id=?"
                    " AND cards.exercise_type='73' AND reviews.grade >= 4",
                    (mid,)).fetchone()[0]
                transfers = con.execute(
                    "SELECT COUNT(*) FROM reviews JOIN cards"
                    " ON cards.id = reviews.card_id JOIN concepts"
                    " ON concepts.id = cards.concept_id"
                    " WHERE concepts.module_id=?"
                    " AND cards.exercise_type IN ('74','75')"
                    " AND reviews.grade >= 4", (mid,)).fetchone()[0]
                cids = [c for c in omap]
                owned_when = sorted(dates[c] for c in cids if c in dates)
                rows.append({"module_id": mid, "summary": summary,
                             "owned": owned_n, "total": total,
                             "attempts": agg["n"] or 0,
                             "passes": agg["ok"] or 0,
                             "interviews": interviews or 0,
                             "transfers": transfers or 0,
                             "first_owned": owned_when[0] if owned_when else "",
                             "last_owned": owned_when[-1] if owned_when else ""})
        finally:
            con.close()
        totals = {"owned": sum(r["owned"] for r in rows),
                  "total": sum(r["total"] for r in rows),
                  "attempts": sum(r["attempts"] for r in rows),
                  "passes": sum(r["passes"] for r in rows),
                  "interviews": sum(r["interviews"] for r in rows),
                  "transfers": sum(r["transfers"] for r in rows)}
        return {"repo": repo, "rows": rows, "totals": totals}
    except Exception:  # noqa: BLE001
        return {"repo": repo or "", "rows": [], "totals": {}}


def loop_html(db_path, repo=None) -> str:
    """Plan plus proof report; anchor-stable line when empty."""
    try:
        plan = plan_for(db_path, repo)
        proof = proof_for(db_path, plan["repo"])
        if not plan["steps"]:
            return (f"<section id='{BOX_ANCHOR}'><h2>Interview loop</h2>"
                    "<p>No interview loop yet -- study a module first.</p>"
                    "</section>")
        ol = "".join(
            f"<li><a href='{html.escape(s['href'], quote=True)}'>"
            f"{html.escape(s['summary'])}</a> "
            f"<small>{s['owned']}/{s['total']} owned -- "
            f"{html.escape(s['reason'])}</small></li>"
            for s in plan["steps"])
        trs = "".join(
            f"<tr><td><a href='/modules/{html.escape(r['module_id'], quote=True)}'>"
            f"{html.escape(r['summary'])}</a></td>"
            f"<td>{r['owned']}/{r['total']}</td>"
            f"<td>{r['attempts']}</td><td>{r['passes']}</td>"
            f"<td>{r['interviews']}</td><td>{r['transfers']}</td>"
            f"<td>{html.escape(r['first_owned'])}</td>"
            f"<td>{html.escape(r['last_owned'])}</td></tr>"
            for r in proof["rows"])
        t = proof["totals"]
        scope = (f"Loop repo: <b>{html.escape(plan['repo'])}</b> -- "
                 if plan["repo"] else "")
        return (
            f"<section id='{BOX_ANCHOR}'><h2>Interview loop</h2>"
            f"<p><small>{scope}your own attempts only -- no "
            "interviewer, no external verification.</small></p>"
            f"<h3>Study plan</h3><ol>{ol}</ol>"
            "<h3>Proof of understanding</h3>"
            "<table class='log'><tr><th>Module</th><th>Owned</th>"
            "<th>Attempts</th><th>Passes</th><th>Interviews</th>"
            "<th>Transfers</th><th>First owned</th><th>Last owned</th>"
            f"</tr>{trs}</table>"
            f"<p><small>Totals: {t['owned']}/{t['total']} owned, "
            f"{t['attempts']} attempts, {t['passes']} passes, "
            f"{t['interviews']} interviews, {t['transfers']} transfers."
            "</small></p></section>")
    except Exception:  # noqa: BLE001 -- History bytes always survive
        return (f"<section id='{BOX_ANCHOR}'><h2>Interview loop</h2>"
                "<p>No interview loop yet.</p></section>")


def section_html() -> str:
    """Anchored status subsection; joined by the batch27 home module."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Interview loop "
        "<small>(feature)</small></h3>"
        "<p>Interview loop (feature): repo-scoped study plan "
        "weakest-first plus a proof-of-understanding report from your "
        "own attempts -- <code>groundwork/interviewloop.py</code>, "
        "rendered on History beside certificates.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "interview-loop",
        "kind": "feature",
        "title": "Interview loop",
        "blurb": ("A study plan from your weakest modules plus a proof "
                  "report from your own attempts -- interview-ready, "
                  "honestly scoped."),
        "path": "/reviews",
        "anchor": BOX_ANCHOR,
    }
