"""Changelog-entry exercise (type 43, F-20, bloom: create).

The learner writes a keep-a-changelog style entry for the concept:
a section header (Added/Changed/Fixed) plus one user-impact line
saying what a user can now do differently, naming the concept.
Grading is a deterministic prose rubric — no execution, no sandbox.
Stdlib only (``html``/``re``), import-safe standalone: no groundwork imports.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); see ===WIRES===.
"""
from __future__ import annotations

import html
import re

TYPE_NUM = 43
TYPE_NAME = "changelog-entry"
BLOOM = "create"

SECTIONS = ("Added", "Changed", "Fixed")

_FIXED_CUES = ("fix", "bug", "error", "patch", "correct", "crash")
_CHANGED_CUES = ("refactor", "chang", "updat", "renam", "mov", "deprecat",
                 "speed", "fast", "slow", "perf", "optim", "improv")
_IMPACT_WORDS = ("add", "fix", "change", "improve", "support", "remove",
                 "deprecate", "fast", "slow", "now", "you", "user",
                 "no longer", "instead", "can")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _pick_section(name: str, code: str) -> str:
    blob = f"{name}\n{code}".lower()
    if any(c in blob for c in _FIXED_CUES):
        return "Fixed"
    if any(c in blob for c in _CHANGED_CUES):
        return "Changed"
    return "Added"


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a changelog-entry card: section header + user-impact line."""
    ctx = ctx or {}
    snippet = list(snippet or [])
    code = str(ctx.get("runnable") or "\n".join(snippet) or "")
    name = _concept_field(concept, "name", "func") or "func"
    kind = _concept_field(concept, "kind", "function")
    file = _concept_field(concept, "file")
    try:
        line = int(getattr(concept, "line", 0) or 0)
    except (TypeError, ValueError):
        line = 0
    commit = str(ctx.get("commit", "") or "")
    section = _pick_section(name, code)
    where = f" in {file}" if file else ""
    front = (
        f"Write a keep-a-changelog entry for `{name}` ({kind}{where}).\n"
        f"1. Put it under the section header `### {section}`.\n"
        f"2. Add one user-impact line: what can a user now do differently "
        f"because of `{name}`? Name `{name}` explicitly.\n"
        f"Reply with the header line plus your one-line entry.")
    back = (f"### {section}\n- `{name}` now lets users do more with "
            f"{kind}{where} "
            f"(model entry — any line under `### {section}` that states "
            f"the user-visible change and names `{name}` counts).")
    hints = [
        f"Section is `### {section}` — copy that header line exactly.",
        f"Impact line must name `{name}` and say what changed for the user.",
        "One line is enough: start it with `- ` and keep it user-facing.",
    ]
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
        "concept_id": _concept_field(concept, "node_id", name),
        "concept": name, "file": file, "line": line, "commit": commit,
        "hints": hints, "front": front, "back": back,
        "payload": {"section": section, "keyword": name, "grounded": True},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _keyword_ok(keyword: str, text: str) -> bool:
    # Full normalized keyword first ("fetch_user"); otherwise EVERY
    # significant token must appear ("fetch user" still names it, but
    # a lone "user" does not — any() here would pass concept-fragments).
    norm = re.sub(r"\W+", " ", text.lower())
    want = re.sub(r"\W+", " ", keyword.lower()).strip()
    if want and want in norm:
        return True
    toks = [tok for tok in want.split() if len(tok) >= 4]
    return bool(toks) and all(tok in norm for tok in toks)


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Deterministic rubric: right section, user-impact line, concept keyword.

    3 points, all required to pass; partial credit recorded. ``runner``
    accepted for API symmetry and ignored. Never raises.
    """
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {})
        section = str(payload.get("section", "") or "")
        keyword = str(payload.get("keyword", "") or "")
        text = str(submission or "").strip()
        if not text:
            return _fail("Submit a `###` section header plus one impact line.")
        low = text.lower()
        earned, total, missing = 0, 3, []
        if section and section.lower() in low:
            earned += 1
        else:
            missing.append(f"header should be `### {section or 'Added|Changed|Fixed'}`")
        body = "\n".join(l for l in text.splitlines()
                         if l.strip() and not l.strip().startswith("#"))
        words = re.findall(r"[A-Za-z']+", body)
        if len(words) >= 6 and any(w in low for w in _IMPACT_WORDS):
            earned += 1
        else:
            missing.append("impact line must state the user-visible change (6+ words)")
        if keyword and _keyword_ok(keyword, text):
            earned += 1
        else:
            missing.append(f"impact line must name `{keyword or 'the concept'}`")
        score = earned / total
        detail = f"{earned}/{total} rubric points."
        if earned == total:
            return {"pass": True, "score": 1.0,
                    "feedback": f"Entry accepted. {detail}"}
        return {"pass": False, "score": score,
                "feedback": f"Not yet. {detail} Fix: {'; '.join(missing)[:200]}."}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit header + one line.")


def render(exercise: dict) -> str:
    """Exercise widget: prompt plus a textarea seeded with the `###` header."""
    payload = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    seed = html.escape(f"### {payload.get('section', 'Added')}\n- `{exercise.get('concept', '')}` ")
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Rubric: the right `### Added|Changed|Fixed` header, one "
        f"user-impact line (6+ words stating what changed for the user), "
        f"and the concept named. All 3 points required; partial credit "
        f"recorded, no sandbox.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='70'>{seed}</textarea>"
        f"<br><button>Check entry</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b8-changelog'>Changelog entry <small>(feature)</small></h3>"
        "<p>Write a keep-a-changelog entry — pick Added/Changed/Fixed and "
        "state the user-visible impact naming the concept. Graded by "
        "deterministic rubric with partial credit, no sandbox. "
        "<code>groundwork/changelog.py</code>.</p>"
    )
