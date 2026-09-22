"""Protege-effect studio drills (type 84, F-80, bloom: create).

Teaching cements learning. The front stages a simulated junior who
states a plausible-but-wrong claim about the concept (a planted
misconception from fixed templates — direction-inverted,
scope-swapped, always/never absolutized) and then asks one follow-up
question (3 choices, deterministic seed from the card id). The learner
must (a) correct the junior in their own words and (b) answer the
follow-up. Grading: correction passes on the rubric half-or-more bar
(same bar as types 5/6/24/25/73); follow-up passes on exact letter
match; the card passes only if BOTH pass; score is the mean.

``generate`` never returns None and never raises: thin input yields an
ungrounded card the pipeline skips.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``gen_protege`` (alias), ``render(exercise) -> html``,
``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 84),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES) and
``groundwork/__main__.py`` (cmd_e2e fixture); status section and
tour entry live below.
"""
from __future__ import annotations

import hashlib
import html
import random

TYPE_NUM = 84
TYPE_NAME = "protege-studio"
BLOOM = "create"
STATUS_ANCHOR = "status-b19-protege"

_PASS_FRACTION = 0.5

_CLAIMS = (
    "I think {name} always returns the same value no matter the inputs.",
    "I think {name} never changes anything outside itself.",
    "I think the order of the lines inside {name} does not matter.",
    "I think {name} works for every possible input.",
)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _seed(ex_id) -> int:
    try:
        return int(hashlib.sha256(str(ex_id).encode()).hexdigest(), 16)
    except Exception:  # noqa: BLE001 -- seeding must never raise
        return 0


def _rubric(concept) -> list[str]:
    try:
        words = [_concept_field(concept, "name", ""),
                 _concept_field(concept, "kind", "")]
        file = _concept_field(concept, "file", "")
        if file:
            words.append(file.rsplit("/", 1)[-1])
        return [w.lower() for w in words if w] or ["code"]
    except Exception:  # noqa: BLE001
        return ["code"]


def _followup(concept, rubric: list[str], ex_id) -> dict:
    """3-choice follow-up; deterministic shuffle; never raises."""
    try:
        name = _concept_field(concept, "name", "it") or "it"
        answer = rubric[0] if rubric else name
        pool = [answer, f"not {answer}", f"only {answer}"]
        rng = random.Random(_seed(ex_id) & 0xFFFFFFFF)
        order = [0, 1, 2]
        rng.shuffle(order)
        choices = [pool[i] for i in order]
        key = "ABC"[choices.index(answer)]
        return {"q": f"The junior asks: what is the one key idea behind {name}?",
                "choices": choices, "answer": answer, "key": key}
    except Exception:  # noqa: BLE001
        return {"q": "What is the key idea?", "choices": ["A", "B", "C"],
                "answer": "A", "key": "A"}


def _hints() -> list[str]:
    return [
        "Correct the claim first — quote the line that proves it wrong.",
        "Then answer the follow-up with its letter.",
        "Teach, don't scold: the junior is you from last week.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a protege-studio card; never None, never raises."""
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
        claim = _CLAIMS[_seed(ex_id) % len(_CLAIMS)].format(name=name)
        rubric = _rubric(concept)
        followup = _followup(concept, rubric, ex_id)
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": node_id or "protege",
            "concept": name, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": (f"A junior says: \"{claim}\"\nCorrect them, then "
                      f"answer their follow-up: {followup['q']}\n"
                      + "".join(f"{chr(65 + i)}) {c}\n"
                                for i, c in enumerate(followup["choices"])) +
                      f"```python\n{code}\n```"),
            "back": ("Correction covers: " + ", ".join(rubric) +
                     f". Follow-up answer: {followup['key']}."),
            "payload": {"rubric": rubric, "junior_claim": claim,
                        "followup": followup, "key": followup["key"],
                        "reference": ", ".join(rubric),
                        "grounded": True},
        }
    except Exception:
        return _ungrounded(ex_id, "", "app.py", 0, "")


def gen_protege(ex_id, concept, snippet, ctx):
    """Alias under the card-type name; never None, never raises."""
    return generate(ex_id, concept, snippet, ctx)


def _ungrounded(ex_id, name, file, line, commit) -> dict:
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": "protege",
        "concept": name or "protege", "file": file, "line": line,
        "commit": commit, "hints": _hints(),
        "front": "A junior asks about this concept. (Nothing staged found.)",
        "back": "No concept recorded — skipped by the pipeline.",
        "payload": {"rubric": [], "junior_claim": "",
                    "followup": {"q": "", "choices": [], "answer": "",
                                 "key": ""},
                    "key": "", "reference": "", "grounded": False},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _parse(submission: str) -> tuple:
    """(correction prose, letter or "") from a two-part answer."""
    try:
        text = str(submission if submission is not None else "")
        if not text.strip():
            return ("", "")
        lines = [l for l in text.strip().splitlines() if l.strip()]
        last = lines[-1].strip()
        letter = ""
        if len(last) == 1 and last.upper() in "ABC":
            letter = last.upper()
            lines = lines[:-1]
        elif "=" in last:
            _k, _, v = last.partition("=")
            v = v.strip().upper()
            if _k.strip().lower() in ("followup", "follow-up", "letter",
                                      "answer") and v in "ABC":
                letter = v
                lines = lines[:-1]
        return ("\n".join(lines), letter)
    except Exception:  # noqa: BLE001
        return ("", "")


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Correction half-bar AND follow-up letter; both must pass."""
    _ = runner
    try:
        return _grade(exercise, submission)
    except Exception as exc:  # noqa: BLE001 -- grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    rubric = [str(w).lower() for w in (p.get("rubric", []) or []) if w]
    key = str(p.get("key", "") or "").upper()
    correction, letter = _parse(submission)
    if not str(submission or "").strip():
        return _fail("Teach first — correct the junior, then answer "
                     "the follow-up with its letter.")
    if not rubric or not key:
        return _fail("No junior staged on this card.")
    lowered = correction.lower()
    hits = [w for w in rubric if w in lowered]
    rubric_score = len(hits) / len(rubric)
    correction_ok = rubric_score >= _PASS_FRACTION
    followup_ok = letter == key
    score = round((rubric_score + (1.0 if followup_ok else 0.0)) / 2, 2)
    if correction_ok and followup_ok:
        return {"pass": True, "score": score,
                "feedback": "Junior corrected — teaching lands."}
    bits = []
    if not correction_ok:
        missing = [w for w in rubric if w not in hits]
        bits.append("correction still missing: " + ", ".join(missing[:4]))
    if not followup_ok:
        bits.append(f"follow-up answer is {key}")
    return {"pass": False, "score": score,
            "feedback": "Not yet — " + "; ".join(bits)}


def render(exercise: dict) -> str:
    """Exercise widget: junior claim, follow-up choices, two inputs."""
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
        f"<p><small>Correct the junior (half the key points) AND answer "
        f"the follow-up — both must pass.</small></p>"
        f"</details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='70' "
        f"placeholder='Correction…, then the letter on its own line'></textarea><br>"
        f"<button>Teach the junior</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Protege-effect studio <small>(feature)</small></h3>"
        "<p>Teach a simulated junior: correct their claim, then answer the "
        "follow-up — both halves must pass. "
        "<code>groundwork/protege.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "protege-studio", "kind": "feature",
            "title": "Protege-effect studio",
            "blurb": "Teach a simulated junior — correct the claim, answer the follow-up, both must pass.",
            "path": "/due", "anchor": "up-next"}
