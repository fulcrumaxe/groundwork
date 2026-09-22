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
        15: "Single choice — exact answer text wins.",
        16: "Single choice — exact answer text wins.",
        17: "Your new name must be snake_case and meaningful; your reason must cover at least half the key points.",
        18: "Single choice — exact answer text wins.",
        19: _EXEC,
        20: "The optional parameter must exist (AST-checked) and old tests must stay green.",
        21: "Name the bad line, and cover at least half the key points.",
        22: "First letter picks the version; reasons stay on record.",
        23: _EXEC,
        24: _RUBRIC,
        25: _RUBRIC,
        26: "Your rewrite must nest less deeply (AST-measured) and keep the hidden tests green.",
        27: "The dependency must arrive as a parameter defaulting to the original, and old tests must stay green.",
        28: _EXEC,
        29: "Logging checklist — every marked line needs the right level; partial credit per line.",
        30: "Every pair must match; partial credit per pair.",
        31: "Every annotation slot must match (spelling-normalized); partial credit per slot.",
        32: "Your >>> example must run green as a doctest, and one example must call the function.",
        33: "Each assert line must hold against the shown code, and one must call the function.",
        34: "Name the exact crashing call or the crashing line — either half counts.",
        35: "Your rewrite must score strictly lower (AST-measured) and keep the hidden tests green.",
        36: "Name the top-allocating line as file:line — exact match.",
        37: "Name the exact shared-state line plus a fix (copy, lock, or parameter).",
        38: "Remove the flagged dead code; the remaining tests must stay green.",
        39: "Magic literals must live in named constants, bodies must not hold them; hidden tests stay green.",
        40: "Every rubric point must hold: exact name, params, defaults, return annotation.",
        41: "Every acceptance point must appear in your criteria; partial credit per point.",
        42: "Imperative subject of 72 chars or fewer naming the what and the why; partial credit per point.",
        43: "The right ### section, one user-impact line naming the concept; partial credit per point.",
        44: "Your script must run and reproduce the reported failure within the line budget.",
        45: "Exact breaking-commit hash or index; off-by-one fails.",
        46: "No markers remain, both sides kept, same def, parses; partial credit per point.",
        47: "Migrated JSON rows must equal the expected rows exactly, old field dropped.",
        48: "Exact step sequence; partial credit per correct adjacent pair.",
        49: "Name at least half the abuse cases — checklist match with partial credit per item.",
        50: "Exact leaked value (quotes/whitespace ignored) or exact line number.",
        51: "Exact unvalidated-input set required; partial credit per correct name.",
        52: "Name every required rule; partial credit per rule, plain words accepted.",
        53: "Exact string set required — every string present, nothing extra.",
        54: "Your pattern must fullmatch every required case and reject every negative case; partial credit per case.",
        55: "Your query must return the spec'd result set on the fixture; order matters only under ORDER BY.",
        56: "Every spec property must be present with a matching value; harmless extras allowed up to 2.",
        57: "Name the single flaw category — exact match after case/separator normalization.",
        58: "Name the exact root-cause phrase — red herrings and pasted logs never count.",
        59: "Reply with the single regressing-graph letter A, B, or C — exact match.",
        60: "Name the dominant frame plus one why-word — both required, exact match.",
        61: "Name the crashing function as an isolated answer plus the fix category — both required.",
        62: "New-API shape present with no old-API shape left — static check, no sandbox.",
        63: "Exact verdict (OK/NOT-OK) plus one reason keyword — both must match.",
        64: "Every build-gate point must hold — pinned base, COPY, matching EXPOSE, exec launch, USER; no partial credit.",
        65: "Every pipeline point must hold — on-push trigger, jobs with steps, run/uses per step, no syntax errors; no partial credit.",
        66: "Flag reference fully removed (name must not appear anywhere), both branches resolved, hidden tests green — static grep gate plus sandbox run.",
        67: "Your backfill function runs in the sandbox over fixture rows — every row migrated with defaults applied and no rows lost passes.",
        68: "Every page slice must match the fixture with a consistent total and stable order; out-of-range pages return empty items — no partial credit.",
        69: "Every invalidation point must be named and no hot path busted — exact set match; no partial credit.",
        70: "Double-run gate: your handler runs twice on the same store with the same key — same end state and no duplicate side effects; a fresh key must still apply; no partial credit.",
        71: "Name scoped limits, a concrete window, burst handling, and 429 + Retry-After with a reason — partial credit per point, half or more passes.",
        72: "All four signature vectors must verify correctly — valid passes, tampered body, wrong secret, and replayed timestamp all rejected; no partial credit.",
        73: "Speak it aloud, then write it down — your words must cover at least half the key points; missing points are listed in the feedback.",
        74: "Your answer on the unfamiliar snippet must equal the sandbox-measured output, run live — no lesson text to lean on.",
        75: "Re-express the pattern in the target language — every listed check must hold; no partial credit.",
        76: "Name the exact root cause within the 90s drill budget — exact phrase (case, quotes, whitespace ignored; listed aliases accepted); herrings, decoy requests, and pasted logs never count.",
        77: "Name the signal, detection, mitigation, and prevention plus the true timeline order — partial credit per point, half or more passes.",
        78: "Name at least half the failure modes — checklist match with partial credit per item.",
        79: "Skim-then-verify: every probe letter must match — all correct passes, partial credit per probe.",
        80: "Predict the purpose from the name — exact choice wins; the docstring on the back is the verify step.",
        81: "Predict the call — exact choice wins; the synopsis and docs pointer on the back are the verify step.",
        82: "Draw the data flow from memory — exact edge set passes, partial credit per correct edge.",
        83: "Answer the duck's three questions — cover at least half the key points; the thinnest answer is named in the feedback.",
    }
    return table.get(t, "Graded like its exercise family.")


def disclosure_html(etype: str | int) -> str:
    """Collapsible grading contract shown before answering."""
    return ("<details><summary>How grading works</summary>"
            f"<p><small>{html.escape(disclosure(etype))}</small></p></details>")
