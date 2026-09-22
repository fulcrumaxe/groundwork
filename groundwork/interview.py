"""Mastery interview exercise (type 73, F-69, bloom: evaluate).

Oral-exam mode, simulated: no audio capture exists, so the front invites
the learner to explain the concept aloud (read-aloud prompt) and the
written explanation is graded against a spoken-style rubric (keyword
coverage, rubric family bar: half or more of the key points passes —
same bar as types 5/6/24/25). Static and deterministic, stdlib only.

``gen_mastery_interview`` never returns None and never raises: thin input
yields an ungrounded card the pipeline skips (``grounded: False``).

Plugin API: ``gen_mastery_interview(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 73) and
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES); status section and
tour entry live in ``groundwork/batch18.py``.
"""

from __future__ import annotations

import html

TYPE_NUM = 73
TYPE_NAME = "mastery-interview"
BLOOM = "evaluate"
STATUS_ANCHOR = "status-b18-interview"

_PASS_FRACTION = 0.5


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _relatives(ctx: dict, concept) -> list[str]:
    """Up to 2 graph neighbours (callers + callees), display names only."""
    try:
        graph = ctx.get("graph")
        if graph is None:
            return []
        node_id = _concept_field(concept, "node_id", "")
        name = _concept_field(concept, "name", "")
        rel: list[str] = []
        for s, d, k in graph.edges:
            if k != "calls":
                continue
            if d in (node_id, name) and s != node_id:
                rel.append(s)
            elif s == node_id and d != node_id:
                rel.append(d)
        out: list[str] = []
        for nid in rel:
            node = graph.nodes.get(nid) if graph is not None else None
            disp = (node.name if node is not None and node.name else nid)
            if disp != name and disp not in out:
                out.append(disp)
            if len(out) >= 2:
                break
        return out
    except Exception:  # noqa: BLE001 — rubric must never raise
        return []


def _rubric(concept, ctx: dict) -> list[str]:
    file = _concept_field(concept, "file", "")
    base = file.split("/")[-1] if file else ""
    rubric = [_concept_field(concept, "name", ""),
              _concept_field(concept, "kind", ""), base]
    rubric += _relatives(ctx, concept)
    return [r for r in rubric if r]


def _front_text(name: str, code: str) -> str:
    return (
        f"Mastery interview: read this aloud as if defending `{name}` in an "
        f"oral exam — what it does, why it is shaped this way, what breaks "
        f"without it. Then write down the explanation you just spoke.\n"
        f"```\n{code[:600]}\n```"
    )


def _hints() -> list[str]:
    return [
        "Say it first, then write it: speaking exposes gaps writing hides.",
        "Cover what it does, why this shape, and what breaks without it.",
        "Worked step: name the concept, its kind, and one neighbour.",
    ]


def gen_mastery_interview(ex_id, concept, snippet, ctx) -> dict:
    """Build a mastery-interview card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        file = _concept_field(concept, "file", "") or "repo.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        code = "\n".join(str(l) for l in snippet) or (name or "concept")
        rubric = _rubric(concept, ctx) or [name or "concept"]
        grounded = bool(name or any(str(l).strip() for l in snippet))
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", "interview"),
            "concept": name or "interview", "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": _front_text(name or "interview", code),
            "back": "; ".join(rubric),
            "payload": {"rubric": rubric, "code": code[:600],
                        "grounded": grounded},
        }
    except Exception:
        return {  # generate never raises and never returns None
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "interview",
            "concept": "interview", "file": "repo.py", "line": 0,
            "commit": "", "hints": _hints(),
            "front": _front_text("interview", "concept"),
            "back": "interview",
            "payload": {"rubric": ["interview"], "code": "",
                        "grounded": False},
        }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Spoken-style rubric: cover at least half the key points."""
    _ = runner
    try:
        p = (exercise or {}).get("payload", {}) or {}
        text = str(submission if submission is not None else "").lower()
        if not text.strip():
            return _fail("Speak it, then write it — an empty page says nothing.")
        rubric = [r for r in p.get("rubric", []) if r]
        total = max(1, len(rubric))
        hits = [r for r in rubric if r.lower() in text]
        score = len(hits) / total
        if score >= _PASS_FRACTION:
            return {"pass": True, "score": score,
                    "feedback": f"Covered {len(hits)}/{total} key points — "
                                "oral-exam bar cleared."}
        missing = [r for r in rubric if r.lower() not in text]
        return {"pass": False, "score": score,
                "feedback": f"Covered {len(hits)}/{total} key points. "
                            f"Missing: {', '.join(missing)[:120]}"}
    except Exception as exc:  # noqa: BLE001 — grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def render(exercise: dict) -> str:
    """Exercise widget: read-aloud prompt plus explanation textarea."""
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Speak it aloud, then write it down — your words must "
        f"cover at least half the key points; missing points are listed "
        f"in the feedback.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='8' cols='70' "
        f"placeholder='The explanation you just spoke aloud…'>"
        f"</textarea><br><button>Submit explanation</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch18.py."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Mastery interview <small>(feature)</small></h3>"
        "<p>Oral-exam mode: read the prompt aloud, defend the concept, "
        "then write the explanation — graded against a spoken-style rubric "
        "(half the key points passes). "
        "<code>groundwork/interview.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Tour registry entry; the parent copies it into tour.ENTRIES."""
    return {
        "id": "mastery-interview",
        "kind": "feature",
        "title": "Mastery interview",
        "blurb": "Defend a concept aloud like an oral exam — speak it, write it, and clear half the rubric points.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
