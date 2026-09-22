"""Analogy-builder drills (type 86, F-82, bloom: explain).

Map the concept onto an assigned familiar domain (a public library, a
restaurant kitchen, …) and state where the analogy breaks. Grading is
a keyword rubric half-bar (same family contract as types 5/6/24/25):
the submission must cover at least half the rubric points; feedback
lists the missing ones.

``generate`` never returns None and never raises: thin input yields an
ungrounded card the pipeline skips.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``gen_analogy`` (alias), ``render(exercise) -> html``,
``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 86),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES) and
``groundwork/__main__.py`` (cmd_e2e fixture); status section and
tour entry live below.
"""
from __future__ import annotations

import hashlib
import html

TYPE_NUM = 86
TYPE_NAME = "analogy-builder"
BLOOM = "explain"
STATUS_ANCHOR = "status-b19-analogy"

_PASS_FRACTION = 0.5

_DOMAINS = (
    "a public library",
    "a restaurant kitchen",
    "a post office",
    "a bus depot",
    "a gardening shed",
    "a school front office",
)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _seed(ex_id) -> int:
    try:
        return int(hashlib.sha256(str(ex_id).encode()).hexdigest(), 16)
    except Exception:  # noqa: BLE001 -- seeding must never raise
        return 0


def _domain(ex_id) -> str:
    try:
        return _DOMAINS[_seed(ex_id) % len(_DOMAINS)]
    except Exception:  # noqa: BLE001
        return _DOMAINS[0]


def _relatives(ctx: dict, concept) -> list[str]:
    """Up to 2 graph neighbour display names; never raises."""
    try:
        graph = (ctx or {}).get("graph")
        if graph is None:
            return []
        node_id = _concept_field(concept, "node_id", "")
        name = _concept_field(concept, "name", "")
        found = []
        for s, d, k in (list(getattr(graph, "edges", []) or [])):
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


def _rubric(concept, ctx: dict) -> list[str]:
    try:
        words = [_concept_field(concept, "name", ""),
                 _concept_field(concept, "kind", "")]
        file = _concept_field(concept, "file", "")
        if file:
            words.append(file.rsplit("/", 1)[-1])
        words += [w for w in _relatives(ctx, concept) if w not in words]
        return [w.lower() for w in words if w][:5] or ["code"]
    except Exception:  # noqa: BLE001
        return ["code"]


def _hints(domain: str) -> list[str]:
    return [
        f"Start inside {domain}: who are the actors?",
        "Map each actor to one part of the concept.",
        "End with the break: where does the mapping lie?",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build an analogy-builder card; never None, never raises."""
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
        if not name and not any(str(l).strip() for l in snippet):
            return _ungrounded(ex_id, name, file, line, commit)
        code = "\n".join(str(l) for l in snippet)[:600]
        domain = _domain(ex_id)
        rubric = _rubric(concept, ctx)
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": node_id or "analogy",
            "concept": name or "analogy", "file": file, "line": line,
            "commit": commit,
            "hints": _hints(domain),
            "front": (f"Explain `{name or 'this concept'}` through {domain}: "
                      "map each part, then state exactly where the analogy "
                      "breaks.\n"
                      f"```python\n{code}\n```"),
            "back": "; ".join(rubric) + f" as {domain}",
            "payload": {"domain": domain, "rubric": rubric, "code": code,
                        "grounded": True},
        }
    except Exception:
        return _ungrounded(ex_id, "", "app.py", 0, "")


def gen_analogy(ex_id, concept, snippet, ctx):
    """Alias under the card-type name; never None, never raises."""
    return generate(ex_id, concept, snippet, ctx)


def _ungrounded(ex_id, name, file, line, commit) -> dict:
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": "analogy",
        "concept": name or "analogy", "file": file, "line": line,
        "commit": commit, "hints": _hints("a public library"),
        "front": "Explain this through a familiar place. (Nothing found.)",
        "back": "No concept recorded — skipped by the pipeline.",
        "payload": {"domain": "", "rubric": [], "code": "",
                    "grounded": False},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Keyword rubric half-bar; the break must be attempted in prose."""
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
        return _fail("Map it first — pick the domain apart, then say "
                     "where it breaks.")
    if not rubric:
        return _fail("No key points recorded on this card.")
    lowered = text.lower()
    hits = [w for w in rubric if w in lowered]
    score = len(hits) / len(rubric)
    if score >= _PASS_FRACTION:
        return {"pass": True, "score": round(score, 2),
                "feedback": "Mapping holds — and you named its limit."}
    missing = [w for w in rubric if w not in hits]
    return {"pass": False, "score": round(score, 2),
            "feedback": ("Thin mapping — still missing: "
                         + ", ".join(missing[:4]))}


def render(exercise: dict) -> str:
    """Exercise widget: domain assignment, textarea, disclosure."""
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
        f"<p><small>Map it to the given familiar domain — your words "
        f"must cover at least half the key points; missing points are "
        f"listed in the feedback.</small></p>"
        f"</details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='70' "
        f"placeholder='The mapping…, and where it breaks…'></textarea><br>"
        f"<button>Map it</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Analogy builder <small>(feature)</small></h3>"
        "<p>Map the concept onto a familiar domain — and state where the "
        "analogy breaks. <code>groundwork/analogy.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "analogy-builder", "kind": "feature",
            "title": "Analogy builder",
            "blurb": "Map it onto a familiar domain — then state where the analogy breaks.",
            "path": "/due", "anchor": "up-next"}
