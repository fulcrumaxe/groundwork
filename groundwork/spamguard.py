"""One submit per card per 5s: double-click guard (I-199).

Double clicks, Enter-key repeats, and instant retries can grade the
same card twice: ``optimistic`` only changes presentation (it never
cancels the submit event) and ``collapse`` only swallows submits while
its fetch is in flight -- and only when ``fetch`` exists at all. This
module owns ONLY the time throttle closing that hole: one ``submit``
listener per card-review form stamps the card id with ``Date.now()``,
and a second submit for the same card within WINDOW_MS (5s) is
cancelled with ``preventDefault`` plus a short ``role='status'`` note.
The first submit always proceeds untouched.

The throttle key is the card id parsed from the form's own action
(``/cards/<id>/review``), so the answer form and the give-up form that
``cards.answer_widget`` emits share one budget: answering and then
instantly giving up counts as the same card. Like its siblings it
never calls ``stopPropagation``/``stopImmediatePropagation`` and never
touches ``fetch``/``localStorage``/``sessionStorage``, so the
collapse, draft-clear, and unsaved listeners keep working unchanged;
without JS the forms submit normally (progressive enhancement).

``guard_css()`` returns raw CSS declarations only, never ``<style>``
tags -- the parent concatenates it into the head wire next to
``optimistic_css()``. The throttle note is static text with no
animation, so it is reduced-motion safe by construction. Pure
functions, stdlib only (``re``), no I/O, no DB/schema changes.
"""
from __future__ import annotations

import re

#: Queue-card review forms only. Same as ``collapse.FORM_SELECTOR`` /
#: ``optimistic.FORM_SELECTOR``: the ``[action$='/review']`` tail keeps
#: snooze forms (``/cards/<id>/snooze``) out while covering both forms
#: ``cards.answer_widget`` emits (answer + give-up, both POST review).
FORM_SELECTOR = "form[action^='/cards/'][action$='/review']"

SCRIPT_MARKER = "data-spamguard-throttle"
STATUS_ANCHOR = "status-b29-spamguard"

NOTE_CLASS = "gw-throttle"
STATUS_TEXT = "Already submitted - wait a moment."
#: Same text as STATUS_TEXT with the dash JS-escaped for the snippet.
NOTE_JS = "Already submitted - wait a moment."

#: JS regex source parsing the card id out of a review-form action.
_CARD_RE_JS = r"/\/cards\/([^\/]+)\/review/"

#: One submit per card per window. Clamp range for ``window_ms()``:
#: under a second the guard misfires on slow input methods; over half
#: a minute it strands legitimate retries.
WINDOW_MS = 5000
WINDOW_S = 5
MIN_WINDOW_MS = 1000
MAX_WINDOW_MS = 30000


def form_selector(extra=None) -> str:
    """CSS selector for card-review forms, with one optional prepend.

    Same bracket-scoped quote rule as ``optimistic.form_selector``:
    ``extra`` must not contain ``<>`` or backticks, its brackets must
    balance, and quotes may only sit inside ``[...]`` attribute
    brackets -- stray quotes outside brackets fall back to the
    default. Never raises.
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

    Same shape as ``optimistic._js_string``.
    """
    try:
        if not isinstance(value, str) or not value:
            value = FORM_SELECTOR
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    except Exception:  # noqa: BLE001 -- literal builder must never raise
        return '"' + FORM_SELECTOR + '"'


def window_ms(value=WINDOW_MS) -> int:
    """Clamped throttle window in ms (MIN_WINDOW_MS..MAX_WINDOW_MS).

    Non-numeric or out-of-range input fails closed to WINDOW_MS;
    never raises.
    """
    try:
        v = int(value)
        if v < MIN_WINDOW_MS or v > MAX_WINDOW_MS:
            return WINDOW_MS
        return v
    except Exception:  # noqa: BLE001 -- window lookup must never raise
        return WINDOW_MS


def guard_js(selector=None, window=None) -> str:
    """Per-card 5s throttle: cancel a repeat submit inside the window.

    One ``submit`` listener per review form. The handler parses the
    card id from the form action, stamps ``Date.now()`` on the first
    submit (which proceeds untouched), and ``preventDefault``s any
    second submit for the same card within the window, appending one
    reusable ``role='status'`` note. No ``stopPropagation``, no
    ``fetch``/storage touches, so collapse, draft-clear, and unsaved
    listeners all still run; without ``querySelectorAll``/``Date.now``
    the snippet returns early and the form submits normally.
    Non-string/empty ``selector`` and bad ``window`` fall back to the
    defaults; never raises at build time.
    """
    try:
        sel = form_selector(selector) if selector is not None else FORM_SELECTOR
        lit = _js_string(sel)
    except Exception:  # noqa: BLE001 -- guard snippet must never raise
        lit = _js_string(FORM_SELECTOR)
    try:
        ms = window_ms(window) if window is not None else WINDOW_MS
    except Exception:  # noqa: BLE001 -- guard snippet must never raise
        ms = WINDOW_MS
    try:
        return (
            "<script " + SCRIPT_MARKER + ">"
            "(function(){"
            "if(!document.querySelectorAll||!Date.now)return;"
            "var SEL=" + lit + ";"
            "var WINDOW=" + str(ms) + ";"
            "var last={};"
            "function key(f){"
            "try{var a=f.getAttribute(\"action\")||\"\";"
            "var m=a.match(" + _CARD_RE_JS + ");"
            "return m?m[1]:a;}catch(e){return \"?\";}}"
            "function note(f){"
            "try{"
            "if(f.querySelector(\"." + NOTE_CLASS + "\"))return;"
            "var t=document.createElement(\"span\");"
            "t.className=\"" + NOTE_CLASS + "\";"
            "t.setAttribute(\"role\",\"status\");"
            "t.textContent=\"" + NOTE_JS + "\";"
            "f.appendChild(t);"
            "}catch(e){}}"
            "Array.prototype.forEach.call(document.querySelectorAll(SEL),"
            "function(f){f.addEventListener(\"submit\","
            "function(e){try{"
            "var k=key(f);var now=Date.now();"
            "if(last[k]&&(now-last[k])<WINDOW){"
            "e.preventDefault();note(f);return;}"
            "last[k]=now;"
            "}catch(err){}});});"
            "})();</script>"
        )
    except Exception:  # noqa: BLE001 -- guard snippet must never raise
        return "<script " + SCRIPT_MARKER + "></script>"


def guard_css() -> str:
    """Raw CSS declarations for the throttle note (static, no motion).

    Never emits ``<style>`` tags; the parent wires this into the head
    stylesheet. Never raises.
    """
    try:
        return (
            "." + NOTE_CLASS + "{font-size:.85rem;margin-left:.4rem;color:#666}"
        )
    except Exception:  # noqa: BLE001 -- CSS emitter must never raise
        return ".gw-throttle{font-size:.85rem;margin-left:.4rem;color:#666}"


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
        ms = window_ms()
    except Exception:  # noqa: BLE001 -- status must never raise
        ms = WINDOW_MS
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Double-submit guard <small>(improvement)</small></h3>"
        "<p>Each card now allows one submit per "
        f"<code>{ms}ms</code> window, keyed by the card id in the review "
        "form's own action: a repeat within the window is cancelled with "
        "a short status note, while the first submit always proceeds "
        "untouched. Bubble-phase only -- no propagation stop, no "
        "<code>fetch</code> or storage touches -- so collapse, "
        "draft-clearing, and no-JS plain submits behave exactly as today. "
        "<code>groundwork/spamguard.py</code> provides "
        "<code>guard_js()</code> (per-card timestamp throttle) and "
        "<code>guard_css()</code> (raw declarations only, no "
        "<code>&lt;style&gt;</code> tags -- the parent concatenates it into "
        "the head wire); helpers fail closed, never raise.</p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "double-submit-guard",
        "kind": "improvement",
        "title": "Double-submit guard",
        "blurb": "One submit per card per 5 seconds: rapid repeats are cancelled with a status note, first submits always go through.",
        "path": "/status",
        "anchor": "status-b29-spamguard",
    }
