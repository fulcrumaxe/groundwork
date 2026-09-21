"""Containerize-it exercise (type 64, F-41, bloom: create).

The learner writes a complete Dockerfile for a small Python service
(entrypoint, port, static files) described on the card. There is no
docker daemon and no network here, so the "build gate" is a STATIC
verifier over the submitted Dockerfile text: a fixed required-directive
checklist plus forbidden patterns. Fully deterministic, no subprocess,
no network, no sandbox runner.

Required (ALL must hold): FROM with a pinned base image, WORKDIR, COPY,
EXPOSE matching the service port, CMD/ENTRYPOINT in exec (JSON-array)
form. Forbidden (ANY fails the card): ADD for local files, no USER
(running as root), any :latest tag, ENV binding a literal secret value.
Partial credit is forbidden: pass needs every checklist point (score
1.0) and any miss scores 0.0 — a build gate either ships or it does not.
Empty or garbage submissions fail closed.

Grounding: the card's rules mirror the repo's own Dockerfile
(python:3.12-slim pinned base, WORKDIR /app, COPY, EXPOSE, exec-form
CMD). The service port is derived deterministically from ex_id so the
card is stable across runs.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches) and
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES); status section and
tour entry live below.

``generate`` never raises: it returns None only when there is no
concept name AND no snippet to ground the service description on.
"""

from __future__ import annotations

import hashlib
import html
import re

TYPE_NUM = 64
TYPE_NAME = "containerize"
BLOOM = "create"
STATUS_ANCHOR = "status-b10-containerize"

_DEFAULT_PORT = 8765  # mirrors the repo's own Dockerfile EXPOSE

_FROM_RE = re.compile(r"^\s*FROM\s+(\S+)", re.IGNORECASE | re.MULTILINE)
_WORKDIR_RE = re.compile(r"^\s*WORKDIR\s+(\S+)", re.IGNORECASE | re.MULTILINE)
_COPY_RE = re.compile(r"^\s*COPY\s+(\S+)", re.IGNORECASE | re.MULTILINE)
_EXPOSE_RE = re.compile(r"^\s*EXPOSE\s+(\S+)", re.IGNORECASE | re.MULTILINE)
_EXEC_RE = re.compile(r"^\s*(CMD|ENTRYPOINT)\s*\[", re.IGNORECASE | re.MULTILINE)
_USER_RE = re.compile(r"^\s*USER\s+(\S+)", re.IGNORECASE | re.MULTILINE)
_ADD_RE = re.compile(r"^\s*ADD\s+(\S+)", re.IGNORECASE | re.MULTILINE)
_ENV_RE = re.compile(r"^\s*ENV\s+(\S+)(?:\s*=\s*|\s+)(\S*)",
                     re.IGNORECASE | re.MULTILINE)
_LATEST_RE = re.compile(r":latest(?:\s|$|@)", re.IGNORECASE)

_SECRET_NAME_RE = re.compile(
    r"(key|token|secret|password|passwd|pwd)", re.IGNORECASE)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _service_port(ex_id: str) -> int:
    """Deterministic service port in 8000-8999 derived from ex_id."""
    try:
        digest = hashlib.sha256(str(ex_id).encode()).hexdigest()[:4]
        return 8000 + int(digest, 16) % 1000
    except (TypeError, ValueError):
        return _DEFAULT_PORT


def _strip_comments(text: str) -> str:
    """Drop full-line `#` comments so commented directives never count."""
    return "\n".join(
        l for l in str(text).splitlines()
        if not l.lstrip().startswith("#"))


def _hints(entrypoint: str, port: int) -> list[str]:
    return [
        "Pin the base image tag (never :latest) and set WORKDIR first.",
        f"COPY the app in (ADD is for URLs, not local files), "
        f"EXPOSE {port} to match the service, and use exec-form CMD.",
        f"Worked step: end with USER plus CMD [\"python\", \"{entrypoint}\"].",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a containerize card, or None when nothing grounds it.

    The service description is grounded on the concept (entrypoint file
    defaults to ``app.py``) and the snippet (static files named there);
    the port is deterministic from ``ex_id``. Returns None only when
    the concept has no usable name AND the snippet is empty.
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
        if not lines and not name:
            return None  # no surface to describe a service from
        service = name or "app"
        entrypoint = file.split("/")[-1] or "app.py"
        if not entrypoint.endswith(".py"):
            entrypoint = "app.py"
        port = _service_port(ex_id)
        front = (
            f"Containerize the `{service}` service: a Python app with "
            f"entrypoint `{entrypoint}` listening on port {port}.\n"
            "Write a complete Dockerfile with: a pinned base image "
            "(never `:latest`), WORKDIR, COPY (not ADD) for local files, "
            f"EXPOSE {port}, exec-form CMD/ENTRYPOINT, and a non-root USER.\n"
            "Never bake secrets into ENV with literal values."
        )
        back = (
            "Model Dockerfile:\n"
            f"FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\n"
            f"EXPOSE {port}\nUSER appuser\n"
            f'CMD ["python", "{entrypoint}"]'
        )
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", service),
            "concept": service, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(entrypoint, port),
            "front": front, "back": back,
            "payload": {"entrypoint": entrypoint, "port": port,
                        "service": service, "grounded": True},
        }
    except Exception:
        return None  # generate never raises


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _checklist(text: str, port: int) -> list[str]:
    """Missing-required and forbidden-hit messages; empty means pass."""
    missing: list[str] = []
    froms = _FROM_RE.findall(text)
    pinned = [f for f in froms
              if ":" in f.rsplit("/", 1)[-1]
              and not f.lower().endswith(":latest")]
    if not pinned:
        missing.append("FROM with a pinned base tag (never :latest)")
    if not _WORKDIR_RE.search(text):
        missing.append("WORKDIR")
    if not _COPY_RE.search(text):
        missing.append("COPY for local files")
    exposed = _EXPOSE_RE.findall(text)
    if not any(str(port) in e.split() or e.strip() == str(port)
               for e in exposed):
        missing.append(f"EXPOSE {port} matching the service port")
    if not _EXEC_RE.search(text):
        missing.append("CMD/ENTRYPOINT in exec (JSON-array) form")
    if not _USER_RE.search(text):
        missing.append("USER (must not run as root)")
    for src in _ADD_RE.findall(text):
        if not src.lower().startswith(("http://", "https://")):
            missing.append("ADD for local files — use COPY")
            break
    if _LATEST_RE.search(text):
        missing.append("`:latest` tag is forbidden — pin the version")
    for var, val in _ENV_RE.findall(text):
        if (_SECRET_NAME_RE.search(var) and val.strip()
                and not val.strip().startswith("$")):
            missing.append(f"ENV {var} bakes in a literal secret")
            break
    return missing


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Static Dockerfile gate: every point required, no partial credit."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        try:
            port = int(payload.get("port", 0) or 0)
        except (TypeError, ValueError):
            port = 0
        if not port:
            return _fail("Exercise payload is missing the service port.")
        text = _strip_comments(str(submission if submission is not None else ""))
        if not text.strip():
            return _fail("Submit a complete Dockerfile.")
        if not re.search(r"^\s*(FROM|WORKDIR|COPY|EXPOSE|CMD|ENTRYPOINT|USER|RUN|ENV|ADD)\b",
                         text, re.IGNORECASE | re.MULTILINE):
            return _fail("No Dockerfile directives found — submit a Dockerfile.")
        missing = _checklist(text, port)
        if not missing:
            return {"pass": True, "score": 1.0,
                    "feedback": "Build gate green: pinned base, COPY, "
                                "matching EXPOSE, exec-form launch, non-root."}
        return _fail("Build gate red — fix: " + "; ".join(missing) + ".")
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit a Dockerfile.")


def render(exercise: dict) -> str:
    """Exercise widget: service spec plus disclosed checklist and textarea."""
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    port = html.escape(str((exercise.get("payload", {}) or {}).get("port", "")))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Static build gate, no partial credit. Required: pinned "
        f"FROM, WORKDIR, COPY, EXPOSE {port}, exec-form CMD/ENTRYPOINT, USER. "
        f"Forbidden: ADD for files, :latest, missing USER, ENV secret "
        f"literals.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='12' cols='70' "
        f"placeholder='FROM python:3.12-slim&#10;WORKDIR /app&#10;...'>"
        f"</textarea><br><button>Run build gate</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Containerize it <small>(feature)</small></h3>"
        "<p>Write a complete Dockerfile for a small Python service — static "
        "build gate over the submitted text (pinned FROM, WORKDIR, COPY, "
        "matching EXPOSE, exec-form CMD, USER; no ADD-for-files, :latest, "
        "or ENV secret literals; no partial credit). "
        "<code>groundwork/containerize.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "containerize-it", "kind": "feature",
            "title": "Containerize it",
            "blurb": "Write a Dockerfile for a small service — static build gate, no partial credit.",
            "path": "/status", "anchor": "status-b10-containerize"}
