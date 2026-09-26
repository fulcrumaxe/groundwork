"""Sandbox output inline on predict-output cards (I-156).

Predict-the-output (type 8) cards ask for a guess but hide the
sandbox-measured reference output until the Result screen, which
strands the learner off the queue. ``output_html`` renders that
stored measurement as a collapsed <details> block so the learner
predicts first, then reveals without leaving the card.

Pure HTML builders over card dicts — no HTTP, no subprocess, no
DB. The text shown is the stored ``expected`` value written by
``exercises.gen_predict_output`` and re-verified against a fresh
``SandboxRunner`` run at grade time; rendering never executes code,
so the card path stays synchronous and fast. Stdlib only
(``html``, ``json``); never raises.
"""
from __future__ import annotations

import html
import json

STATUS_ANCHOR = "status-b24-sandout"

_MAX_OUT = 500


def _payload_of(card) -> dict:
    """Card payload as a dict; {} for anything unreadable."""
    try:
        if isinstance(card, dict) and "payload" in card:
            return json.loads(card.get("payload") or "{}")
        if isinstance(card, dict):
            return card
    except (ValueError, TypeError):
        pass
    return {}


def measured_output(payload) -> str:
    """Stored sandbox-measured stdout, or "" when nothing was measured."""
    if not isinstance(payload, dict):
        return ""
    code = payload.get("code", "")
    expected = payload.get("expected", "")
    if not isinstance(code, str) or not isinstance(expected, str):
        return ""
    if not code.strip() or not expected.strip():
        return ""
    return expected.strip()


def output_html(card) -> str:
    """Collapsed measured-output reveal for a predict-output card.

    "" when the payload carries no measured output, so legacy and
    non-executable cards render byte-identical (legacy no-data
    fallback). Never raises.
    """
    try:
        out = measured_output(_payload_of(card))
        if not out:
            return ""
        shown = out[:_MAX_OUT]
        tail = "…" if len(out) > _MAX_OUT else ""
        return (
            "<details class='sandout'>"
            "<summary>Show measured output</summary>"
            f"<pre>{html.escape(shown)}{tail}</pre></details>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch24.py."""
    try:
        sample = output_html(
            {"payload": json.dumps(
                {"code": "print(2 + 3)", "expected": "5"})})
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Sandbox output inline "
            "<small>(improvement)</small></h3>"
            "<p>Predict-then-verify without leaving the card — "
            "<code>groundwork/sandout.py</code> renders the stored "
            "sandbox-measured output in a collapsed block on the "
            "type-8 widget (<code>cards.answer_widget</code>). "
            "A live sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Sandbox output inline</h3>"
                "<p>Inline-output help temporarily unavailable.</p>")
