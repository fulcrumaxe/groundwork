"""Commit-message authorship exercise (type 42, F-19, bloom: create).

Summarize a diff as a commit message: imperative subject line <=72
chars naming the what + why keywords. Reference keywords come from the
concept itself (name/file tokens) and the diff context (ctx hunks /
decisions when present, else the snippet), so the card always builds.
Grading is a deterministic 4-point rubric — no execution, no sandbox.
Stdlib only (``html``/``re``), import-safe standalone: no groundwork imports.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); see ===STATUS===.
"""
from __future__ import annotations

import html
import re

TYPE_NUM = 42
TYPE_NAME = "commit-message"
BLOOM = "create"

_MAX_SUBJECT = 72
_IMPERATIVES = frozenset(
    "add allow avoid bump cache clean correct disable document drop enable fix "
    "handle hide ignore implement improve introduce make move prevent refactor "
    "remove rename replace revert show simplify speed support test update use "
    "validate guard keep log match order parse quote retry return scope sort "
    "split strip tighten trace trim warn wire".split()
)
_STOP = frozenset(
    "the a an of to in on for with and or as at by from that this it its "
    "be are was were has have had not no def return class self none true "
    "false if else elif for while import from".split()
)
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_]*")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _words(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text or "")]


def _name_tokens(name: str) -> list[str]:
    parts = re.split(r"(?<=[a-z0-9])(?=[A-Z])|_+", name or "")
    out = [p.lower() for p in parts if p and p.lower() not in _STOP]
    return [w for w in dict.fromkeys(out) if w]


def _diff_text(ctx: dict, snippet: list[str]) -> str:
    lines = ctx.get("diff_lines")
    if isinstance(lines, list) and any(str(l).strip() for l in lines):
        return "\n".join(str(l) for l in lines)[:1500]
    hunks = ctx.get("hunks")
    if isinstance(hunks, list) and hunks:
        return "\n".join(str(h) for h in hunks)[:1500]
    code = str(ctx.get("runnable") or "")
    if code.strip():
        return code[:1500]
    return "\n".join(snippet or [])[:1500]


def _why_source(ctx: dict) -> str:
    dec = ctx.get("decisions")
    if isinstance(dec, list) and dec:
        bits = []
        for d in dec[:3]:
            if isinstance(d, dict):
                bits.extend(str(v) for v in d.values())
            else:
                bits.append(str(d))
        if any(b.strip() for b in bits):
            return "\n".join(bits)
    lesson = ctx.get("lesson")
    if isinstance(lesson, dict):
        for key in ("summary", "docstring"):
            if str(lesson.get(key) or "").strip():
                return str(lesson[key])
    return ""


def _keywords(concept, diff: str, ctx: dict):
    what = _name_tokens(_concept_field(concept, "name", "change"))[:3]
    stem = re.sub(r"\.\w+$", "", (_concept_field(concept, "file") or "").split("/")[-1])
    for tok in _name_tokens(stem)[:1]:
        if tok not in what:
            what.append(tok)
    if not what:
        what = ["change"]
    why_cands = [w for w in _words(_why_source(ctx)) if w not in _STOP and w not in what]
    if not why_cands:
        why_cands = [w for w in _words(diff) if w not in _STOP and w not in what and len(w) > 2]
    why = list(dict.fromkeys(why_cands))[:2] or ["update"]
    return what, why


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a commit-message card from diff context (else snippet)."""
    ctx = ctx or {}
    snippet = list(snippet or [])
    name = _concept_field(concept, "name", "change")
    file = _concept_field(concept, "file")
    try:
        line = int(getattr(concept, "line", 0) or 0)
    except (TypeError, ValueError):
        line = 0
    commit = str(ctx.get("commit", "") or "")
    diff = _diff_text(ctx, snippet)
    what, why = _keywords(concept, diff, ctx)
    reference = f"Update {what[0]} for {why[0]}"[:_MAX_SUBJECT]
    front = (
        f"Summarize this change to `{name}` as a commit message.\n"
        f"Subject line: imperative, <= {_MAX_SUBJECT} chars, "
        f"naming WHAT changed ({', '.join(f'`{w}`' for w in what)}) "
        f"and WHY ({', '.join(f'`{w}`' for w in why)}).\n"
        f"```diff\n{(diff or '(no diff shown)')[:1200]}\n```"
    )
    back = reference + "  (model answer — any imperative subject <=72 chars naming the what + why counts)."
    hints = [
        f"Start with an imperative verb (Update/Fix/Remove …), not `{name} updated`.",
        f"Name the what: `{what[0]}`.",
        f"Name the why: `{why[0]}` — the intent behind the change.",
    ]
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
        "concept_id": _concept_field(concept, "node_id", name),
        "concept": name, "file": file, "line": line, "commit": commit,
        "hints": hints, "front": front, "back": back,
        "payload": {"diff": diff, "what": what, "why": why,
                    "reference": reference, "grounded": True},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _subject(text: str) -> str:
    for ln in str(text or "").splitlines():
        if ln.strip():
            return ln.strip()
    return ""


def _imperative_ok(subject: str) -> bool:
    core = re.sub(r"^\w+(\([^)]*\))?:\s*", "", subject).strip()
    first = (_WORD.findall(core) or [""])[0].lower()
    return first in _IMPERATIVES


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """4-point rubric: imperative, <=72 chars, what keyword, why keyword."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {})
        what = [str(w).lower() for w in payload.get("what", []) if str(w)]
        why = [str(w).lower() for w in payload.get("why", []) if str(w)]
        subject = _subject(submission)
        if not subject:
            return _fail("Submit a one-line commit message.")
        missing, earned, total = [], 0, 4
        if _imperative_ok(subject):
            earned += 1
        else:
            missing.append("start with an imperative verb (e.g. Update, Fix, Remove)")
        if len(subject) <= _MAX_SUBJECT:
            earned += 1
        else:
            missing.append(f"subject is {len(subject)} chars, keep <= {_MAX_SUBJECT}")
        low = subject.lower()
        if what and any(w in low for w in what):
            earned += 1
        else:
            missing.append(f"name the what ({'/'.join(what) or 'the changed symbol'})")
        if why and any(w in low for w in why):
            earned += 1
        else:
            missing.append(f"name the why ({'/'.join(why) or 'the intent'})")
        score = earned / total
        if not missing:
            return {"pass": True, "score": 1.0, "feedback": "Commit message accepted. 4/4 rubric points."}
        return {"pass": False, "score": score,
                "feedback": f"Not yet. {earned}/{total} rubric points. Fix: {'; '.join(missing)[:200]}."}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit one line of text.")


def render(exercise: dict) -> str:
    """Diff/snippet plus a one-line textarea and grading disclosure."""
    payload = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    diff = html.escape(str(payload.get("diff", ""))[:1500])
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", []))
    )
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<pre>{diff}</pre>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Deterministic rubric (4 points, all required): imperative "
        f"subject, &lt;= 72 chars, names the what, names the why. "
        f"Partial credit recorded, no sandbox.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='3' cols='70'></textarea>"
        f"<br><button>Check message</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def tour_entry() -> dict:
    """Feature-tour registry entry for the parent to append."""
    return {"id": "commitmsg-type", "kind": "feature",
            "title": "Commit-message authorship",
            "blurb": "Summarize a diff as a commit message: imperative subject naming the what and the why.",
            "path": "/status", "anchor": "status-b8-commitmsg"}


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b8-commitmsg'>Commit-message authorship <small>(feature)</small></h3>"
        "<p>Summarize a diff as a commit message — imperative subject "
        "line under 72 chars naming the what and the why, graded by "
        "deterministic rubric with no sandbox. "
        "<code>groundwork/commitmsg.py</code>.</p>"
    )
