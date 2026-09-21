"""CI pipeline authoring exercise (type 65, F-42, bloom: create).

The learner authors a push-triggered CI pipeline as a workflow YAML
file. There is no CI runner and no network here, so the "dry-run
lint" is a STATIC verifier over the submitted text: top-level
``on:`` with ``push``, a non-empty ``jobs:`` mapping, a non-empty
``steps:`` list per job, ``run:`` or ``uses:`` per step, and no
syntax errors (tabs, ragged indent, colon-less mapping lines).
Fully deterministic, stdlib only.

``generate`` never returns None: a truly thin surface still yields an
ungrounded fallback card (``grounded: False``) that the pipeline's
grounded-gate skips, while direct callers still get a card.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches) and
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES); status section and
tour entry live below.
"""

from __future__ import annotations

import hashlib
import html
import re

TYPE_NUM = 65
TYPE_NAME = "cipipe"
BLOOM = "create"
STATUS_ANCHOR = "status-b11-cipipe"

_BRANCH = "main"

_ON_RE = re.compile(r"^\s*on\s*:(.*)$", re.IGNORECASE)
_JOBS_RE = re.compile(r"^\s*jobs\s*:(.*)$", re.IGNORECASE)
_KEY_RE = re.compile(r"^\s*[\w\".'-]+\s*:")
_ITEM_RE = re.compile(r"^(\s*)-\s")
_STEP_KEY_RE = re.compile(r"^\s*(?:-\s+)?(run|uses)\s*:", re.IGNORECASE)
_PUSH_RE = re.compile(r"^\s*push\s*:", re.IGNORECASE)

_MODEL_BACK = (
    "on:\n  push:\n    branches: [main]\n"
    "jobs:\n  test:\n    runs-on: ubuntu-latest\n"
    "    steps:\n      - uses: actions/checkout@v4\n      - run: pytest"
)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _clean_service(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", str(name or "").lower()).strip("-")
    return cleaned or "app"


def _strip_comments(text: str) -> str:
    """Drop full-line `#` comments so commented keys never count."""
    return "\n".join(
        l for l in str(text).splitlines()
        if not l.lstrip().startswith("#"))


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _block(lines: list, start: int, indent: int) -> list:
    """Lines belonging to a mapping key: deeper-indented lines after it."""
    out = []
    for line in lines[start + 1:]:
        if not line.strip():
            continue
        if _indent_of(line) <= indent:
            break
        out.append(line)
    return out


def _checklist(text: str) -> list[str]:
    """Missing-required and syntax-error messages; empty means pass."""
    missing: list[str] = []
    body = _strip_comments(text)
    lines = [l for l in body.splitlines() if l.strip()]
    if not lines:
        return ["a complete workflow YAML file"]
    if any("\t" in l for l in lines):
        return ["no tab indentation — use spaces"]
    indents = sorted({_indent_of(l) for l in lines
                      if l.strip() and not _ITEM_RE.match(l)})
    step = min((i for i in indents if i > 0), default=2)
    if step <= 0:
        step = 2
    for l in lines:
        if not _ITEM_RE.match(l) and _indent_of(l) % step:
            return [f"ragged indentation near: {l.strip()[:40]}"]
        if (not _ITEM_RE.match(l) and ":" not in l
                and _indent_of(l) > 0):
            return [f"mapping line without a colon: {l.strip()[:40]}"]
    on_idx = next((i for i, l in enumerate(lines)
                   if _ON_RE.match(l) and _indent_of(l) == 0), None)
    if on_idx is None:
        missing.append("top-level `on:` trigger block")
    else:
        inline = _ON_RE.match(lines[on_idx]).group(1)
        block = _block(lines, on_idx, 0)
        if ("push" not in inline
                and not any(_PUSH_RE.match(l) for l in block)):
            missing.append("`on:` block containing `push`")
    jobs_idx = next((i for i, l in enumerate(lines)
                     if _JOBS_RE.match(l) and _indent_of(l) == 0), None)
    if jobs_idx is None:
        missing.append("non-empty `jobs:` mapping")
    else:
        if _JOBS_RE.match(lines[jobs_idx]).group(1).strip():
            missing.append("non-empty `jobs:` mapping")
        else:
            jobs_indent = _indent_of(lines[jobs_idx])
            job_lines = [(i, l) for i, l in enumerate(lines)
                         if i > jobs_idx and _indent_of(l) > jobs_indent
                         and _KEY_RE.match(l)
                         and not _ITEM_RE.match(l)]
            if not job_lines:
                missing.append("non-empty `jobs:` mapping")
            else:
                level = min(_indent_of(l) for _, l in job_lines)
                for j, (i, l) in enumerate(job_lines):
                    if _indent_of(l) != level:
                        continue
                    job_block = _block(lines, i, level)
                    steps_idx = next(
                        (k for k, b in enumerate(job_block)
                         if re.match(r"^\s*steps\s*:", b, re.IGNORECASE)
                         and not _ITEM_RE.match(b)), None)
                    if steps_idx is None:
                        missing.append(f"job `{l.strip()}` needs a `steps:` list")
                        continue
                    items = [(k, b) for k, b in enumerate(job_block)
                             if _ITEM_RE.match(b)]
                    if not items:
                        missing.append(f"job `{l.strip()}` needs a `steps:` list")
                        continue
                    for k, (ki, item) in enumerate(items):
                        nxt = items[k + 1][0] if k + 1 < len(items) else None
                        chunk = [item] + [
                            b for q, b in enumerate(job_block)
                            if q > ki and (nxt is None or q < nxt)
                            and _indent_of(b) > _indent_of(item)]
                        if not any(_STEP_KEY_RE.match(c) for c in chunk):
                            missing.append(
                                "every step needs `run:` or `uses:`")
                            break
    return missing


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _hints(workflow: str) -> list[str]:
    return [
        "Order the file trigger-then-jobs-then-steps: `on:` first.",
        "Every step needs `run:` or `uses:` — a bare `- name:` is not a step.",
        f"Worked step: `on: push: branches: [{_BRANCH}]` then one job "
        "with `- uses: actions/checkout@v4` and `- run: pytest`.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a CI-pipeline card; never None, never raises.

    Grounded when the concept has a usable name or the snippet holds
    lines; otherwise an ungrounded fallback card the pipeline skips.
    """
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        file = _concept_field(concept, "file", "") or "app.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        lines = [str(l) for l in snippet if str(l).strip()]
        if lines or name:
            service = _clean_service(name or "app")
            concept_name = name or service
            grounded = True
        else:
            service = "app"
            concept_name = service
            grounded = False
        workflow = f"ci-{service}"
        front = (
            f"Author the `{workflow}` CI pipeline: triggers on push to "
            f"`{_BRANCH}`, one job with steps that check out code and run "
            "tests. Submit a complete workflow YAML file."
        )
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", service),
            "concept": concept_name, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(workflow),
            "front": front, "back": _MODEL_BACK,
            "payload": {"workflow": workflow, "branch": _BRANCH,
                        "grounded": grounded},
        }
    except Exception:
        return {  # generate never raises and never returns None
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "app", "concept": "app",
            "file": "app.py", "line": 0, "commit": "",
            "hints": _hints("ci-app"),
            "front": ("Author the `ci-app` CI pipeline: triggers on push "
                      "to `main`, one job with steps that check out code "
                      "and run tests. Submit a complete workflow YAML file."),
            "back": _MODEL_BACK,
            "payload": {"workflow": "ci-app", "branch": _BRANCH,
                        "grounded": False},
        }


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Static dry-run lint: every point required, no partial credit."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Submit a complete workflow YAML file.")
        if ":" not in _strip_comments(text):
            return _fail("No YAML mapping found — submit a workflow file.")
        missing = _checklist(text)
        if not missing:
            wf = payload.get("workflow", "ci")
            return {"pass": True, "score": 1.0,
                    "feedback": f"Lint green: `{wf}` triggers on push, "
                                "jobs carry steps, every step runs or uses."}
        return _fail("Lint red — fix: " + "; ".join(missing) + ".")
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit YAML.")


def render(exercise: dict) -> str:
    """Exercise widget: pipeline spec plus disclosed checklist and textarea."""
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
        f"<p><small>Static dry-run lint, no partial credit. Required: "
        f"`on:` with push, non-empty `jobs:`, `steps:` per job, "
        f"`run:`/`uses:` per step, no syntax errors.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='12' cols='70' "
        f"placeholder='on:&#10;  push:'>"
        f"</textarea><br><button>Run dry-run lint</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>CI pipeline <small>(feature)</small></h3>"
        "<p>Author a push-triggered CI pipeline — static dry-run lint "
        "over the submitted YAML (`on:` with push, jobs with steps, "
        "`run:`/`uses:` per step, no syntax errors; no partial credit). "
        "<code>groundwork/cipipe.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "cipipe", "kind": "feature",
            "title": "CI pipeline",
            "blurb": "Author a push-triggered CI pipeline — static dry-run lint, no partial credit.",
            "path": "/status", "anchor": "status-b11-cipipe"}
