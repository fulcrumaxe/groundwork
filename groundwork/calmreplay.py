"""Calm walkthrough reveals: instant when reduced-motion is set (I-140).

Stepped replay reveals one trace step per click — interaction as
motion. When the learner prefers reduced motion, the walkthrough
should simply be there: every step visible at once, no stepping.
``instant_html`` renders that full-steps twin (hidden by default);
``script_js`` unhides it and hides the stepper when
``prefers-reduced-motion: reduce`` matches. Without the preference
(or without JS) the stepped block stands alone exactly as before.
Reuses replay.replay_steps so the twin never disagrees with the
stepper. Stdlib only; never raises.
"""
from __future__ import annotations

import html

from . import replay as replaymod

STATUS_ANCHOR = "status-b22-calmreplay"


def instant_html(lesson) -> str:
    """Full-steps table, hidden until the script claims it.

    "" when the lesson has no measured trace, so traceless lessons
    render byte-identical (legacy no-data fallback). Never raises.
    """
    try:
        rows = replaymod.replay_steps(lesson)
        if not rows:
            return ""
        cells = "".join(
            f"<tr><td>{r['step']}</td>"
            f"<td>{html.escape(r['does'])}</td>"
            f"<td>{html.escape(r['state'])}</td></tr>"
            for r in rows)
        return (
            f"<div class='replay-full' id='replay-full' hidden>"
            f"<h5>Full trace — all {len(rows)} steps</h5>"
            "<table class='log'><tr><th>Step</th><th>Does</th>"
            f"<th>State</th></tr>{cells}</table></div>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def script_js() -> str:
    """Page wire: swap the stepper for the full trace on reduced motion."""
    return (
        "<script data-calm-replay>"
        "(function(){try{"
        "var q=window.matchMedia&&window.matchMedia("
        "\"(prefers-reduced-motion: reduce)\");"
        "if(!q||!q.matches)return;"
        "document.querySelectorAll('.replay-full[hidden]').forEach("
        "function(full){"
        "full.removeAttribute('hidden');"
        "var box=full.parentNode&&full.parentNode.querySelector('.replay');"
        "if(box)box.setAttribute('hidden','');});"
        "}catch(e){}})</script>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = instant_html(
            {"worked": {"trace": {"steps": ["1", "3"]}},
             "how": ["Sets total.", "Adds."]})
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Calm walkthrough reveals "
            "<small>(improvement)</small></h3>"
            "<p>Stepping is motion too — "
            "<code>groundwork/calmreplay.py</code> renders a hidden "
            "full-steps twin beside every stepped replay on the lesson "
            "rendering path (<code>lessons.render_levels</code>), and one "
            "page script swaps the stepper for the full trace when "
            "reduced-motion is set. A live sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Calm walkthrough reveals</h3>"
                "<p>Calm-reveal help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "calm-reveals",
        "kind": "improvement",
        "title": "Calm walkthrough reveals",
        "blurb": ("Reduced-motion learners get the whole trace at once "
                  "— no stepping required."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
