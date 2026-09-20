"""Confirm before leaving a half-answered card (I-29).

Unsaved-textarea guard: a small `beforeunload` script that only fires
when a card form holds non-empty text AND that form was never
submitted (submitted-flag pattern, so real submits are never blocked).

Complement to `answerguard` (I-151), which validates blank input at
submit time: answerguard handles the empty-submit case, this module
handles the typed-then-navigated-away case. No DB/schema changes,
stdlib only (`html`). Web wiring lives in web.py (see WIRES); this
module only builds strings the handler embeds.
"""
from __future__ import annotations

FORM_SELECTOR = "form[action^='/cards/']"


def is_dirty(text) -> bool:
    """True when a textarea value holds non-space text worth keeping."""
    if text is None:
        return False
    if not isinstance(text, str):
        text = str(text)
    return bool(text.strip())


def guard_js() -> str:
    """beforeunload guard: warn only on unsent text, never on submit."""
    return (
        "<script>(function(){"
        "var SUBMITTED='gw-unsaved-submitted';"
        f"var forms=document.querySelectorAll(\"{FORM_SELECTOR}\");"
        "Array.prototype.forEach.call(forms,function(f){"
        "f.addEventListener('submit',function(){"
        "f.setAttribute('data-'+SUBMITTED,'1');});});"
        "window.addEventListener('beforeunload',function(e){"
        "for(var i=0;i<forms.length;i++){"
        "var f=forms[i];"
        "if(f.getAttribute('data-'+SUBMITTED))continue;"
        "var areas=f.querySelectorAll('textarea');"
        "for(var j=0;j<areas.length;j++){"
        "if(areas[j].value&&areas[j].value.replace(/\\s+/g,'')){"
        "e.preventDefault();e.returnValue='';return '';}}}"
        "});})();</script>"
    )


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        "<h2 id='status-b7-unsaved'>Unsaved-answer guard</h2>"
        "<p>Start typing an answer and then navigate away and the "
        "browser asks first: a small <code>beforeunload</code> script "
        "fires only when a card textarea holds unsent text and the "
        "form was never submitted, so real submits and clean "
        "navigation are never blocked. "
        "<code>groundwork/unsaved.py</code>.</p>"
    )
