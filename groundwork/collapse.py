"""Collapse answered Due cards in place with inline undo (I-42).

After a learner answers a Due card, the card's ``<article>`` collapses
in place to a compact answered state with an inline undo button,
instead of a full page reload to a separate result screen. Grading
and scheduling run unchanged on the server; only the presentation
of the answered card changes.

How it works: ``collapse_js()`` intercepts each card-review form,
POSTs it with ``fetch`` (same body, same route), and on success
hides the article's forms and appends the compact banner shaped by
``collapsed_html()``. The article keeps its ``#card-<id>`` anchor so
deep links still land. No-JS browsers submit normally and get the
current Result page (progressive enhancement).

Boundary -- this module owns ONLY the in-place collapse + inline undo:

* ``scrollpos.py`` owns queue anchors/origin keys; this script never
  reads or writes ``sessionStorage``, ``gw-scroll`` keys, or hashes.
* ``autoscroll.py`` owns the result verdict; this script never parses
  or scrolls to any verdict.
* ``autofocus.py`` owns focus; this script never calls ``focus``.
* ``unsaved.py`` (+ ``GLOBAL_JS`` drafts) owns the submit-listener
  chain; this script lets those listeners run (no propagation stop)
  and never touches ``localStorage`` or ``beforeunload`` itself.

Pure functions only, stdlib only (``html``). No I/O, no DB/schema
changes. Undo reuses the existing ``POST /reviews/undo`` route
(``groundwork/undo.py``, 60-second window).

WIRES (parent; no web.py route/form edits):
1. ``page()`` foot in ``groundwork/web.py`` (~line 282): append
   ``collapsemod.collapse_js()`` after ``autofocusmod.focus_js()``.
2. ``due_html()`` unchanged: ``<article id='card-<id>'>`` + review
   forms already match ``FORM_SELECTOR``; snooze forms do not.
3. ``groundwork/status.py`` Batch 9 group: add
   ``collapsemod.section_html()`` + the tour entry below.
"""
from __future__ import annotations

import html

#: Queue-card review forms only. Narrower than autofocus/unsaved's
#: ``form[action^='/cards/']``: the ``[action$='/review']`` tail keeps
#: snooze forms (``/cards/<id>/snooze``) out while covering both forms
#: ``cards.answer_widget`` emits (answer + give-up, both POST review).
FORM_SELECTOR = "form[action^='/cards/'][action$='/review']"

#: Existing undo route (web.py ``POST /reviews/undo`` -> ``undo.undo``).
UNDO_ACTION = "/reviews/undo"

HISTORY_PATH = "/reviews"
SCRIPT_MARKER = "data-collapse-answered"
STATUS_ANCHOR = "status-b9-collapse"
UNDO_LABEL = "Undo answer"
ANSWERED_TEXT = "\u2713 Answered"


def undo_form_html(label=UNDO_LABEL) -> str:
    """Inline undo form posting to the existing undo route.

    Same shape as ``undo.section_html``'s form but compact: no review
    id is needed because the route always undoes the newest review
    inside its 60-second window. Non-string/blank labels fall back.
    Never raises.
    """
    if not isinstance(label, str) or not label.strip():
        label = UNDO_LABEL
    return (
        f"<form method='post' action='{UNDO_ACTION}'>"
        f"<button>{html.escape(label.strip())}</button></form>"
    )


def collapsed_html(concept="") -> str:
    """Compact answered banner inserted inside the kept article.

    Carries no ``id`` of its own: the surrounding ``<article>`` keeps
    ``#card-<id>`` (owned by scrollpos), so no anchor is minted here.
    Non-string concepts are stringified; markup is escaped. Never raises.
    """
    if concept is None:
        concept = ""
    elif not isinstance(concept, str):
        concept = str(concept)
    head = ANSWERED_TEXT
    if concept.strip():
        head += " \u2014 " + concept.strip()
    return (
        "<div class='collapsed-answer'>"
        f"<p class='ok'>{html.escape(head)}</p>"
        f"{undo_form_html()}"
        f"<p><small><a href='{HISTORY_PATH}'>History</a></small></p></div>"
    )


def collapse_js() -> str:
    """Intercept card-review submits; collapse the article on success.

    ``fetch`` POSTs the untouched form body to the same review route,
    so grading/scheduling behave exactly as today. On ``ok`` the
    article's forms hide and a banner (answered line + undo form +
    history link, built with ``textContent`` so nothing parses HTML)
    is appended; the article element -- and its anchor id -- is never
    removed or renamed. Double submits while busy are swallowed, so
    one answer can never grade twice. Failed POSTs show one inline
    ``stale`` line and re-enable the form. Other ``submit`` listeners
    (draft-clear, unsaved flag) still run: nothing is stopped and no
    storage key is touched here. No ``fetch`` in the browser means no
    interception (plain Result page). Never raises at build time.
    """
    return (
        "<script " + SCRIPT_MARKER + ">"
        "(function(){"
        "if(!('fetch' in window))return;"
        "var SEL=\"" + FORM_SELECTOR + "\";"
        "var UNDO=\"" + UNDO_ACTION + "\";"
        "var HIST=\"" + HISTORY_PATH + "\";"
        "var LBL=\"" + UNDO_LABEL + "\";"
        "var DONE=\"" + ANSWERED_TEXT + "\";"
        "function art(f){if(f.closest)return f.closest('article');"
        "var n=f;while(n&&n.tagName!=='ARTICLE')n=n.parentNode;return n;}"
        "function fail(f){if(f.getAttribute('data-gw-collapse-error'))return;"
        "var p=document.createElement('p');p.className='stale';"
        "p.setAttribute('data-gw-collapse-error','1');"
        "p.textContent='Not saved \u2014 check connection, then submit again.';"
        "f.appendChild(p);}"
        "function done(f){var a=art(f);if(!a)return;"
        "if(a.getAttribute('data-gw-collapsed'))return;"
        "a.setAttribute('data-gw-collapsed','1');"
        "var cur=a.getAttribute('class')||'';"
        "a.setAttribute('class',(cur?cur+' ':'')+'answered');"
        "Array.prototype.forEach.call(a.querySelectorAll('form'),"
        "function(x){x.style.display='none';});"
        "var d=document.createElement('div');d.className='collapsed-answer';"
        "var p=document.createElement('p');p.className='ok';"
        "p.textContent=DONE;d.appendChild(p);"
        "var u=document.createElement('form');u.method='post';u.action=UNDO;"
        "var b=document.createElement('button');b.textContent=LBL;"
        "u.appendChild(b);d.appendChild(u);"
        "var s=document.createElement('p');var h=document.createElement('a');"
        "h.href=HIST;h.textContent='History';s.appendChild(h);"
        "d.appendChild(s);a.appendChild(d);}"
        "Array.prototype.forEach.call(document.querySelectorAll(SEL),"
        "function(f){f.addEventListener('submit',function(e){"
        "if(f.getAttribute('data-gw-busy')){e.preventDefault();return;}"
        "e.preventDefault();f.setAttribute('data-gw-busy','1');"
        "fetch(f.action,{method:'post',body:new FormData(f),"
        "credentials:'same-origin'}).then(function(r){"
        "f.removeAttribute('data-gw-busy');"
        "if(!r.ok)throw new Error('grade');done(f);})"
        ".catch(function(){f.removeAttribute('data-gw-busy');fail(f);});});});"
        "})();</script>"
    )


def demo_html() -> str:
    """Status-page demo: one collapsed card, anchor kept on the article."""
    return (
        "<article id='card-demo'>"
        "<h3>Demo concept</h3>"
        "<p>What is the capital of France?</p>"
        + collapsed_html("Demo concept")
        + "</article>"
    )


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Collapse answered cards <small>(improvement)</small></h3>"
        "<p>Answering a Due card collapses it in place to a compact "
        "answered state with an inline undo button instead of a full "
        "reload: the article keeps its <code>#card-&lt;id&gt;</code> "
        "anchor, grading/scheduling run untouched, and the undo form "
        "reuses <code>POST /reviews/undo</code> (60-second window, "
        "<code>groundwork/undo.py</code>). No DB change. "
        "<code>groundwork/collapse.py</code>.</p>"
    )
