"""Fuller FSRS-4.5 parameters with per-learner optimization (I-201).

sched.py ships FSRS-lite: one fixed difficulty step, one fixed
stability-growth shape, and one forgetting curve for every learner.
This module owns the fuller model: grade-specific initial stability
and difficulty, difficulty mean-reversion, retrievability-modulated
stability growth, and a two-knob per-learner fit (growth x decay)
chosen by replaying the learner's own review history and keeping the
knobs that best predicted it. Db-free library: pure functions, stdlib
only (math), no I/O, no DB or schema changes.

Wiring (Batch-14 precedent): sched.review_card gains optional
params/lag_days kwargs. params=None runs today's code verbatim -- the
legacy default every existing caller relies on. params=None here
means DEFAULT knobs, not the legacy path: the legacy path is sched
not calling advance() at all. When MCPServer.submit_review fits knobs
from the trailing reviews history it passes them through and the
fuller update runs instead.
"""
from __future__ import annotations

import math

STATUS_ANCHOR = "status-b29-fsrs45"

# Fuller parameter set (FSRS-4.5 shape on this codebase's scale:
# difficulty in [0.1, 1.0], stability in days).
S0 = {1: 0.4, 2: 1.2, 3: 2.5, 4: 5.0}  # initial stability per rating
D_INIT = 0.5      # difficulty center (D0 of a Good recall)
D_SPREAD = 0.15   # difficulty step per rating point off Good
DRIFT = 0.08      # difficulty move per grade point off 3
REVERT = 0.15     # mean-reversion weight toward D0(Good)
GAIN = 3.0        # stability-gain scale on recall
STAB_EXP = 0.3    # stability exponent (mature memories grow slower)
RATE = 1.0        # retrievability sensitivity of the gain
HARD_FACTOR = 0.5  # Hard recalls earn half the Good gain
FORGET_KEEP = 0.3  # stability fraction kept on a lapse
D_MIN = 0.1
D_MAX = 1.0
S_MIN = 0.1
NOMINAL_R = 0.9   # assumed retrievability when the lag is unknown

# Per-learner fit grid (growth x decay), replayed over history.
GROWTHS = (0.5, 0.7, 1.0, 1.4, 2.0)
DECAYS = (0.6, 0.8, 1.0, 1.3, 1.6)
MIN_EVENTS = 6     # scored recalls needed before personalizing
MIN_GAIN = 0.005   # min mean-log-loss beat over defaults to adopt
MAX_EVENTS = 400   # trailing cap so fitting stays cheap


def _num(value, default):
    try:
        got = float(value)
    except (TypeError, ValueError):
        return default
    return default if got != got else got  # NaN fails closed


def _knobs(params) -> tuple:
    """(growth, decay) from a fit dict; (1.0, 1.0) on anything hostile."""
    try:
        growth = _num((params or {}).get("growth", 1.0), 1.0)
        decay = _num((params or {}).get("decay", 1.0), 1.0)
    except AttributeError:
        return (1.0, 1.0)
    if growth <= 0:
        growth = 1.0
    if decay <= 0:
        decay = 1.0
    return (min(4.0, growth), min(4.0, decay))


def to_rating(grade) -> int:
    """Grade 0-5 mapped to FSRS rating 1-4 (Again/Hard/Good/Easy)."""
    try:
        g = max(0, min(5, int(grade)))
    except (TypeError, ValueError):
        return 1
    if g <= 2:
        return 1
    if g == 3:
        return 2
    if g == 4:
        return 3
    return 4


def initial_stability(rating, growth=1.0) -> float:
    """First-review stability for a rating; Good on hostile input."""
    try:
        r = max(1, min(4, int(rating)))
    except (TypeError, ValueError):
        r = 3
    g = _num(growth, 1.0)
    if g <= 0:
        g = 1.0
    return max(S_MIN, S0[r] * min(4.0, g))


def initial_difficulty(rating) -> float:
    """First-review difficulty for a rating; center on hostile input."""
    try:
        r = max(1, min(4, int(rating)))
    except (TypeError, ValueError):
        r = 3
    return min(D_MAX, max(D_MIN, D_INIT - (r - 3) * D_SPREAD))


def recall_prob(stability, lag_days, decay=1.0) -> float:
    """Recall probability under decay; sched's curve exactly at 1.0."""
    try:
        stab = float(stability)
        lag = max(0.0, float(lag_days))
        kk = float(decay)
        if kk <= 0:
            kk = 1.0
        if stab <= 0:
            return 0.0
        return (1.0 + lag / (9.0 * (stab / kk))) ** -1
    except (TypeError, ValueError):
        return 1.0


def days_since(stamp_iso, now=None) -> float | None:
    """Days from an ISO stamp to now; None on anything hostile."""
    try:
        from datetime import datetime, timezone
        due = datetime.strptime(str(stamp_iso),
                                "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        end = now or datetime.now(timezone.utc)
        return max(0.0, (end - due).total_seconds() / 86400.0)
    except (TypeError, ValueError):
        return None


def advance(stability, difficulty, grade, lag_days=None, params=None,
            first=False) -> tuple:
    """Fuller FSRS-4.5 update; returns (stability, difficulty).

    First reviews initialize from the S0/D0 tables; recalls grow
    stability by a gain that rises as retrievability falls (hard-won
    recalls count more); lapses keep a retrievability-weighted
    fraction; difficulty drifts then reverts toward center. params
    carries the fitted (growth, decay) knobs (defaults when absent).
    Never raises.
    """
    try:
        growth, decay = _knobs(params)
        stab = _num(stability, 1.0)
        if not math.isfinite(stab) or stab <= 0:
            stab = 1.0
        diff = min(D_MAX, max(D_MIN, _num(difficulty, D_INIT)))
        try:
            g = max(0, min(5, int(grade)))
        except (TypeError, ValueError):
            return (max(S_MIN, stab), diff)
        rating = to_rating(g)
        if first:
            return (initial_stability(rating, growth),
                    initial_difficulty(rating))
        retr = NOMINAL_R if lag_days is None else recall_prob(
            stab, lag_days, decay)
        if rating == 1:
            stab = max(S_MIN, stab * FORGET_KEEP * (0.5 + retr))
        else:
            inc = (growth * GAIN * (1.1 - diff) * (stab ** STAB_EXP)
                   * (math.exp(RATE * (1.0 - retr)) - 1.0))
            if rating == 2:
                inc *= HARD_FACTOR
            stab = stab * (1.0 + max(0.0, inc))
        diff = diff - DRIFT * (g - 3)
        diff = REVERT * D_INIT + (1.0 - REVERT) * diff
        return (max(S_MIN, stab), min(D_MAX, max(D_MIN, diff)))
    except Exception:  # noqa: BLE001 -- scheduling must never raise
        try:
            return (max(S_MIN, float(stability)),
                    min(D_MAX, max(D_MIN, float(difficulty))))
        except (TypeError, ValueError):
            return (1.0, D_INIT)


def clean_sequences(rows) -> list:
    """Per-card [(grade, lag_days|None)] oldest-first; trailing-capped.

    Rows are mappings (card_id/grade/reviewed_at) or tuples in that
    order; anything unparseable is skipped. Lags run between a card's
    consecutive reviews, so each chain head has lag None and scores
    no event. Never raises.
    """
    try:
        from datetime import date
        by_card: dict = {}
        for row in rows or []:
            try:
                if isinstance(row, dict):
                    cid = row.get("card_id", "")
                    grade, when = row.get("grade"), row.get("reviewed_at")
                else:
                    cid, grade, when = row[0], row[1], row[2]
                g = int(grade)
            except (TypeError, IndexError, KeyError, ValueError):
                continue
            when = str(when or "")
            if not cid or not when:
                continue
            by_card.setdefault(str(cid), []).append(
                (max(0, min(5, g)), when))
        seqs = []
        for attempts in by_card.values():
            attempts.sort(key=lambda a: a[1])
            seq, prev = [], None
            for g, when in attempts:
                lag = None
                if prev is not None:
                    try:
                        lag = max(0, (date.fromisoformat(when[:10])
                                     - date.fromisoformat(prev[:10])).days)
                    except ValueError:
                        continue  # bad stamp breaks the chain; skip event
                seq.append((g, lag))
                prev = when
            if seq:
                seqs.append(seq)
        total = sum(len(s) for s in seqs)
        if total > MAX_EVENTS:
            drop = total - MAX_EVENTS
            trimmed = []
            for s in seqs:
                if drop <= 0:
                    trimmed.append(s)
                    continue
                cut = min(drop, len(s))
                drop -= cut
                if s[cut:]:
                    head = list(s[cut:])
                    head[0] = (head[0][0], None)  # new chain head: no lag
                    trimmed.append(head)
            seqs = trimmed
        return seqs
    except Exception:  # noqa: BLE001 -- cleaning must never raise
        return []


def _replay_loss(seq, growth, decay) -> tuple:
    """Binary log-loss of predicted retrievability over one sequence."""
    loss, n = 0.0, 0
    stab, diff, first = 1.0, D_INIT, True
    for g, lag in seq:
        if lag is not None:
            p = min(1.0 - 1e-6,
                    max(1e-6, recall_prob(stab, lag, decay)))
            y = 1.0 if g >= 3 else 0.0
            loss += -(y * math.log(p) + (1.0 - y) * math.log(1.0 - p))
            n += 1
        stab, diff = advance(stab, diff, g, lag_days=lag,
                             params={"growth": growth, "decay": decay},
                             first=first)
        first = False
    return (loss, n)


def fit(rows) -> dict | None:
    """Per-learner (growth, decay) from recall history; None keeps legacy.

    Replays every card's review sequence under each grid candidate and
    keeps the knobs whose predicted retrievability best explained what
    the learner actually recalled (binary log-loss). Returns None when
    history is too thin (< MIN_EVENTS scored recalls) or no candidate
    beats the defaults by MIN_GAIN -- both mean the legacy schedule
    stands. Never raises.
    """
    try:
        seqs = clean_sequences(rows)
        scored = sum(1 for s in seqs for (_, lag) in s if lag is not None)
        if scored < MIN_EVENTS:
            return None

        def mean_loss(growth, decay):
            tot, n = 0.0, 0
            for s in seqs:
                loss, k = _replay_loss(s, growth, decay)
                tot += loss
                n += k
            return tot / n if n else float("inf")

        base = mean_loss(1.0, 1.0)
        best, best_loss = None, base - MIN_GAIN
        for growth in GROWTHS:
            for decay in DECAYS:
                if growth == 1.0 and decay == 1.0:
                    continue
                got = mean_loss(growth, decay)
                if got < best_loss:
                    best, best_loss = {"growth": growth, "decay": decay}, got
        return best
    except Exception:  # noqa: BLE001 -- fitting must never raise
        return None


def describe(params) -> str:
    """One-line reading of the fit; never raises."""
    try:
        if not params:
            return "Standard FSRS schedule -- no personal fit yet."
        growth, decay = _knobs(params)
        if growth > 1.15:
            grower = "fast grower"
        elif growth < 0.87:
            grower = "slow grower"
        else:
            grower = "steady grower"
        if decay > 1.15:
            fader = "fast fader"
        elif decay < 0.87:
            fader = "slow fader"
        else:
            fader = "steady fader"
        return (f"Personal fit (growth={growth:.2f}, decay={decay:.2f})"
                f" -- {grower}, {fader}.")
    except Exception:  # noqa: BLE001 -- describe must never raise
        return "Standard FSRS schedule."


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Fuller FSRS fit <small>(improvement)</small></h3>"
        "<p>Review gaps now use fuller FSRS-4.5 updates tuned to your "
        "own recalls: <code>groundwork/fsrs45.py</code> fits a personal "
        "(growth, decay) pair by replaying your review history and "
        "keeping the knobs that best predicted it. "
        f"Fast fader: {describe({'growth': 0.7, 'decay': 1.6})} "
        f"Slow fader: {describe({'growth': 1.4, 'decay': 0.6})}</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "fsrs45-fit",
        "kind": "improvement",
        "title": "Fuller FSRS fit",
        "blurb": ("Review gaps use fuller FSRS-4.5 updates tuned to your "
                  "own recall history -- newcomers keep the standard schedule."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
