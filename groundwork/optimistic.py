"""Optimistic UI on review submit (I-82): disable + spinner to hide latency.

Submitting a card review currently shows nothing until the server round
trip (or the collapse fetch) resolves, so slow connections invite double
clicks. This module owns ONLY the submit-guard presentation: on
``submit`` each card-review form disables its buttons and appends a
small spinner plus a ``Working...`` status line. It never calls
``preventDefault``/``stopPropagation`` and never touches
``fetch``/``localStorage``/``sessionStorage``, so the other
submit-listener owners keep working unchanged:

* ``collapse.py`` still intercepts via ``fetch`` and collapses the card.
* ``unsaved.py`` (+ ``GLOBAL_JS`` drafts) still clears draft keys.
* No-JS browsers submit normally (progressive enhancement).

Targets are the real forms ``cards.answer_widget`` emits (answer +
give-up, both ``POST /cards/<id>/review``), hence the same selector as
``collapse.FORM_SELECTOR``. ``optimistic_css()`` returns raw CSS
declarations only, never ``<style>`` tags -- the parent concatenates it
into the head wire next to ``progbar_css()``. The spin iteration is
SPIN_MS (250ms, under the 300ms budget); a ``prefers-reduced-motion``
override sets ``animation:none`` so reduced-motion users get a static
ring plus the ``Working...`` text. Pure functions, stdlib only (``re``),
no I/O, no DB/schema changes.
"""
from __future__ import annotations

import re

#: Queue-card review forms only. Same as ``collapse.FORM_SELECTOR``:
#: the ``[action$='/review']`` tail keeps snooze forms
#: (``/cards/<id>/snooze``) out while covering both forms
#: ``cards.answer_widget`` emits (answer + give-up, both POST review).
FORM_SELECTOR = "form[action^='/cards/'][action$='/review']"

SCRIPT_MARKER = "data-optimistic-submit"
STATUS_ANCHOR = "status-b12-optimistic"

SPINNER_CLASS = "gw-spinner"
STATUS_CLASS = "gw-status"
BUSY_FLAG = "data-gw-optimistic"
STATUS_TEXT = "Working..."

#: One spinner revolution in ms; continuous rotation, so each cycle
#: stays inside the 300ms motion budget.
SPIN_MS = 250
MAX_SPIN_MS = 300

_DURATION_RE = re.compile(r"(\d+)\s*ms")


def form_selector(extra=None) -> str:
    """CSS selector for card-review forms, with one optional prepend.

    Same bracket-scoped quote rule as ``autofocus.field_selector``:
    ``extra`` must not contain ``<>`` or backticks, its brackets must
    balance, and quotes may only sit inside ``[...]`` attribute
    brackets (the normal ``action^='...'`` shape) -- stray quotes
    outside brackets fall back to the default. Never raises.
    """
    try:
        if not isinstance(extra, str):
            return FORM_SELECTOR
        cand = extra.strip()
        if not cand or any(ch in cand for ch in "<>`"):
            return FORM_SELECTOR
        if cand.count("[") != cand.count("]"):
            return FORM_SELECTOR
        neb = re.sub(r"\[[^\[\]]*\]", "", cand)
        if any(ch in neb for ch in "\"'"):
            return FORM_SELECTOR
        return f"{cand},{FORM_SELECTOR}"
    except Exception:  # noqa: BLE001 -- selector lookup must never raise
        return FORM_SELECTOR


def _js_string(value) -> str:
    """Double-quoted JS string literal for a CSS selector (safe).

    Double quotes keep the common ``action^='...'`` selectors
    byte-identical inside the literal; backslash and double-quote are
    escaped. Same shape as ``autofocus._js_string``.
    """
    try:
        if not isinstance(value, str) or not value:
            value = FORM_SELECTOR
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    except Exception:  # noqa: BLE001 -- literal builder must never raise
        return '"' + FORM_SELECTOR + '"'


def spin_ms(value=SPIN_MS) -> int:
    """Clamped spinner iteration in ms (0..MAX_SPIN_MS).

    Non-numeric, negative, or over-budget input fails closed to
    SPIN_MS; never raises.
    """
    try:
        v = int(value)
        if v < 0 or v > MAX_SPIN_MS:
            return SPIN_MS
        return v
    except Exception:  # noqa: BLE001 -- duration lookup must never raise
        return SPIN_MS


def optimistic_js(selector=None) -> str:
    """Submit-guard snippet: disable buttons + show spinner on submit.

    One ``submit`` listener per review form. The handler only marks the
    form busy (``data-gw-optimistic``), disables its buttons, and
    appends a ``gw-spinner`` dot plus a ``role='status'`` ``Working...``
    line -- the submit itself proceeds untouched, so grading,
    collapse-fetch, and draft-clear listeners all still run. Repeat
    submits are idempotent (flag + existing-spinner checks), so one
    answer can never render two spinners. No ``fetch`` check needed:
    without JS the form submits normally. Non-string/empty
    ``selector`` falls back to the default; never raises at build time.
    """
    try:
        sel = form_selector(selector) if selector is not None else FORM_SELECTOR
        lit = _js_string(sel)
    except Exception:  # noqa: BLE001 -- guard snippet must never raise
        lit = _js_string(FORM_SELECTOR)
    try:
        return (
            "<script " + SCRIPT_MARKER + ">"
            "(function(){"
            "if(!document.querySelectorAll)return;"
            "var SEL=" + lit + ";"
            "function guard(f){"
            "try{"
            "if(f.getAttribute(\"" + BUSY_FLAG + "\"))return;"
            "f.setAttribute(\"" + BUSY_FLAG + "\",\"1\");"
            "Array.prototype.forEach.call(f.querySelectorAll(\"button\"),"
            "function(b){b.disabled=true;});"
            "if(f.querySelector(\"." + SPINNER_CLASS + "\"))return;"
            "var s=document.createElement(\"span\");"
            "s.className=\"" + SPINNER_CLASS + "\";"
            "s.setAttribute(\"aria-hidden\",\"true\");"
            "var t=document.createElement(\"span\");"
            "t.className=\"" + STATUS_CLASS + "\";"
            "t.setAttribute(\"role\",\"status\");"
            "t.textContent=\"" + STATUS_TEXT + "\";"
            "f.appendChild(s);f.appendChild(t);"
            "}catch(e){}}"
            "Array.prototype.forEach.call(document.querySelectorAll(SEL),"
            "function(f){f.addEventListener(\"submit\","
            "function(){guard(f);});});"
            "})();</script>"
        )
    except Exception:  # noqa: BLE001 -- guard snippet must never raise
        return "<script " + SCRIPT_MARKER + "></script>"


def optimistic_css() -> str:
    """Raw CSS declarations: spinner shape + reduced-motion override.

    Never emits ``<style>`` tags; the parent wires this into the head
    stylesheet. Never raises.
    """
    try:
        ms = spin_ms()
        return (
            "." + SPINNER_CLASS + "{display:inline-block;width:.9em;height:.9em;"
            "vertical-align:-0.15em;border:2px solid #999;"
            "border-top-color:#1a1a1a;border-radius:50%;"
            f"animation:gw-spin {ms}ms linear infinite}}"
            "@keyframes gw-spin{to{transform:rotate(360deg)}}"
            "." + STATUS_CLASS + "{font-size:.85rem;margin-left:.4rem}"
            "@media(prefers-reduced-motion:reduce){"
            "." + SPINNER_CLASS + "{animation:none;border-color:#999}"
            "." + STATUS_CLASS + "{font-size:.85rem}}"
        )
    except Exception:  # noqa: BLE001 -- CSS emitter must never raise
        return (
            ".gw-spinner{display:inline-block;width:.9em;height:.9em;"
            "vertical-align:-0.15em;border:2px solid #999;"
            "border-top-color:#1a1a1a;border-radius:50%;"
            "animation:gw-spin 250ms linear infinite}"
            "@keyframes gw-spin{to{transform:rotate(360deg)}}"
            ".gw-status{font-size:.85rem;margin-left:.4rem}"
            "@media(prefers-reduced-motion:reduce){"
            ".gw-spinner{animation:none;border-color:#999}"
            ".gw-status{font-size:.85rem}}"
        )


def demo_html() -> str:
    """Status-page demo: one review form showing the guard targets."""
    return (
        "<article id='card-demo'>"
        "<p>What is the capital of France?</p>"
        "<form method='post' action='/cards/demo/review'>"
        "<label>It prints/returns: <input name='answer' size='30'></label> "
        "<button>Check prediction</button></form></article>"
    )


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    try:
        ms = spin_ms()
    except Exception:  # noqa: BLE001 -- status must never raise
        ms = SPIN_MS
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Optimistic submit <small>(improvement)</small></h3>"
        "<p>Submitting a Due card now locks its buttons and shows a "
        "spinner plus a <code>Working...</code> status line within the "
        "form, so latency never invites a double click: one "
        f"<code>{ms}ms</code>-per-cycle CSS spin on "
        "<code>.gw-spinner</code> (continuous rotation, gated under "
        "<code>prefers-reduced-motion</code> to a static ring plus text), "
        "with the submit itself untouched so grading, "
        "<code>groundwork/collapse.py</code>, and draft-clearing all run "
        "as today. <code>groundwork/optimistic.py</code> provides "
        "<code>optimistic_js()</code> (submit guard, no dependencies) "
        "and <code>optimistic_css()</code> (raw declarations only, no "
        "<code>&lt;style&gt;</code> tags — the parent concatenates it into "
        "the head wire); helpers fail closed, never raise.</p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "optimistic-submit",
        "kind": "improvement",
        "title": "Optimistic submit",
        "blurb": "Submit a card and its buttons lock with a spinner and Working status — no double grades while grading runs.",
        "path": "/status",
        "anchor": "status-b12-optimistic",
    }
