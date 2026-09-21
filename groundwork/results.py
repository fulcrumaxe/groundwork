"""Result-screen renderers: verdict, explanation, onward navigation.

Pure HTML builders — the review POST handler calls these so result UI
never lives in web.py.
"""
from __future__ import annotations

import html

from . import verdicts as verdictsmod


def result_nav(origin: str, mod_id: str) -> str:
    """Never strand: back to origin, module, queue and history."""
    back_link = f"/modules/{mod_id}" if mod_id else "/"
    links = (f"<p><a class='btn' href='{html.escape(origin)}'>"
             f"Continue where you left off</a>")
    if back_link != origin:
        links += f" · <a href='{back_link}'>Back to module</a>"
    links += " · <a href='/due'>Due queue</a> · <a href='/reviews'>History</a></p>"
    return links


def render_result(passed: bool, feedback: str, back: str, next_due: str,
                 origin: str, mod_id: str, due_left: int | None = None,
                 points: int | None = None, drill: str = "") -> str:
    """Result screen: verdict first, explanation, then where to go next.

    ``points`` is the banked confidence-weighted score (Batch 15,
    F-65); None hides the line for pre-points reviews. ``drill`` is
    the settled explicit-odds line (Batch 15, F-66); "" hides it.
    """
    cls = "ok" if passed else "stale"
    verdict = verdictsmod.stamp_html(passed)
    left = (f"<p><small>{due_left} more card{'s' if due_left != 1 else ''} "
            f"due.</small></p>" if due_left else "")
    banked = ""
    try:
        if points is not None:
            banked = (f"<p><small>Calibration banked {int(points):+d} pts "
                      f"(brave-correct earns, bluffing costs).</small></p>")
    except Exception:  # noqa: BLE001 -- display must never raise
        banked = ""
    drill_line = ""
    try:
        if isinstance(drill, str) and drill.strip():
            drill_line = f"<p><small>{html.escape(drill)}</small></p>"
    except Exception:  # noqa: BLE001 -- display must never raise
        drill_line = ""
    return (f"<p class='verdict {cls}'>{verdict} — {html.escape(feedback)}</p>"
            f"<details open><summary>Explanation</summary><p>{html.escape(back)}</p></details>"
            f"<p>Next review: {html.escape(next_due)}</p>{banked}{drill_line}"
            f"{left}{result_nav(origin, mod_id)}")
