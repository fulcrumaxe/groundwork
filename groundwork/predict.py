"""Prediction-then-reveal (F-64): one-click cover on every code snippet.

Learners read code and nod — comprehension without a prediction is
cheap. This module owns the cover widget: ``cover_html`` wraps a
snippet in a ``<details class='predict'>`` whose summary invites a
prediction ("Predict the output, then reveal") and whose body holds
the escaped ``<pre>``. No JavaScript: the browser's native
disclosure does the covering, so no-JS readers get the same
struggle-first order. Db-free library — renderers are untouched;
pure functions, stdlib only (``html``), no I/O, no DB changes.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b13-predict"

SUMMARY_TEXT = "Predict the output, then reveal"


def cover_html(code: str = "", language: str = "python") -> str:
    """Snippet under a one-click cover; empty code renders nothing."""
    try:
        text = code if isinstance(code, str) else ""
        if not text.strip():
            return ""
        lang = (language or "python").strip().lower() or "python"
        if len(lang) > 20 or not lang.replace("+", "").replace(
                "-", "").replace("#", "").isalnum():
            lang = "python"
        return (
            "<details class='predict'>"
            f"<summary>{SUMMARY_TEXT}</summary>"
            f"<pre data-lang='{html.escape(lang, True)}'>"
            f"{html.escape(text)}</pre></details>")
    except Exception:  # noqa: BLE001 -- widget must never raise
        return ""


def is_covered(widget: str = "") -> bool:
    """True when a widget hides its snippet until clicked.

    A covered widget is a ``<details>`` without the ``open``
    attribute containing exactly one ``<pre>``; anything else
    (pre-shown, no snippet, wrong shape) is not covered.
    """
    try:
        if not isinstance(widget, str):
            return False
        low = widget.lower()
        if "<details" not in low or "<pre" not in low:
            return False
        tag = low.split("<details", 1)[1].split(">", 1)[0]
        if "open" in tag.split():
            return False
        return low.count("<pre") == 1
    except Exception:  # noqa: BLE001 -- check must never raise
        return False


def section_html() -> str:
    """Status-page subsection with a live covered snippet."""
    demo = cover_html("def double(n):\n    return n * 2\n\ndouble(21)")
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Predict-then-reveal <small>(feature)</small></h3>"
        "<p>Code snippets now hide until you commit to a prediction: "
        "<code>groundwork/predict.py</code> provides "
        "<code>cover_html()</code> (a native <code>&lt;details&gt;</code> "
        "cover — no JavaScript, so no-JS readers struggle first too) "
        "and <code>is_covered()</code>, a db-free library the "
        "renderers do not touch. Predict <code>double(21)</code>, then "
        "click below.</p>" + demo)


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "predict-reveal",
        "kind": "feature",
        "title": "Predict-then-reveal",
        "blurb": "Every code snippet hides under a one-click cover — predict first, then reveal.",
        "path": "/status",
        "anchor": "status-b13-predict",
    }
