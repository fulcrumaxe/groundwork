"""Feynman-check drills (type 85, F-81, bloom: explain).

Explain the concept as if to a smart 12-year-old: what it does, why
it exists, one concrete example. Plain words score; jargon costs.
Grading is a machine rubric plus a jargon gate: coverage of the
payload rubric points (case-insensitive substring) with a fixed
jargon budget — over budget halves the score and fails the card.

The jargon list is deliberate academese only (leverage, paradigm,
synergy, …): domain vocabulary the rubric itself requires (function,
loop, call, …) is never penalized, or coverage and clarity would
fight each other.

``generate`` never returns None and never raises: thin input yields an
ungrounded card the pipeline skips.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``jargon_hits(text)``, ``clarity_report(text)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 85),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES) and
``groundwork/__main__.py`` (cmd_e2e fixture); status section and
tour entry live below.
"""
from __future__ import annotations

import html
import re

TYPE_NUM = 85
TYPE_NAME = "feynman-check"
BLOOM = "explain"
STATUS_ANCHOR = "status-b19-feynman"

BUDGET = 2

JARGON = (
    "leverage", "leveraging", "utilize", "utilise", "utilizing",
    "paradigm", "synergy", "synergistic", "synergies", "orthogonal",
    "heuristic", "holistic", "granular", "robust", "scalable",
    "seamless", "ecosystem", "bandwidth", "ideate", "disrupt",
    "disruptive", "actionable", "deliverable", "stakeholder",
    "learnings", "deep dive", "drill down", "move the needle",
    "boil the ocean", "best practice", "touch base",
)

_PLAIN_TIP = {
    "leverage": "use", "leveraging": "using",
    "utilize": "use", "utilise": "use", "utilizing": "using",
    "paradigm": "pattern", "synergy": "teamwork",
    "synergistic": "working together", "synergies": "combined effects",
}


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def jargon_hits(text) -> list[str]:
    """Matched jargon terms, first-seen order, deduped; never raises."""
    try:
        if not isinstance(text, str) or not text:
            return []
        lowered = text.lower()
        hits = []
        for term in JARGON:
            try:
                if " " in term:
                    found = term in lowered
                else:
                    found = re.search(r"\b" + re.escape(term) + r"\b",
                                      lowered) is not None
            except re.error:
                found = False
            if found and term not in hits:
                hits.append(term)
        return hits
    except Exception:  # noqa: BLE001 -- scanning never raises
        return []


def clarity_report(text) -> dict:
    """{total_words, jargon_words, hits, plain_ratio}; never raises."""
    try:
        words = str(text or "").split() if isinstance(text, str) else []
        hits = jargon_hits(text)
        total = len(words)
        count = sum(len(str(h).split()) for h in hits)
        ratio = 1.0 - count / max(1, total)
        return {"total_words": total, "jargon_words": count,
                "hits": hits, "plain_ratio": round(ratio, 3)}
    except Exception:  # noqa: BLE001
        return {"total_words": 0, "jargon_words": 0,
                "hits": [], "plain_ratio": 1.0}


def _rubric(concept, graph) -> list[str]:
    try:
        words = [_concept_field(concept, "name", ""),
                 _concept_field(concept, "kind", "")]
        file = _concept_field(concept, "file", "")
        if file:
            words.append(file.rsplit("/", 1)[-1])
        try:
            edges = list(getattr(graph, "edges", []) or [])
            node_id = _concept_field(concept, "node_id", "")
            name = _concept_field(concept, "name", "")
            for s, d, k in edges:
                if k != "calls":
                    continue
                other = s if d in (node_id, name) else ""
                if other and other != node_id and other not in words:
                    try:
                        node = (graph.nodes or {}).get(other)
                        label = getattr(node, "name", "") if node else ""
                        words.append(str(label or other))
                    except Exception:  # noqa: BLE001
                        words.append(str(other))
                if len(words) >= 5:
                    break
        except Exception:  # noqa: BLE001 -- neighbours never raise
            pass
        return [w.lower() for w in words if w][:5] or ["code"]
    except Exception:  # noqa: BLE001
        return ["code"]


def _hints() -> list[str]:
    return [
        "Pretend the reader is twelve and smart — no jargon allowed.",
        "Say what it does, why it exists, and give one example.",
        "Read it back: every hard word costs you.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a Feynman-check card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        node_id = _concept_field(concept, "node_id", name)
        file = _concept_field(concept, "file", "") or "app.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        if not name or not snippet:
            return _ungrounded(ex_id, name, file, line, commit)
        code = "\n".join(str(l) for l in snippet)[:600]
        rubric = _rubric(concept, ctx.get("graph"))
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": node_id or "feynman",
            "concept": name, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": (f"Explain `{name}` as if to a smart 12-year-old: "
                      "what it does, why it exists, one concrete example. "
                      f"Plain words score; jargon costs (budget: {BUDGET}).\n"
                      f"```python\n{code}\n```"),
            "back": ("Key points: " + "; ".join(rubric) +
                     ". Plain-words tip: say it simply first."),
            "payload": {"rubric": rubric, "jargon": sorted(JARGON),
                        "budget": BUDGET, "grounded": True},
        }
    except Exception:
        return _ungrounded(ex_id, "", "app.py", 0, "")


def _ungrounded(ex_id, name, file, line, commit) -> dict:
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": "feynman",
        "concept": name or "feynman", "file": file, "line": line,
        "commit": commit, "hints": _hints(),
        "front": "Explain this simply. (No concept found — skipped.)",
        "back": "No concept recorded — skipped by the pipeline.",
        "payload": {"rubric": [], "jargon": sorted(JARGON),
                    "budget": BUDGET, "grounded": False},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Rubric coverage gated by the jargon budget; no sandbox."""
    _ = runner
    try:
        return _grade(exercise, submission)
    except Exception as exc:  # noqa: BLE001 -- grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    rubric = [str(w).lower() for w in (p.get("rubric", []) or []) if w]
    try:
        budget = int(p.get("budget", BUDGET))
    except (TypeError, ValueError):
        budget = BUDGET
    text = str(submission if submission is not None else "")
    if not text.strip():
        return _fail("Say it plainly first — one sentence a 12-year-old "
                     "would follow.")
    if not rubric:
        return _fail("No key points recorded on this card.")
    lowered = text.lower()
    hits = [w for w in rubric if w in lowered]
    coverage = len(hits) / len(rubric)
    over = jargon_hits(text)
    too_many = len(over) > budget
    score = round(coverage * (0.5 if too_many else 1.0), 3)
    if coverage >= 0.5 and not too_many:
        return {"pass": True, "score": score,
                "feedback": "Plain and complete — Feynman nods."}
    bits = []
    missing = [w for w in rubric if w not in hits]
    if missing:
        bits.append("missing points: " + ", ".join(missing[:4]))
    if too_many:
        swaps = [f"{j}→{_PLAIN_TIP[j]}" for j in over if j in _PLAIN_TIP]
        bits.append("jargon over budget: " + ", ".join(over[:4]) +
                    (f" (try: {', '.join(swaps[:3])})" if swaps else ""))
    return {"pass": False, "score": score,
            "feedback": "Not yet plain — " + "; ".join(bits) if bits else "No overlap."}


def render(exercise: dict) -> str:
    """Exercise widget: prompt, textarea, live budget line."""
    p = (exercise or {}).get("payload", {}) or {}
    try:
        budget = int(p.get("budget", BUDGET))
    except (TypeError, ValueError):
        budget = BUDGET
    front = html.escape(str(exercise.get("front", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{type_name}</h3>"
        f"<p>{front}</p>"
        f"<p><small>Plain-words budget: ≤{budget} jargon terms.</small></p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Cover half the key points in plain words — jargon "
        f"over budget halves the score and fails the card.</small></p>"
        f"</details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='70' "
        f"placeholder='Explain it simply…'></textarea><br>"
        f"<button>Explain simply</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Feynman check <small>(feature)</small></h3>"
        "<p>Explain it like the reader is twelve — rubric coverage gated "
        "by a jargon budget. <code>groundwork/feynman.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "feynman-check", "kind": "feature",
            "title": "Feynman check",
            "blurb": "Explain it simply — rubric coverage gated by a jargon budget.",
            "path": "/due", "anchor": "up-next"}
