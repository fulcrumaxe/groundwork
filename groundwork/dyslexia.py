"""Dyslexia-friendly type/spacing toggle (I-139).

One header button switches the page to a friendlier reading shape:
roomier line-height, wider letter- and word-spacing, left-aligned
ragged-right text. The density.py shape exactly: ``dyslexia_css()``
returns raw declarations for the head wire (a ``data-dys`` override
referencing only real scale tokens), ``toggle_js`` persists the
choice in ``localStorage`` (no-JS browsers keep the default), and
``toggle_html`` is the header button on every page. Stdlib only,
no I/O, no DB. Never raises.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b22-dyslexia"

STORE_KEY = "gw-dys"
ATTR = "data-dys"
ON = "on"
TOGGLE_ID = "gw-dys-toggle"


def dyslexia_css() -> str:
    """Raw friendlier-reading overrides plus the toggle's own shape."""
    return (
        f"html[{ATTR}='{ON}'] body{{line-height:1.75;letter-spacing:.035em;"
        "word-spacing:.16em;text-align:left}}"
        f"html[{ATTR}='{ON}'] p,html[{ATTR}='{ON}'] li{{max-width:62ch}}"
        f"#{TOGGLE_ID}{{font-size:.8rem;padding:.3rem .6rem;"
        "border:1px solid var(--stale);border-radius:var(--r-control);"
        "background:var(--paper);color:var(--ink);cursor:pointer}")


def toggle_js() -> str:
    """Dyslexia switch: read stored choice, toggle on click, persist.

    Presentation only: no ``fetch``, no cookies, no server round trip.
    Without JS the button does nothing and the default stays on.
    """
    return (
        "<script data-dys-toggle>"
        "(function(){"
        "try{"
        "var root=document.documentElement;"
        "try{if(localStorage.getItem(\"" + STORE_KEY + "\")===\"" + ON + "\")"
        "root.setAttribute(\"" + ATTR + "\",\"" + ON + "\");}catch(e){}"
        "var b=document.getElementById(\"" + TOGGLE_ID + "\");"
        "if(!b||!b.addEventListener)return;"
        "b.addEventListener(\"click\",function(){"
        "var cur=root.getAttribute(\"" + ATTR + "\")===\"" + ON + "\";"
        "try{"
        "if(cur){root.removeAttribute(\"" + ATTR + "\");"
        "localStorage.removeItem(\"" + STORE_KEY + "\");"
        "b.textContent=\"Readable\";}"
        "else{root.setAttribute(\"" + ATTR + "\",\"" + ON + "\");"
        "localStorage.setItem(\"" + STORE_KEY + "\",\"" + ON + "\");"
        "b.textContent=\"Default\";}"
        "}catch(e){}});}catch(e){}"
        "})();</script>")


def toggle_html() -> str:
    """Header button; label names the action, not the state."""
    return (f"<button id='{TOGGLE_ID}' type='button' "
            "title='Toggle dyslexia-friendly reading'>Readable</button>")


def status_section_html() -> str:
    """Status-page subsection: visible home for this item."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Dyslexia-friendly reading "
            "<small>(improvement)</small></h3>"
            "<p>Roomier reading on demand: "
            "<code>groundwork/dyslexia.py</code> provides "
            "<code>dyslexia_css()</code> (a <code>data-dys</code> "
            "override widening line-height, letter- and word-spacing), "
            "<code>toggle_js()</code> (a <code>localStorage</code> switch, "
            "no server round trip), and <code>toggle_html()</code> (the "
            "header button on every page).</p>"
            + toggle_html())
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Dyslexia-friendly reading</h3>"
                "<p>Reading help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "dyslexia-toggle",
        "kind": "improvement",
        "title": "Dyslexia-friendly reading",
        "blurb": ("One header button widens spacing and line-height — "
                  "reading stays comfortable."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
