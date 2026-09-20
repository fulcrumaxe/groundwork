"""Focus a card's answer field when it scrolls into view (I-41).

QUEUE half only. Boundary (no overlap by construction):

* ``scrollpos.py`` (I-14) owns RETURN-to-queue: per-card ``#card-<id>``
  anchors, the hidden origin field, and the ``sessionStorage``
  ``gw-scroll:<path>`` save/restore pair.
* ``autoscroll.py`` (I-30) owns the RESULT screen: the ``id='verdict'``
  anchor plus focus + ``scrollIntoView`` (reduced-motion aware).
* This module owns QUEUE answer-field focus only: when a card article
  scrolls into view, focus its first answer field. It never touches
  ``sessionStorage``, ``gw-scroll`` keys, ``location.hash``,
  ``scrollTo``, or ``scrollIntoView`` — scrolling stays owned by the
  two modules above. Reduced motion is irrelevant (no scrolling), but
  the script must not fight them: focus uses ``preventScroll:true``.

Guards: never steal focus while the user is typing elsewhere
(``document.activeElement`` check, same shape as ``search.py``'s
``/`` hotkey guard); no-op when ``IntersectionObserver`` is missing
rather than guessing visibility; one focus per form.

Pure functions only: web.py embeds the returned strings (see WIRES).
No I/O, no DB/schema changes, stdlib only (``html``).
"""
from __future__ import annotations

import html
import re

SCRIPT_MARKER = "data-autofocus-answer"
STATUS_ANCHOR = "status-b8-autofocus"

# WIRES: parent embeds ``focus_js()`` once per queue-bearing page, in
#   ``page()``'s global foot scripts (``groundwork/web.py`` ~line 288,
#   next to ``scrollposmod.record_js()``) so it covers BOTH the Due
#   queue and module-detail practice cards. The observed targets are
#   the forms emitted by ``cards.answer_widget`` — no edits to those
#   renderers needed. Do NOT embed on the result screen next to
#   ``verdict_js()``: the verdict owns focus there.

#: Default fields worth focusing, in preference order. Covers every
#: shape ``cards.answer_widget`` emits: recall textarea, explanation /
#: code textareas (``name='answer'``), parsons order box
#: (``name='answer_text'``), typed inputs, selects.
FIELD_SELECTOR = (
    "textarea[name='recall'],"
    "textarea[name='answer'],"
    "input[name='answer_text'],"
    "input[name='answer'],"
    "select[name='answer']"
)

#: Queue-card scope: only forms that submit a card review. Mirrors
#: ``unsaved.FORM_SELECTOR`` so practice cards match and site chrome
#: (header search, journal, diagnose) never does.
FORM_SELECTOR = "form[action^='/cards/']"


def field_selector(extra=None) -> str:
    """CSS selector for a card form's focusable answer field.

    ``extra`` prepends one caller-supplied selector (e.g. a pilot
    field name). ``<>`` and backtick are rejected anywhere (they
    break out of the script element); quotes must sit inside
    ``[...]`` attribute brackets — the normal ``name='...'`` shape —
    so stray quotes outside brackets fall back to the default.
    ``_js_string`` still escapes the embedded literal. Never raises.
    """
    if not isinstance(extra, str):
        return FIELD_SELECTOR
    cand = extra.strip()
    if not cand or any(ch in cand for ch in "<>`"):
        return FIELD_SELECTOR
    if cand.count("[") != cand.count("]"):
        return FIELD_SELECTOR
    neb = re.sub(r"\[[^\[\]]*\]", "", cand)
    if any(ch in neb for ch in "\"'"):
        return FIELD_SELECTOR
    return f"{cand},{FIELD_SELECTOR}"


def _js_string(value) -> str:
    """Double-quoted JS string literal for a CSS selector (safe).

    Double quotes keep the common ``name='...'`` selectors byte-identical
    inside the literal; backslash and double-quote are escaped.
    """
    if not isinstance(value, str) or not value:
        value = FIELD_SELECTOR
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def focus_js(selector=None) -> str:
    """Focus each card's answer field as it scrolls into view.

    One ``IntersectionObserver`` watches every ``FORM_SELECTOR`` form;
    when a form becomes visible and the user is not typing elsewhere,
    its first field match takes focus with ``preventScroll:true``
    (never scrolls: no fight with scrollpos/autoscroll). Each form
    focuses at most once (``data-`` flag). No ``sessionStorage``, no
    origin keys, no ``scrollIntoView``. Non-string/empty ``selector``
    falls back to the default; never raises.
    """
    sel = field_selector(selector) if selector is not None else FIELD_SELECTOR
    lit = _js_string(sel)
    forms = _js_string(FORM_SELECTOR)
    return (
        f"<script {SCRIPT_MARKER}>"
        "(function(){"
        "if(!('IntersectionObserver' in window))return;"
        f"var SEL={lit};"
        "function typing(){"
        "var a=document.activeElement;if(!a)return false;"
        "var t=(a.tagName||'').toLowerCase();"
        "if(t==='input'||t==='textarea'||t==='select')return true;"
        "return !!(a.isContentEditable);}"
        "function field(f){try{return f.querySelector(SEL);}catch(e){return null;}}"
        "var seen='gw-autofocus-done';"
        "var obs=new IntersectionObserver(function(entries){"
        "entries.forEach(function(en){"
        "if(!en.isIntersecting)return;"
        "var f=en.target;if(f.getAttribute('data-'+seen))return;"
        "if(typing())return;"
        "var el=field(f);if(!el)return;"
        "try{el.focus({preventScroll:true});}catch(e){try{el.focus();}catch(_){}}"
        "f.setAttribute('data-'+seen,'1');"
        "});},{rootMargin:'0px 0px -20% 0px',threshold:0.35});"
        "Array.prototype.forEach.call(document.querySelectorAll(" + forms + "),"
        "function(f){obs.observe(f);});"
        "})();</script>"
    )


def demo_html() -> str:
    """Minimal queue-card snippet showing the focus target (Status demo)."""
    return (
        "<article id='card-demo'>"
        "<p>What is the capital of France?</p>"
        "<form method='post' action='/cards/demo/review'>"
        "<label>It prints/returns: <input name='answer' size='30'></label> "
        "<button>Check prediction</button></form></article>"
    )


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Answer-field autofocus <small>(improvement)</small></h3>"
        "<p>When a queue card scrolls into view, its answer field takes "
        "focus so typing can start immediately — never while typing "
        "elsewhere, never scrolling the page (scroll position stays "
        "owned by <code>groundwork/scrollpos.py</code>, the verdict by "
        "<code>groundwork/autoscroll.py</code>). "
        "<code>groundwork/autofocus.py</code>.</p>"
    )
