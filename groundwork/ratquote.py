"""Decision-context quote beside design-rationale choices (I-176).

Type-7 (design-rationale) cards ask what beat what, but the recorded
why only appears on the lesson page (decisions.lesson_block), so the
learner decides before seeing the context. ``quote_html`` renders the
linked decision's own words beside the choice buttons.

The quote resolves ONLY from live card data: payload ``reason``,
``answer``, and ``choices`` copied from the linked decision record by
``exercises.gen_design_rationale`` (or caller-authored through
create_learning_module payloads). No text is invented: a missing
reason yields "" and the widget renders byte-identical legacy.

Pure HTML builders over card rows - no HTTP, no DB. Stdlib only
(``html``, ``json``); never raises.
"""
from __future__ import annotations

import html
import json

STATUS_ANCHOR = "status-b26-ratquote"

_MAX_REASON = 500


def _payload_of(card) -> dict:
    """Card payload as a dict; {} for anything unreadable."""
    try:
        if isinstance(card, dict) and "payload" in card:
            return json.loads(card.get("payload") or "{}")
        if isinstance(card, dict):
            return card
        try:
            raw = card["payload"]
        except (KeyError, IndexError, TypeError):
            return {}
        return json.loads(raw or "{}")
    except (ValueError, TypeError):
        pass
    return {}


def _etype_of(card) -> str:
    """Exercise type as text; "" when unreadable (Row- and dict-safe)."""
    try:
        if isinstance(card, dict):
            return str(card.get("exercise_type") or "")
        return str(card["exercise_type"] or "")
    except (KeyError, IndexError, TypeError):
        return ""


def decision_quote(payload) -> str:
    """Recorded decision reason from a type-7 payload, or "".

    Resolves only when ``reason`` is a non-empty string and the card
    is not explicitly ungrounded; ungrounded and agent-authored cards
    without decision text honestly yield "".
    """
    if not isinstance(payload, dict):
        return ""
    if payload.get("grounded") is False:
        return ""
    reason = payload.get("reason", "")
    if not isinstance(reason, str) or not reason.strip():
        return ""
    return reason.strip()


def _rejected(payload: dict, answer: str) -> str:
    """First stored choice that is not the answer; "" when none."""
    choices = payload.get("choices", [])
    if not isinstance(choices, list):
        return ""
    for c in choices:
        if isinstance(c, str) and c and c != answer:
            return c
    return ""


def quote_html(card) -> str:
    """Chose-X-over-Y quote beside type-7 choices; "" when none resolves.

    Type 7 only; "" for every other type and whenever no recorded
    reason resolves, so legacy cards render byte-identical. The text
    shown is the stored payload reason (plus stored answer/choices),
    written from the linked decision record at generation - never
    invented here. Never raises.
    """
    try:
        if _etype_of(card) != "7":
            return ""
        p = _payload_of(card)
        reason = decision_quote(p)
        if not reason:
            return ""
        shown = reason[:_MAX_REASON]
        tail = "..." if len(reason) > _MAX_REASON else ""
        answer = p.get("answer", "")
        answer = answer.strip() if isinstance(answer, str) else ""
        if not answer:
            return ("<blockquote class='ratquote'>"
                    f"{html.escape(shown)}{tail}</blockquote>")
        over = _rejected(p, answer)
        over_bit = f" over {html.escape(over)}" if over else ""
        return ("<blockquote class='ratquote'>"
                f"Chose <b>{html.escape(answer)}</b>{over_bit} - "
                f"{html.escape(shown)}{tail}</blockquote>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def tour_entry() -> dict:
    """Tour registry entry for the decision-context quote."""
    return {"id": "rationale-quote", "kind": "improvement",
            "title": "Decision quote beside rationale choices",
            "blurb": ("Type-7 cards quote the recorded chose-X-over-Y "
                      "context beside the choice buttons."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch26.py."""
    try:
        sample = quote_html(
            {"exercise_type": "7", "payload": json.dumps(
                {"choices": ["signed token", "raw JSON blob"],
                 "answer": "signed token",
                 "reason": ("Unsigned blobs are forgeable; signing keeps "
                            "the link tamper-evident."),
                 "grounded": True})})
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Decision quote beside rationale choices "
            "<small>(improvement)</small></h3>"
            "<p>Type-7 cards ask what beat what - "
            "<code>groundwork/ratquote.py</code> quotes the recorded "
            "decision context beside the choice buttons "
            "(<code>cards.answer_widget</code>). The text is the stored "
            "payload reason from the linked decision record, never "
            "invented; cards without one render byte-identical. "
            "A live sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Decision quote beside rationale "
                "choices</h3>"
                "<p>Quote help temporarily unavailable.</p>")
