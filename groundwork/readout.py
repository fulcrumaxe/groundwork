"""Code-reading-aloud mode: speech synthesis for walkthroughs (I-138).

Walkthrough steps (replay blocks) gain a Listen button that reads
the current step aloud via the Web Speech API. Progressive
enhancement all the way down: without JS the page is byte-identical
(the script wire is the only server change), and without
speechSynthesis the script injects nothing. The script cancels any
ongoing speech before starting, and a second click stops. Pure
string emitters, stdlib only; never raises.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b22-readout"

BUTTON_CLASS = "readaloud"
BUTTON_LABEL = "Listen to this step"


def sample_button_html() -> str:
    """The exact button the script injects; doubles as the demo sample."""
    return (f"<button class='{BUTTON_CLASS}' type='button'>"
            f"{BUTTON_LABEL}</button>")


def script_js() -> str:
    """Page wire: Listen buttons on every replay block, speech-guarded."""
    return (
        "<script data-readaloud>"
        "(function(){try{"
        "if(!('speechSynthesis' in window))return;"
        "function speak(t){try{"
        "if(window.speechSynthesis.speaking){window.speechSynthesis.cancel();return;}"
        "window.speechSynthesis.cancel();"
        "window.speechSynthesis.speak(new SpeechSynthesisUtterance(t));"
        "}catch(e){}}"
        "document.querySelectorAll('.replay').forEach(function(box){"
        "if(box.querySelector('." + BUTTON_CLASS + "'))return;"
        "var b=document.createElement('button');"
        "b.className='" + BUTTON_CLASS + "';b.type='button';"
        "b.textContent='" + BUTTON_LABEL + "';"
        "b.addEventListener('click',function(){"
        "var rows=box.querySelectorAll('table tr');"
        "if(rows.length<2)return;"
        "speak(rows[rows.length-1].textContent);});"
        "var h=box.querySelector('h5');"
        "if(h&&h.parentNode){h.parentNode.insertBefore(b,h.nextSibling);}"
        "else{box.insertBefore(b,box.firstChild);}});"
        "}catch(e){}})</script>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Reading aloud "
            "<small>(improvement)</small></h3>"
            "<p>Walkthrough steps that speak — "
            "<code>groundwork/readout.py</code> wires one page script "
            "that injects a Listen button into every replay block "
            "(speechSynthesis, click toggles stop); no JS or no speech "
            "support means the page renders exactly as before. The "
            "injected button looks like this: "
            f"{sample_button_html()}</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Reading aloud</h3>"
                "<p>Read-aloud help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "reading-aloud",
        "kind": "improvement",
        "title": "Reading aloud",
        "blurb": ("Walkthrough steps grow a Listen button — the trace, "
                  "spoken."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
