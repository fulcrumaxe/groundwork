"""Rubber-duck drills (type 83, F-79, bloom: explain).

The card stages a patient-bot Socratic loop. The front shows the
concept's code plus exactly three duck questions the bot "asks"
(fixed, deterministic, derived from the concept — never generated
prose): what it does in one sentence, one concrete input-output
walk-through, and what breaks if a key line were removed. The learner
answers all three in one box. The duck only asks questions — it never
explains, and neither does the card.

Grading is a keyword-coverage half-bar (same family contract as types
5/6/24/25): pass iff the submission covers at least half the rubric
keywords; feedback names the thinnest question and lists missing
points.

``generate`` never returns None and never raises: thin input yields an
ungrounded card the pipeline skips.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``,
``disclosure() -> str`` (contract also copied into the grading table).
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 83),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES) and
``groundwork/__main__.py`` (cmd_e2e fixture); status section and
tour entry live below.
"""
from __future__ import annotations

import html

TYPE_NUM = 83
TYPE_NAME = "rubber-duck"
BLOOM = "explain"
STATUS_ANCHOR = "status-b19-rubberduck"

QUESTIONS = (
    "Q1 — What does it do, in one sentence?",
    "Q2 — Show one concrete input → output (or call → effect) walk-through.",
    "Q3 — What breaks, or what changes, if one key line or branch were removed?",
)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _relatives(graph, node_id: str, name: str) -> list[str]:
    """Up to 2 neighbour display names; never raises."""
    try:
        if graph is None:
            return []
        edges = list(getattr(graph, "edges", []) or [])
        found = []
        for s, d, k in edges:
            if k != "calls":
                continue
            other = s if d in (node_id, name) else (d if s == node_id else "")
            if other and other != node_id and other not in found:
                try:
                    node = (graph.nodes or {}).get(other)
                    label = getattr(node, "name", "") if node is not None else ""
                    found.append(str(label or other))
                except Exception:  # noqa: BLE001 -- label never raises
                    found.append(str(other))
            if len(found) >= 2:
                break
        return found
    except Exception:  # noqa: BLE001
        return []


def _rubric(concept, graph) -> list[str]:
    try:
        name = _concept_field(concept, "name", "")
        kind = _concept_field(concept, "kind", "")
        file = _concept_field(concept, "file", "")
        base = file.rsplit("/", 1)[-1] if file else ""
        words = [w for w in (name, kind, base) if w]
        words += [w for w in _relatives(
            graph, _concept_field(concept, "node_id", name), name)
            if w and w not in words]
        return [w.lower() for w in words if w][:5] or ["code"]
    except Exception:  # noqa: BLE001
        return ["code"]


def _hints() -> list[str]:
    return [
        "Answer Q1 first — one sentence forces the essence out.",
        "Q2 must be concrete: real input, real output.",
        "For Q3, pick the line you understand least and test it.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a rubber-duck card; never None, never raises."""
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
        questions = [f"{q}" for q in QUESTIONS]
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": node_id or "rubberduck",
            "concept": name, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": (f"Explain `{name}` to the duck — it only asks "
                      "questions:\n" + "\n".join(questions) +
                      f"\n```python\n{code}\n```"),
            "back": ("The duck accepts any complete explanation covering: "
                     + ", ".join(rubric)),
            "payload": {"questions": list(questions), "rubric": rubric,
                        "code": code, "grounded": True},
        }
    except Exception:
        return _ungrounded(ex_id, "", "app.py", 0, "")


def _ungrounded(ex_id, name, file, line, commit) -> dict:
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": "rubberduck",
        "concept": name or "rubberduck", "file": file, "line": line,
        "commit": commit, "hints": _hints(),
        "front": "Explain this to the duck. (Nothing to explain found.)",
        "back": "No concept recorded — skipped by the pipeline.",
        "payload": {"questions": list(QUESTIONS), "rubric": [],
                    "code": "", "grounded": False},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Keyword-coverage half-bar; the duck only asks, never explains."""
    _ = runner
    try:
        return _grade(exercise, submission)
    except Exception as exc:  # noqa: BLE001 -- grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    rubric = [str(w).lower() for w in (p.get("rubric", []) or []) if w]
    text = str(submission if submission is not None else "")
    if not text.strip():
        return _fail("The duck is still waiting — it only asks questions, "
                     "so the explaining is yours. Answer all three above.")
    if not rubric:
        return _fail("No key points recorded on this card.")
    lowered = text.lower()
    hits = [w for w in rubric if w in lowered]
    score = len(hits) / len(rubric)
    if score >= 0.5:
        return {"pass": True, "score": round(score, 2),
                "feedback": "The duck nods — key points covered."}
    missing = [w for w in rubric if w not in hits]
    return {"pass": False, "score": round(score, 2),
            "feedback": ("Thinnest answer so far — still missing: "
                         + ", ".join(missing[:4]))}


def disclosure() -> str:
    """One-line grading contract (also copied into the grading table)."""
    return ("Answer the duck's three questions — cover at least half the "
            "key points; the thinnest answer is named in the feedback.")


def render(exercise: dict) -> str:
    """Exercise widget: code, three duck questions, one answer box."""
    p = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>{html.escape(disclosure())}</small></p>"
        f"</details>"
        f"<form method='post'><textarea name='answer' rows='8' cols='70' "
        f"placeholder='Q1… Q2… Q3…'></textarea><br>"
        f"<button>Explain to the duck</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Rubber-duck mode <small>(feature)</small></h3>"
        "<p>Explain the concept to a patient bot that only asks questions — "
        "three fixed prompts, keyword half-bar grading. "
        "<code>groundwork/rubberduck.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "rubber-duck", "kind": "feature",
            "title": "Rubber-duck mode",
            "blurb": "Explain it to a patient bot that only asks questions — three prompts, no answers given.",
            "path": "/due", "anchor": "up-next"}
