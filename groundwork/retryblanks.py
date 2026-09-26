"""Retry wrong blanks only, keeping correct ones filled (I-161).

Cloze cards (exercise type 2) grade each blank independently in
``exercises.grade`` (groundwork/exercises.py, type-2 branch), but the
``wrong`` id list is flattened into a feedback string and discarded,
and ``cards.answer_widget`` re-renders every blank empty. A learner
who gets 2 of 3 blanks right must retype the 2 earned answers, which
invites fresh typos on already-proven input.

This module renders the retry form for the result screen: correct
blanks come back filled and locked (``readonly`` + a hidden
carry-field so the re-submit still posts them); only wrong blank ids
are editable. It posts the same ``b<id>`` shape through the unchanged
``POST /cards/<id>/review`` route (``_parse_review_form``), so no
``web.py`` edits are needed beyond embedding the returned string.

Per-blank hook (sibling item I-160, ``groundwork/partial.py``): pass
its per-blank pass/fail ids as ``wrong_ids`` and they are consumed
directly (``MCPServer.submit_review`` does exactly this). Standalone
fallback: ``wrong_ids=None`` recomputes correctness locally with the
same whitespace-normalized compare the grader uses; unparseable input
or a blank-less payload degrades to a full empty re-answer (today's
behavior).

Pure functions, stdlib only (``html``). No I/O, no DB/schema changes.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b24-retryblanks"


def _norm(value) -> str:
    """Whitespace-normalized compare, mirroring exercises._norm."""
    return " ".join(str(value).split())


def _blanks_of(card) -> list:
    """Blank specs from a card dict (or exercise-shaped dict)."""
    if not isinstance(card, dict):
        return []
    payload = card.get("payload", {})
    if not isinstance(payload, dict):
        return []
    blanks = payload.get("blanks")
    if isinstance(blanks, list) and all(isinstance(b, dict) for b in blanks):
        return blanks
    answers = payload.get("answers")
    if isinstance(answers, list) and answers:
        return [{"id": i, "answers": [a]} for i, a in enumerate(answers)]
    return []


def _given_of(submission) -> dict:
    """Parse ``id=value`` lines (one per line) into {id: value}."""
    given: dict = {}
    for line in str(submission or "").splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        try:
            given[int(key)] = value.strip()
        except ValueError:
            given[key] = value.strip()
    return given


def split_blanks(card, submission, wrong_ids=None) -> tuple:
    """Split blank ids into (correct, wrong).

    ``wrong_ids`` (the I-160 per-blank hook) wins when it names known
    blank ids; otherwise correctness is recomputed locally against
    each blank's accepted answers. Unknown input yields ([], all ids)
    so the caller degrades to a full re-answer, never to an empty form.
    """
    blanks = _blanks_of(card)
    ids = [b.get("id", i) for i, b in enumerate(blanks)]
    if not blanks:
        return ([], [])
    if wrong_ids is not None:
        try:
            if isinstance(wrong_ids, str):
                raise ValueError("wrong_ids must be an id list, not text")
            wanted = {int(w) for w in wrong_ids}
        except (TypeError, ValueError):
            wanted = None
        if wanted is not None:
            known = {w for w in wanted if w in ids}
            if known or not wanted:
                wrong = [i for i in ids if i in known]
                return ([i for i in ids if i not in known], wrong)
    given = _given_of(submission)
    correct, wrong = [], []
    for b, bid in zip(blanks, ids):
        answer = given.get(bid, given.get(str(bid), ""))
        candidates = {_norm(a) for a in b.get("answers", [])}
        (correct if _norm(answer) in candidates else wrong).append(bid)
    return (correct, wrong)


def retry_form(card, submission, wrong_ids=None, origin: str = "/due") -> str:
    """Retry form HTML: correct blanks locked+filled, wrong ones open.

    Returns "" when there is nothing to retry (non-cloze card, no
    blanks, or every blank correct). Correct blanks render ``readonly``
    with a hidden twin so the grade-preserving value still posts;
    wrong blanks render empty and editable. All output is escaped.
    """
    if not isinstance(card, dict):
        return ""
    blanks = _blanks_of(card)
    if not blanks:
        return ""
    correct, wrong = split_blanks(card, submission, wrong_ids)
    if not wrong:
        return ""
    given = _given_of(submission)
    ids = [b.get("id", i) for i, b in enumerate(blanks)]
    if set(wrong) - set(ids):
        return ""
    cid = html.escape(str(card.get("id", "")), quote=True)
    action = f"/cards/{cid}/review" if cid else "/due"
    parts = [f"<form method='post' action='{action}'>",
             f"<input type='hidden' name='origin' value='{html.escape(origin, quote=True)}'>"]
    for bid in ids:
        label = html.escape(str(bid), quote=True)
        if bid in correct:
            value = html.escape(str(given.get(bid, given.get(str(bid), ""))), quote=True)
            parts.append(
                f"<label>___({label}) <input name='b{label}' size='12' "
                f"value='{value}' readonly>"
                f"<input type='hidden' name='b{label}' value='{value}'></label>")
        else:
            parts.append(
                f"<label>___({label}) <input name='b{label}' size='12' "
                f"placeholder='retry blank {label}'></label>")
    parts.append("<button>Retry wrong blanks</button></form>")
    return " ".join(parts)


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Retry wrong blanks only <small>(improvement)</small></h3>"
        "<p>Cloze retries keep correct blanks filled and read-only and re-ask "
        "only the missed ids (``groundwork/retryblanks.py``); without per-blank "
        "data it falls back to a full re-answer. No DB change.</p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "retry-wrong-blanks",
        "kind": "improvement",
        "title": "Retry wrong blanks only",
        "blurb": "Miss a cloze blank or two: correct blanks stay filled and locked, so the retry asks only for the ones you missed.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
