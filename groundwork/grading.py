"""Per-type grading disclosures: how each card is judged (I-181).

Every string mirrors the real grader in exercises.grade — self-rating,
normalized match, keyword rubric, or sandbox execution — so learners
trust the verdict before they answer.
"""
from __future__ import annotations

import html

_RUBRIC = ("Your words must cover at least half the key points; "
           "missing points are listed in the feedback.")
_EXEC = ("Your code runs in the sandbox against hidden tests — "
         "all green passes.")


def disclosure(etype: str | int) -> str:
    """One-line grading contract for an exercise type."""
    try:
        t = int(etype)
    except (TypeError, ValueError):
        return "Graded like its exercise family."
    table = {
        1: "Self-graded: rate your recall 0–5 — 3 or higher passes.",
        2: "Every blank must match (spelling normalized, code AST-compared); partial credit per blank.",
        3: "Your signature must match, modulo formatting (AST-compared).",
        4: "Exact file text — pick where it lives.",
        5: _RUBRIC,
        6: _RUBRIC,
        7: "Single choice — exact answer text wins.",
        8: "Your output must equal the sandbox-measured output, run live.",
        9: "Every trace step must match, in order.",
        10: "The call order must match exactly.",
        11: "Reference order wins — or green sandbox tests where harnessed.",
        12: _EXEC,
        13: "The exact buggy line number wins.",
        14: _EXEC,
        16: "Single choice — exact answer text wins.",
        18: "Single choice — exact answer text wins.",
        19: _EXEC,
        20: "The optional parameter must exist (AST-checked) and old tests must stay green.",
        21: "Name the bad line, and cover at least half the key points.",
        22: "First letter picks the version; reasons stay on record.",
        23: _EXEC,
        24: _RUBRIC,
        25: _RUBRIC,
        30: "Every pair must match; partial credit per pair.",
    }
    return table.get(t, "Graded like its exercise family.")


def disclosure_html(etype: str | int) -> str:
    """Collapsible grading contract shown before answering."""
    return ("<details><summary>How grading works</summary>"
            f"<p><small>{html.escape(disclosure(etype))}</small></p></details>")
