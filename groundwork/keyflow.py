"""Full keyboard answer-rate-advance flow (I-200).

The review loop is answer -> rate confidence -> advance. Three steps
already work from the keyboard: autofocus parks the cursor in the
answer field, Ctrl+Enter submits, and the confidence radios move with
arrow keys. This module owns only the two missing links:

* rate-in-place: Alt+1..Alt+5 checks the confidence radio inside the
  focused card's form without moving focus out of the answer field;
* advance: n (or Enter on non-interactive focus) follows the result
  screen's Continue link, found as the first ``a.btn`` at/after
  ``#verdict`` -- a signal that exists only on the result screen.

Boundary (no overlap by construction): ``autofocus.py`` owns queue
answer-field focus; ``scrollpos.py`` owns return-to-queue position;
``autoscroll.py`` owns result-verdict focus; ``shortcuts.py`` owns
g-sequences and the ? overlay; ``web.GLOBAL_JS`` + ``runkey.py`` own
submit; ``confslider.py`` owns the radio renderer. Rate needs Alt so
bare digits keep typing answers; advance needs ``#verdict`` so queue
pages keep native Enter. Without this script the legacy path still
works: Tab/arrows/Enter reach every control natively.

Pure functions only: web.py embeds the returned string (see WIRES).
No I/O, no DB/schema changes, stdlib only.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b29-keyflow"
SCRIPT_MARKER = "data-keyflow"
RATE_HINT = "Alt+1-5 rates confidence"
NEXT_HINT = "Press n to continue"

# WIRES: parent embeds ``flow_js()`` once in ``page()``'s global foot
#   scripts (``groundwork/web.py`` foot line, same-line join next to
#   ``autofocusmod.focus_js()``) with the import folded onto the
#   kids/known line (same-line join). One wire covers
#   queue pages (rate-in-place + hints) and the result screen
#   (advance + hint); no cards.py / results.py edits needed.

_JS = """(function(){
if(window.__keyflowInit)return;window.__keyflowInit=true;
function typing(t){if(!t)return false;var g=(t.tagName||"").toLowerCase();if(g==="input"||g==="textarea"||g==="select")return true;return !!(t.isContentEditable);}
function live(t){if(!t||!t.tagName)return false;var g=t.tagName.toLowerCase();return g==="a"||g==="button"||g==="summary"||g==="select";}
function nextLink(){var v=document.getElementById("verdict");if(!v)return null;var list=document.querySelectorAll("main a.btn[href]");if(!list.length)return null;if(!v.compareDocumentPosition)return list[0];for(var i=0;i<list.length;i++){try{if(v.compareDocumentPosition(list[i])&4)return list[i];}catch(e){return list[0];}}return null;}
document.addEventListener("keydown",function(e){
var t=e.target||null;var k=e.key||"";
if(e.altKey&&!e.ctrlKey&&!e.metaKey&&k>="1"&&k<="5"){
var f=t&&t.closest?t.closest("form[action^='/cards/']"):null;
if(!f)return;
var r=f.querySelector("input[name='confidence'][value='"+k+"']");
if(!r)return;
e.preventDefault();r.checked=true;
try{r.dispatchEvent(new Event("change",{bubbles:true}));}catch(x){}
return;}
if(e.ctrlKey||e.metaKey||e.altKey)return;
if(typing(t))return;
var adv=null;
if(k==="n"){adv=nextLink();}
else if(k==="Enter"&&!live(t)){adv=nextLink();}
else{return;}
if(adv){e.preventDefault();adv.click();}
});
function hints(){
Array.prototype.forEach.call(document.querySelectorAll("form[action^='/cards/'] fieldset.confslider"),function(fs){
if(fs.getAttribute("data-keyflow-hint"))return;
fs.setAttribute("data-keyflow-hint","1");
fs.insertAdjacentHTML("afterend","<small data-keyflow-hint>@RATE@</small>");});
var a=nextLink();
if(a&&!a.getAttribute("data-keyflow-hint")){a.setAttribute("data-keyflow-hint","1");a.insertAdjacentHTML("afterend"," <small data-keyflow-hint>@NEXT@</small>");}}
if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",hints);}else{hints();}
})();"""


def flow_js() -> str:
    """One global handler: Alt+1..5 rates, n/Enter advances, hints.

    Alt+digits act only inside a card-review form (header search and
    chrome never match); n/Enter act only when ``#verdict`` is present
    (result screen only), never while typing, never with Ctrl/Cmd/Alt
    held, and Enter yields to links, buttons, summaries, and selects.
    Hint lines inject once per target, only while this script runs, so
    no-JS pages never advertise dead keys. Installs exactly once via
    ``window.__keyflowInit``. Never raises (pure string build).
    """
    js = _JS.replace("@RATE@", RATE_HINT).replace("@NEXT@", NEXT_HINT)
    return "<script " + SCRIPT_MARKER + ">" + js + "</script>"


def tour_entry() -> dict:
    """Tour registry entry for the keyboard flow."""
    return {
        "id": "keyboard-flow",
        "kind": "improvement",
        "title": "Full keyboard answer-rate-advance flow",
        "blurb": ("Answer, rate confidence with Alt+1-5, and continue "
                  "with n -- the whole review loop without the mouse."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }


def section_html() -> str:
    """Anchored status subsection; joined by the batch29 home module."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Full keyboard answer-rate-advance "
        "<small>(improvement)</small></h3>"
        "<p>Type the answer (<code>autofocus</code> parks the cursor, "
        "<code>Ctrl+Enter</code> submits), rate confidence with "
        "<kbd>Alt+1</kbd>-<kbd>Alt+5</kbd> without leaving the answer "
        "field, then press <kbd>n</kbd> (or <kbd>Enter</kbd>) on the "
        "result screen to follow the Continue link. Bare digits keep "
        "typing, native Tab/arrows/Enter keep working, and the hints "
        "render only while the handler is live. "
        "<code>groundwork/keyflow.py</code> embeds once in "
        "<code>page()</code> foot scripts.</p>"
    )
