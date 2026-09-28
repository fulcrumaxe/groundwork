"""Answer history diff on the result screen (I-197): "last time you wrote X".

A repeat review grades in isolation: the learner sees only today's
verdict, never what they answered last time, so a repeated mistake
reads as a fresh one. This module closes that gap at grade time. The
prior submission already stored in ``reviews.submission`` is compared
with the current answer, and when the two differ a one-line diff rides
the result dict as ``answer_hist`` to the result screen. Nothing is
stored (no schema change) and no new query shape is needed beyond the
one indexed lookup the caller runs: no prior answer, a blank answer,
or an unchanged answer yields no key, and the render seam prints
nothing, so first attempts render legacy-identical. Stdlib only
(``html``); never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b29-answerhist"

#: Longest prior answer shown inline; the reviews table keeps 4000 chars.
MAX_SHOWN = 160


def _clean(value) -> str:
    """Stripped text, else ""."""
    if not isinstance(value, str):
        return ""
    return value.strip()


def _norm(value) -> str:
    """Compare form: runs of whitespace collapse, so spacing-only edits
    are not reported as change. Case-sensitive: "Paris" vs "paris" is
    a real edit worth showing."""
    return " ".join(_clean(value).split())


def changed(prior, current) -> bool:
    """True when both answers are non-blank and differ after normalizing."""
    try:
        p, c = _norm(prior), _norm(current)
        return bool(p and c and p != c)
    except Exception:  # noqa: BLE001 -- compare never raises
        return False


def _shown(prior: str) -> str:
    """Display form of a prior answer: stripped, truncated, ASCII."""
    text = _clean(prior)
    if len(text) > MAX_SHOWN:
        text = text[:MAX_SHOWN].rstrip() + "..."
    return text


def diff_line(prior, current) -> str:
    """Plain-text history line; "" when there is nothing new to show.

    Returns ``Last time you wrote "X".`` only when a prior answer
    exists, the current answer is non-blank, and the two differ. A
    missing, blank, hostile, or unchanged prior stays quiet, so the
    dense result screen earns the extra line only on change.
    """
    try:
        if not changed(prior, current):
            return ""
        return f'Last time you wrote "{_shown(prior)}".'
    except Exception:  # noqa: BLE001
        return ""


def line_html(prior, current) -> str:
    """Result-screen line for a changed answer; "" when quiet."""
    try:
        line = diff_line(prior, current)
        if not line:
            return ""
        return f"<p><small>{html.escape(line)}</small></p>"
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def attach(result, prior, current):
    """Set ``result["answer_hist"]`` when the answer changed.

    One-line grade-time seam: ``result = answerhistmod.attach(result,
    prior, submission)``. The value is the pre-rendered, pre-escaped
    line, joined verbatim by ``results.render_result`` like the other
    composed HTML (``similar``, ``nextup``). Unchanged or first
    attempts keep their legacy dict shape. Same object; never raises.
    """
    try:
        if not isinstance(result, dict):
            return result
        line = line_html(prior, current)
        if line:
            result["answer_hist"] = line
    except Exception:  # noqa: BLE001 -- attach never blocks grading
        pass
    return result


def _demo() -> str:
    """Static format sample; live lines are built at grade time.

    Deliberately not a live lookup: the Status page must render
    byte-identical across runs (pagesnap gate), and per-card history
    never repeats. Grade-time attach is proven by the
    CallerEffectTest, not by this illustration.
    """
    return ("<p><small>Sample rendering with illustrative values "
            "(live lines are built at grade time): "
            "Last time you wrote &quot;Paris&quot;.</small></p>")


def section_html() -> str:
    """Anchored status subsection; joined by the batch29 home module."""
    try:
        demo = _demo()
    except Exception:  # noqa: BLE001 -- status must always render
        demo = ""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Answer history diff "
        "<small>(improvement)</small></h3>"
        "<p>Repeat reviews graded in isolation: only today's verdict, "
        "never what you answered last time. "
        "<code>groundwork/answerhist.py</code> compares the stored prior "
        "submission with the current answer at grade time and shows "
        "<code>Last time you wrote \"X\".</code> on the result screen "
        "(<code>results.render_result</code>) when the answer changed. "
        "First attempts and unchanged repeats show nothing, so legacy "
        "output stays byte-identical. A "
        "format sample renders below.</p>"
        f"{demo}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "answer-history",
        "kind": "improvement",
        "title": "Answer history diff",
        "blurb": "When your answer changes, the result shows what you "
                 "wrote last time -- catch repeated mistakes.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
