"""One-click 5-minute session (I-46).

Builds a ~5-minute queue from the due list using per-card time
estimates, plus the Due-page banner that starts it. Pure functions,
stdlib only, no I/O.

Planning rule: most-overdue first (``due`` ascending, ``id``
tiebreak), greedily keeping each card while the running total stays
inside ``minutes * 60`` seconds. Returns a new list; the input is
never mutated. When anything is due, at least the single
most-overdue card is returned so the button always starts something.

Cost model: a never-attempted card costs NEW_SECS (default 30); a
reviewed card costs REVIEW_SECS (default 20). A card counts as new
when it carries an explicit ``attempts``/``tries``/``reviews`` count
of 0 — or when no attempt signal is present, so the budget errs
toward promising less than 5 minutes rather than more. Pass
``estimate_fn`` (``card -> seconds``) to override per card, e.g.
closing over ``queries.attempts``; ``new_secs``/``review_secs``
retune the default model.

Boundary: planning + banner snippet live here. Grading and queue
rendering stay with cards.py/queue.py; the session-end summary
stays with session.py.
"""
from __future__ import annotations

import html

DEFAULT_MINUTES = 5
NEW_SECS = 30
REVIEW_SECS = 20

_MISSING_DUE = "\uffff"


def _is_new(card: dict) -> bool:
    """True when the card looks never-attempted (cost model)."""
    for key in ("attempts", "tries", "reviews"):
        if key in card:
            try:
                return int(card[key]) <= 0
            except (TypeError, ValueError):
                return True
    return True


def estimate_for(card, estimate_fn=None, new_secs=NEW_SECS,
                 review_secs=REVIEW_SECS) -> float:
    """Seconds one card should cost; hostile input gets the default."""
    if callable(estimate_fn):
        try:
            return max(0.0, float(estimate_fn(card)))
        except (TypeError, ValueError):
            pass
    try:
        new = int(new_secs)
    except (TypeError, ValueError):
        new = NEW_SECS
    try:
        review = int(review_secs)
    except (TypeError, ValueError):
        review = REVIEW_SECS
    if not isinstance(card, dict) or _is_new(card):
        return float(max(0, new))
    return float(max(0, review))


def _due_key(card: dict):
    """Most-overdue first; missing due sorts last; id breaks ties."""
    due = card.get("due") if isinstance(card, dict) else ""
    due = due if isinstance(due, str) and due else _MISSING_DUE
    cid = card.get("id", "") if isinstance(card, dict) else ""
    return (due, str(cid))


def pick_cards(due, minutes=DEFAULT_MINUTES, estimate_fn=None,
               new_secs=NEW_SECS, review_secs=REVIEW_SECS,
               recent=None, tried=None) -> list:
    """Most-overdue prefix of ``due`` fitting in ``minutes`` of estimates.

    Non-dict entries are skipped; bad ``minutes`` falls back to
    DEFAULT_MINUTES; a non-empty queue always yields >= 1 card.

    Load guard (F-94): when the caller supplies a strain signal
    (``recent`` grades) or newness evidence (``tried`` attempt counts
    per card id), the budgeted picks pass through
    ``cogniload.cap_new_concepts`` so strained sessions introduce
    fewer new concepts. No signals means the legacy picks return
    untouched. Never raises; the guard never empties a non-empty plan.
    """
    rows = [c for c in (due or []) if isinstance(c, dict)]
    try:
        budget = float(minutes) * 60.0
    except (TypeError, ValueError):
        budget = float(DEFAULT_MINUTES) * 60.0
    budget = max(0.0, budget)
    ordered = sorted(rows, key=_due_key)
    picks: list = []
    total = 0.0
    for card in ordered:
        est = estimate_for(card, estimate_fn, new_secs, review_secs)
        if total + est > budget:
            break
        picks.append(card)
        total += est
    if not picks and ordered:
        picks.append(ordered[0])
    if recent is None and tried is None:
        return picks  # legacy: no strain signal, no guard
    from . import cogniload as cogmod
    try:
        marked = []
        for c in picks:
            if isinstance(c, dict) and isinstance(tried, dict):
                try:
                    c = dict(c, attempts=tried.get(c.get("id"), 0))
                except (TypeError, ValueError):
                    pass
            marked.append(c)
        return cogmod.cap_new_concepts(marked, recent=recent)
    except Exception:  # noqa: BLE001 -- guard never breaks picking
        return picks


def planned_seconds(picks, estimate_fn=None, new_secs=NEW_SECS,
                    review_secs=REVIEW_SECS) -> float:
    """Summed estimate for an already-picked list."""
    total = 0.0
    for card in picks or []:
        total += estimate_for(card, estimate_fn, new_secs, review_secs)
    return total


def _new_in(card: dict, tried: dict) -> bool:
    """Never-attempted in the minisession _is_new sense."""
    try:
        cid = card.get("id") if isinstance(card, dict) else None
        if cid in (tried or {}):
            return int(tried[cid] or 0) <= 0
        return _is_new(card)
    except (TypeError, ValueError):
        return True


def apply_dial(due, dial, tries=None, decay=None) -> list:
    """F-55: shape the Due queue by the difficulty dial.

    ``dial`` None/"" returns the legacy queue untouched; otherwise the
    level's retrievability floor drops too-forgotten reviews and the
    new-card cap keeps the first N never-attempted cards (attempts
    from ``tries``). Queue order is preserved (filter only, so the
    interleave bridge ordering survives). ``decay`` (F-91) floors on
    the personal curve instead; None/1.0 keeps the legacy floor.
    Never raises.
    """
    from . import diffdial as dialmod
    from . import forgetcurve as fmod
    from . import sched as schedmod
    try:
        if dial is None or (isinstance(dial, str) and not dial.strip()):
            return due
        params = dialmod.dial_params(dial)
        floor = float(params.get("retrievability_floor", 0.0) or 0.0)
        cap = int(params.get("new_cards", 0) or 0)
        try:
            personal = float(decay) if decay is not None else None
            if personal == 1.0:
                personal = None
        except (TypeError, ValueError):
            personal = None
        rows = [c for c in (due or []) if isinstance(c, dict)]
        try:
            tried = dict(tries or {})
        except (TypeError, ValueError):
            tried = {}
        kept = []
        for c in rows:
            try:
                iso = c.get("due", "")
                stab = float(c.get("stability", 1.0) or 0.0)
                if personal is None:
                    r = schedmod.elapsed_retrievability(
                        stab, iso if isinstance(iso, str) else "")
                else:
                    r = fmod.personal_retrievability(
                        stab, fmod.overdue_days(c), personal)
            except (TypeError, ValueError):
                r = 1.0
            if r >= floor:
                kept.append(c)
        fresh = [c for c in kept if _new_in(c, tried)]
        if len(fresh) > cap:
            drop = set(map(id, fresh[cap:]))
            kept = [c for c in kept if id(c) not in drop]
        return kept
    except Exception:  # noqa: BLE001 — dial must never break the queue
        return due


def cold_box(rows, due_concept_ids=None) -> str:
    """F-56: cold-attempt round from live concepts (``/due?mode=cold``).

    Mastered concepts (mastery ≥ 0.85) and concepts already due are
    excluded via cold_session; each pick renders its priming line
    with a study link. Empty pool renders the engine's note, never
    an empty section. Never raises.
    """
    from . import coldattempt as coldmod
    from . import lessons as lesmod
    try:
        items = [r for r in (rows or []) if isinstance(r, dict)]
        owned = {str(r.get("id", "")) for r in items
                 if (r.get("mastery") or 0.0) >= 0.85}
        try:
            due_ids = {str(i) for i in (due_concept_ids or []) if str(i)}
        except TypeError:
            due_ids = set()
        session = coldmod.cold_session(items, owned_ids=owned, due_ids=due_ids)
        meta = {str(r.get("id", "")): r for r in items}
        lis = []
        for it in session.get("items", []):
            cid = str(it.get("concept_id", ""))
            row = meta.get(cid, {})
            name = str(row.get("name") or cid)
            mid = str(row.get("module_id") or "")
            anchor = f"/modules/{mid}#lesson-{lesmod.slug(name)}" if mid else "/modules"
            lis.append(
                f"<li>{html.escape(str(it.get('prime', '')))} — "
                f"<a href='{html.escape(anchor, True)}'>"
                f"Study {html.escape(name)}</a></li>")
        body = "".join(lis)
        note = html.escape(str(session.get("note", "")))
        if body:
            body = f"<ol>{body}</ol>"
        return (f"<section id='cold'><h2>Cold round</h2>"
                f"<p>{note}</p>{body}</section>")
    except Exception:  # noqa: BLE001 — cold round never raises
        return ""


def dial_box(dial=None, mode="") -> str:
    """F-55: working difficulty control for the Due page.

    Links carry the dial level (session mode preserved); the line
    describes the active level via diffdial.describe. Always renders
    so the queue state stays explainable. Never raises.
    """
    from . import diffdial as dialmod
    try:
        active = dialmod.normalize_level(dial)
        params = dialmod.dial_params(active)
        suffix = f"mode={mode}&" if mode in ("one", "cold") else ""
        links = " · ".join(
            f"<a href='/due?{suffix}dial={n}'>{dialmod.LABELS[n]}</a>"
            + (" <b>(dialed)</b>" if n == active else "")
            for n in dialmod.LEVELS)
        return (f"<p id='dial'><small>Difficulty dial: {links}<br>"
                f"{html.escape(dialmod.describe(params))}</small></p>")
    except Exception:  # noqa: BLE001 — control never raises
        return ""


def session_box_html(due, minutes=DEFAULT_MINUTES, estimate_fn=None,
                     new_secs=NEW_SECS, review_secs=REVIEW_SECS,
                     recent=None, tried=None, flow_attempts=None) -> str:
    """Due-page banner: start button plus 'about N cards, ~M min' copy.

    Always renders (calm all-clear, no button, when nothing is due)
    so the ``minisession`` anchor never moves. The start link targets
    the lead-card ``#up-next`` tag, which is the picked set's first
    card since picks are most-overdue-first.
    """
    picks = pick_cards(due, minutes, estimate_fn, new_secs, review_secs,
                       recent=recent, tried=tried)
    if flow_attempts is not None:
        # Flow gate (F-95): in-flow sessions grow by a few bonus cards.
        # No attempts means no extension — the planned session stands.
        from . import flowdetect as flowdetectmod
        try:
            picks = flowdetectmod.extend_session(picks, due, flow_attempts)
        except Exception:  # noqa: BLE001 -- extension never breaks Due
            pass
    if not picks:
        return ("<section id='minisession'><p>All clear — nothing due. "
                "Browse a module to learn ahead.</p></section>")
    secs = planned_seconds(picks, estimate_fn, new_secs, review_secs)
    mins = max(1, round(secs / 60.0))
    n = len(picks)
    try:
        label = int(minutes)
    except (TypeError, ValueError):
        label = DEFAULT_MINUTES
    noun = "card" if n == 1 else "cards"
    return (
        f"<section id='minisession'><p>About {n} {noun}, "
        f"~{mins} min. <a id='mini-start' href='#up-next'>"
        f"Start {html.escape(str(label))}-minute session</a>.</p></section>"
    )


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b9-minisession'>Five-minute session "
        "<small>(improvement)</small></h3>"
        "<p>One click queues about five minutes of the most-overdue "
        "cards — new cards budgeted at 30s, reviews at 20s — and starts "
        "you on them. <code>groundwork/minisession.py</code> provides "
        "<code>pick_cards()</code> (greedy most-overdue fill against a "
        "seconds budget, never mutates its input) and "
        "<code>session_box_html()</code> (Due banner with the start "
        "button and 'about N cards' copy).</p>"
    )
