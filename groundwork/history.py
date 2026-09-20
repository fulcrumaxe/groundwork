"""History page: past attempts, calibration, coverage, workload.

Pure renderer over a database path — the web Handler delegates here.
Workload forecast rides in the same page (I-204).
"""
from __future__ import annotations

import html
from datetime import timedelta

from . import cards as cardsmod
from . import db as dbmod
from . import exercises as exmod
from . import monthreview as monthmod
from . import ownership as ownmod
from . import sched as schedmod
from . import workload as workloadmod

COACH_TIPS = {
    "recall": "Say the answer aloud before rating yourself.",
    "explain": "Check your explanation against the study guide sentence by sentence.",
    "apply": "Predict the outcome before you run anything or peek.",
    "analyse": "Point at the exact line before committing to an answer.",
    "modify": "Run the mental test suite before submitting.",
    "evaluate": "Name the flaw precisely before judging.",
    "create": "Compare your version against the spec line by line.",
    "other": "Slow down on the hard ones.",
}


def calibration_coach(rows: list) -> str:
    """Per-skill accuracy-vs-confidence table plus an overconfidence nudge.

    rows: (exercise_type, grade 0-5, confidence 1-5). A skill earns a
    coaching nudge with 3+ attempts and confidence beating accuracy
    by 15+ points — the blind spot in AI-assisted work.
    """
    by_bloom: dict[str, list] = {}
    for etype, grade, conf in rows:
        try:
            bloom = exmod.TYPES[int(etype)][1]
        except (ValueError, KeyError, TypeError):
            bloom = "other"
        by_bloom.setdefault(bloom, []).append((grade, conf))
    if not by_bloom:
        return ""
    cells = []
    worst = None
    for bloom in sorted(by_bloom):
        rs = by_bloom[bloom]
        acc = sum(1 for g, _ in rs if (g or 0) >= 4) / len(rs)
        avg_conf = sum(((c or 3) - 1) / 4 for _, c in rs) / len(rs)
        gap = avg_conf - acc
        cells.append(f"<tr><td>{html.escape(bloom)}</td><td>{acc:.0%}</td>"
                     f"<td>{avg_conf:.0%}</td><td>{gap:+.0%}</td></tr>")
        if len(rs) >= 3 and gap >= 0.15 and (worst is None or gap > worst[1]):
            worst = (bloom, gap, acc, avg_conf)
    parts = ["<h2>Calibration coach</h2>",
             "<table class='log'><tr><th>Skill</th><th>Accuracy</th>"
             "<th>Confidence</th><th>Gap</th></tr>" + "".join(cells) + "</table>"]
    if worst is not None:
        bloom, _, acc, avg_conf = worst
        parts.append(f"<p>Coach: on {html.escape(bloom)} exercises you feel "
                     f"{avg_conf:.0%} confident but score {acc:.0%}. "
                     f"{COACH_TIPS.get(bloom, COACH_TIPS['other'])}</p>")
    return "".join(parts)


def history_html(db_path: str) -> str:
    """Past attempts: grades, confidence, calibration — not a second queue."""
    con = dbmod.connect(db_path)
    try:
        cal = con.execute(
            "SELECT AVG(grade) AS g, AVG(confidence) AS c, COUNT(*) AS n FROM reviews"
        ).fetchone()
        days = con.execute(
            "SELECT substr(reviewed_at, 1, 10) AS d, COUNT(*) AS n,"
            " SUM(CASE WHEN grade >= 4 THEN 1 ELSE 0 END) AS ok"
            " FROM reviews GROUP BY d ORDER BY d DESC LIMIT 14").fetchall()
        week = con.execute(
            "SELECT COUNT(*) AS n,"
            " SUM(CASE WHEN grade >= 4 THEN 1 ELSE 0 END) AS ok,"
            " COUNT(DISTINCT substr(reviewed_at, 1, 10)) AS days"
            " FROM reviews WHERE reviewed_at >= ?",
            ((schedmod.utcnow() - timedelta(days=7)).strftime(
                "%Y-%m-%dT%H:%M:%SZ"),)).fetchone()
        rows = con.execute(
            "SELECT reviews.grade, reviews.confidence, reviews.reviewed_at,"
            " concepts.name AS concept, concepts.module_id AS module_id,"
            " modules.task_summary AS summary"
            " FROM reviews JOIN cards ON cards.id = reviews.card_id"
            " JOIN concepts ON concepts.id = cards.concept_id"
            " JOIN modules ON modules.id = concepts.module_id"
            " ORDER BY reviews.id DESC LIMIT 100").fetchall()
        coach_rows = con.execute(
            "SELECT cards.exercise_type, reviews.grade, reviews.confidence"
            " FROM reviews JOIN cards ON cards.id = reviews.card_id"
            " ORDER BY reviews.id DESC LIMIT 500").fetchall()
        tl_mods = [dict(r) for r in con.execute(
            "SELECT id, task_summary, created_at, repo FROM modules"
            " ORDER BY created_at DESC LIMIT 30").fetchall()]
        tl_stats = {}
        for tm in tl_mods:
            omap = ownmod.owned_map(con, tm["id"])
            cards_n = con.execute(
                "SELECT COUNT(*) FROM cards JOIN concepts"
                " ON concepts.id = cards.concept_id"
                " WHERE concepts.module_id=?",
                (tm["id"],)).fetchone()[0]
            tries_n = con.execute(
                "SELECT COUNT(*) FROM reviews JOIN cards"
                " ON cards.id = reviews.card_id JOIN concepts"
                " ON concepts.id = cards.concept_id"
                " WHERE concepts.module_id=?",
                (tm["id"],)).fetchone()[0]
            tl_stats[tm["id"]] = (cards_n, tries_n, omap)
    finally:
        con.close()
    parts = []
    if cal and cal["n"]:
        acc = (cal["g"] or 0) / 5.0
        conf = ((cal["c"] or 3) - 1) / 4.0
        parts.append(f"<p id='calibration'>Calibration: accuracy {acc:.0%} vs confidence {conf:.0%} "
                     f"(gap {conf - acc:+.0%}, n={cal['n']})</p>")
        parts.append(calibration_coach(
            [(r[0], r[1], r[2]) for r in coach_rows]))
        if tl_mods:
            tl_rows = []
            for tm in tl_mods:
                cards_n, tries_n, omap = tl_stats[tm["id"]]
                owned_n = sum(1 for _, o in omap.values() if o)
                date = (tm["created_at"] or "")[:10]
                tl_rows.append(
                    f"<tr><td>{html.escape(date)}</td>"
                    f"<td><a href='/modules/{tm['id']}'>"
                    f"{html.escape(tm['task_summary'] or tm['id'])}</a>"
                    f"<br><small>{html.escape(tm['repo'] or '')}</small></td>"
                    f"<td>{cards_n}</td><td>{tries_n}</td>"
                    f"<td>{owned_n}/{len(omap)}</td></tr>")
            parts.append("<h2 id='coverage'>Coverage timeline</h2>"
                         "<p><small>Every session, what it made, "
                         "and what stuck.</small></p>"
                         "<table class='log'><tr><th>Date</th><th>Session</th>"
                         "<th>Cards</th><th>Attempts</th><th>Owned</th></tr>"
                         + "".join(tl_rows) + "</table>")
    else:
        parts.append("<p>No attempts yet. Answer a card on the "
                     "<a href='/due'>Due</a> page and it will show up here.</p>")
        parts.append(monthmod.section_html(db_path))
        return "".join(parts)
    if days:
        cells = "".join(
            f"<tr><td>{html.escape(d['d'])}</td><td>{d['n']}</td>"
            f"<td>{d['ok']}</td></tr>" for d in days)
        parts.append("<h2>Last 14 practice days</h2>"
                     f"<table class='log'><tr><th>Day</th><th>Attempts</th>"
                     f"<th>Passed</th></tr>{cells}</table>")
        parts.append(workloadmod.section_html(db_path))
        wn, wok, wdays = week["n"] or 0, week["ok"] or 0, week["days"] or 0
        acc = f"{round(100 * wok / wn)}%" if wn else "—"
        parts.append(
            "<h2 id='week'>This week</h2>"
            f"<p>{wn} attempts across {wdays} active day"
            f"{'s' if wdays != 1 else ''} · {wok} passed "
            f"({acc}) — your weekly review ritual: wins, weak spots, "
            f"next week on the <a href='/due'>Due</a> queue.</p>")
        parts.append(monthmod.section_html(db_path))
    parts.append("<h2 id='attempts'>Attempts</h2>"
                     "<p id='timestamps'><small>Relative times "
                     "(“just now”, “3h ago”) — hover any time for "
                     "the exact timestamp.</small></p>")
    for r in rows:
        cls = "ok" if (r["grade"] or 0) >= 4 else "stale"
        mark = "✓" if (r["grade"] or 0) >= 4 else "✗"
        parts.append(
            f"<p class='{cls}'>{mark} {html.escape(r['concept'] or '')} — "
            f"grade {r['grade']}/5, confidence {r['confidence']}/5 "
            f"<small>{cardsmod._rel_time(r['reviewed_at'] or '')}</small><br>"
            f"<small>in <a href='/modules/{r['module_id']}'>"
            f"{html.escape(r['summary'] or r['module_id'])}</a></small></p>")
    return "".join(parts)
