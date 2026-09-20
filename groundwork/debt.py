"""Comprehension debt page plus Bloom ladder fragments.

Debt = what changed vs what the learner can prove they own. The ladder
fragments are shared with the module page; both live here so web.py
stays routing and assembly.
"""
from __future__ import annotations

import html

from . import db as dbmod
from . import exercises as exmod
from . import ownership as ownmod

BLOOM_RUNGS = ["recall", "explain", "apply", "analyse", "modify", "create"]


def bloom_reached(con, mid: str) -> dict:
    """Highest Bloom rung with a passing review, per concept in a module."""
    rung_of = {}
    for t, (_name, bloom) in exmod.TYPES.items():
        rung_of[str(t)] = BLOOM_RUNGS.index(bloom) if bloom in BLOOM_RUNGS else -1
    out: dict[str, int] = {}
    try:
        rows = con.execute(
            "SELECT cards.concept_id, cards.exercise_type FROM reviews"
            " JOIN cards ON cards.id = reviews.card_id"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " WHERE concepts.module_id=? AND reviews.grade >= 4",
            (mid,)).fetchall()
    except Exception:  # noqa: BLE001 — no reviews yet still renders
        return out
    for r in rows:
        rung = rung_of.get(str(r["exercise_type"]), -1)
        if rung >= 0:
            out[r["concept_id"]] = max(out.get(r["concept_id"], -1), rung)
    return out


def ladder_html(reached: int, extra: str = "") -> str:
    """Six ascending rungs; lit rungs mark demonstrated skill tiers."""
    bars = []
    for i, bloom in enumerate(BLOOM_RUNGS):
        cls = "on" if i <= reached else "off"
        bars.append(f"<i class='{cls}' style='height:{4 + 2 * i}px' "
                    f"title='{bloom}'></i>")
    return (f"<span class='ladder'{extra} title='Highest demonstrated: "
            f"{BLOOM_RUNGS[reached] if reached >= 0 else 'none yet'}'>"
            + "".join(bars) + "</span>")


def debt_html(db_path: str) -> str:
    """Comprehension debt: what changed vs what you can prove you own."""
    con = dbmod.connect(db_path)
    try:
        mods = con.execute(
            "SELECT id, repo, task_summary FROM modules"
            " ORDER BY created_at DESC").fetchall()
        per_repo: dict[str, dict[str, list]] = {}
        for m in mods:
            omap = ownmod.owned_map(con, m["id"])
            rows = con.execute(
                "SELECT id, file FROM concepts WHERE module_id=?",
                (m["id"],)).fetchall()
            bucket = per_repo.setdefault(m["repo"] or "(unknown repo)", {})
            for r in rows:
                cell = bucket.setdefault(r["file"] or "(unknown)", [0, 0])
                cell[1] += 1
                if omap.get(r["id"], (0, False))[1]:
                    cell[0] += 1
    finally:
        con.close()
    if not per_repo:
        return ("<p>No modules yet — debt is zero because nothing "
                "has changed.</p>")
    total_o = sum(c[0] for b in per_repo.values() for c in b.values())
    total_n = sum(c[1] for b in per_repo.values() for c in b.values())
    debt = 0 if not total_n else int(round(100 * (1 - total_o / total_n)))
    parts = [f"<div class='bar' id='debt-meter' role='img' aria-label='{debt}% "
               f"comprehension debt'><i style='width:{debt}%'></i></div>"
               f"<p><strong>{debt}% comprehension debt</strong> "
               f"({total_o}/{total_n} concepts owned)</p>"]
    for repo in sorted(per_repo):
        parts.append(f"<h2>{html.escape(repo)}</h2>")
        files = sorted(per_repo[repo].items(),
                       key=lambda kv: (kv[1][0] / kv[1][1] if kv[1][1] else 1))
        cells = "".join(
            f"<tr><td>{html.escape(f)}</td><td>{o}/{n}</td>"
            f"<td>{int(round(100 * (1 - o / n))) if n else 0}%</td></tr>"
            for f, (o, n) in files)
        parts.append("<table class='log'><tr><th>File</th><th>Owned</th>"
                     "<th>Debt</th></tr>" + cells + "</table>")
    return "".join(parts)
