"""Inline glossary tooltips for jargon in leveled explainers (I-103).

Curated term table plus tooltip-markup helpers applied to leveled
explainer text on the lesson rendering path. Pure functions, stdlib
only (``html``, ``re``), no I/O, no DB changes, never raises.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b18-glossary"

MAX_TOOLTIPS = 12

TERMS = {
    "function": "a reusable set of instructions you can run by name",
    "argument": "an input value you hand to a function when you run it",
    "parameter": "the named slot a function declares for an input value",
    "return": "handing an answer back to whoever ran the function",
    "variable": "a named box that holds a value which can change",
    "call": "running a function",
    "module": "one file of code",
    "test": "a check that code does what it should",
    "bug": "a mistake in code that makes it misbehave",
    "trace": "the values a variable takes, step by step, as code runs",
    "class": "a blueprint for building objects that bundle data and behaviour",
    "method": "a function that belongs to a class",
    "loop": "code that repeats",
    "condition": "a yes/no question the code branches on",
    "recursion": "a function that runs itself to solve smaller pieces",
    "exception": "an error signal the code raises when something goes wrong",
    "import": "bringing code from another file into this one",
    "callback": "a function you hand to other code so it can run it later",
}

_SORTED_TERMS = sorted(TERMS, key=len, reverse=True)
_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(t) + r"s?" for t in _SORTED_TERMS) + r")\b",
    re.IGNORECASE,
)


def term_def(term: str) -> str:
    """One-line definition for a term (plural-tolerant); "" when unknown."""
    try:
        key = (term or "").strip().lower()
        if key in TERMS:
            return TERMS[key]
        if key.endswith("s") and key[:-1] in TERMS:
            return TERMS[key[:-1]]
        return ""
    except Exception:  # noqa: BLE001 -- lookup never raises
        return ""


def _wrap(match: "re.Match", budget: list) -> str:
    word = match.group(1)
    if budget[0] <= 0:
        return word
    defn = term_def(word)
    if not defn:
        return word
    budget[0] -= 1
    return (
        f"<dfn class='gloss' tabindex='0' title='{html.escape(defn, quote=True)}'>"
        f"{html.escape(word)}</dfn>"
    )


def gloss_html(text: str) -> str:
    """Plain text -> escaped HTML with known jargon wrapped in tooltips.

    Unknown terms pass through as plain escaped text (legacy fallback).
    Empty/hostile input returns escaped text or "" -- never raises.
    """
    try:
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)
        # Escape first so matching runs on safe text; terms are plain
        # ascii words, for which escaping is a fixed point.
        safe = html.escape(text)
        budget = [MAX_TOOLTIPS]
        return _PATTERN.sub(lambda m: _wrap(m, budget), safe)
    except Exception:  # noqa: BLE001 -- markup never raises
        try:
            return html.escape(str(text))
        except Exception:  # noqa: BLE001
            return ""


def annotate_html(fragment: str) -> str:
    """Already-escaped HTML fragment -> same fragment with tooltips in text nodes.

    Splits on tags so tag names/attributes are never matched; text segments
    are already escaped, so substitution wraps without re-escaping.
    Unknown terms pass through untouched; never raises.
    """
    try:
        if fragment is None:
            return ""
        if not isinstance(fragment, str):
            fragment = str(fragment)
        if not fragment:
            return ""
        parts = re.split(r"(<[^>]*>)", fragment)
        budget = [MAX_TOOLTIPS]
        for i in range(0, len(parts), 2):
            parts[i] = _PATTERN.sub(lambda m: _wrap_raw(m, budget), parts[i])
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- markup never raises
        try:
            return str(fragment)
        except Exception:  # noqa: BLE001
            return ""


def _wrap_raw(match: "re.Match", budget: list) -> str:
    # Text nodes here are already escaped; the match is safe to re-emit raw.
    word = match.group(1)
    if budget[0] <= 0:
        return word
    defn = term_def(word)
    if not defn:
        return word
    budget[0] -= 1
    return (
        f"<dfn class='gloss' tabindex='0' title='{html.escape(defn, quote=True)}'>"
        f"{word}</dfn>"
    )


def section_html() -> str:
    """Anchored status subsection; joined by the batch18 home module."""
    sample = gloss_html("Recursion means the function makes a call with new arguments.")
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Inline glossary tooltips <small>(improvement)</small></h3>"
        "<p>Jargon in leveled explainers now defines itself in place: "
        "<code>groundwork/glossary.py</code> provides a curated term table plus "
        "<code>gloss_html()</code>/<code>annotate_html()</code> helpers that wrap known "
        "terms in <code>&lt;dfn class='gloss'&gt;</code> tooltips on the lesson rendering "
        "path (<code>lessons.render_levels</code>). Unknown words pass through untouched; "
        "without CSS/JS the markup degrades to plain text. A live sample renders below.</p>"
        f"<p>{sample}</p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "inline-glossary",
        "kind": "improvement",
        "title": "Inline glossary tooltips",
        "blurb": "Jargon in leveled explainers defines itself on hover — no lookup, no lost place.",
        "path": "/status",
        "anchor": "status-b18-glossary",
    }
