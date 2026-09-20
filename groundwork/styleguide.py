"""Component gallery: every UI building block on one page (I-96).

Renders real fragments from the cards/lessons/grading modules beside
their CSS class names, so contributors see what exists before adding
anything new. Dev page, not linked from the main nav.
"""
from __future__ import annotations

from . import cards as cardsmod
from . import grading as gradingmod


def _sample_card() -> dict:
    return {"id": "styleguide", "exercise_type": "8",
            "payload": ('{"choices": ["42", "43"], "expected": "42",'
                        ' "hints": ["Read the loop bound."]}'),
            "stability": 4.0, "difficulty": 0.6, "retrievability": 0.8,
            "due": "2026-01-01T00:00:00Z", "lapses": 1,
            "front": "What does it print?", "concept": "sample"}


def page() -> str:
    """Full gallery body with a stable tour anchor."""
    card = _sample_card()
    widget = cardsmod.answer_widget(card, 0, "/styleguide")
    sections = [
        ("<h2>Chips &amp; status</h2>"
         "<p><span class='chip'>due</span> "
         "<span class='chip stale'>3d overdue</span> "
         "<span class='chip'>new</span> "
         "<span class='chip'>Owned</span> — <code>.chip</code>, "
         "<code>.chip.stale</code></p>"),
        ("<h2>Buttons</h2>"
         "<p><a class='btn' href='/styleguide'>Action link</a> "
         "<button>Real button</button> "
         "<button class='giveup'>Give-up link-button</button> — "
         "<code>a.btn</code>, <code>button</code>, "
         "<code>button.giveup</code></p>"),
        ("<h2>Progress bars</h2>"
         "<div class='bar' aria-hidden='true'>"
         "<i style='width:60%'></i></div> — <code>.bar &gt; i</code>"),
        ("<h2>Difficulty dots</h2>"
         f"<p>{cardsmod._difficulty_dots(0.6)}</p>"),
        ("<h2>Memory strength</h2>"
         f"{cardsmod._memory_bar(card)}"),
        ("<h2>Queue status</h2>"
         f"<p>{cardsmod.status_chip(card, 0)} "
         f"{cardsmod.status_chip(card, 2)}</p>"),
        ("<h2>Confidence pills</h2>"
         f"<p>{cardsmod._confidence()}</p>"),
        ("<h2>Grading contract</h2>"
         f"{gradingmod.disclosure_html(8)}"),
        ("<h2>Answer widget</h2>"
         f"<article>{widget}</article>"),
        ("<h2>Log tables</h2>"
         "<table class='log'><tr><th>Day</th><th>Due</th></tr>"
         "<tr><td>today</td><td>3</td></tr></table> — "
         "<code>table.log</code>"),
    ]
    return ("<div id='styleguide'><p><small>Dev gallery — every "
            "component with its class name.</small></p>"
            + "".join(sections) + "</div>")
