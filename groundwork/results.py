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
                 origin: str, mod_id: str, due_left: int | None = None) -> str:
    """Result screen: verdict first, explanation, then where to go next."""
    cls = "ok" if passed else "stale"
    verdict = verdictsmod.stamp_html(passed)
    left = (f"<p><small>{due_left} more card{'s' if due_left != 1 else ''} "
            f"due.</small></p>" if due_left else "")
    return (f"<p class='verdict {cls}'>{verdict} — {html.escape(feedback)}</p>"
            f"<details open><summary>Explanation</summary><p>{html.escape(back)}</p></details>"
            f"<p>Next review: {html.escape(next_due)}</p>"
            f"{left}{result_nav(origin, mod_id)}")
