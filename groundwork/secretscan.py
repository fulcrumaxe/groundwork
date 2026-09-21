"""Secret-scan exercise (type 50, F-27, bloom: analyse).

The learner reads a short snippet containing one planted (clearly-fake)
credential pattern and must name the exact leaked value or its line.
Grading is exact match after documented normalization: surrounding
quotes/whitespace are stripped, nothing else — a wrong value that
merely contains the right substring must NOT pass, and a dump of the
whole snippet must NOT pass either (it never isolates the leak).

Safety: this module never invents real-looking secrets. Planted values
always use the ``[REDACTED]`` marker prefix plus 8 hex chars derived
deterministically from ``(ex_id, concept)``, so they are recognizably
fake and reproducible. Snippets that already contain a
``name = "value"`` credential-shaped assignment (api key / token /
password / secret) are used as-is (mode ``"found"``); otherwise one
fake line is planted (mode ``"planted"``).

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only (``hashlib``/``html``/``re``), no
groundwork imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); pipeline needs no skip guard (the
fake marker is always plantable, unlike harness-gated 26/27 or
mutation-gated 28/34).

``generate`` never raises: when the snippet has no plantable surface
(empty snippet AND no usable concept name) it returns ``None`` instead
of a card, and the parent pipeline splice must skip ``None``.
"""
from __future__ import annotations

import hashlib
import html
import re

TYPE_NUM = 50
TYPE_NAME = "secret-scan"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b9-secretscan"

FAKE_PREFIX = "[REDACTED]"

_SECRET_NAME_RE = re.compile(
    r"(?i)\b(api[_-]?key|api[_-]?token|access[_-]?token|auth[_-]?token"
    r"|client[_-]?secret|secret|password|passwd|pwd)\b"
    r"\s*[:=]\s*(['\"])(?P<val>.+?)\2"
)

_PLANTED_NAME = "api_key"


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _fake_token(ex_id: str, name: str) -> str:
    digest = hashlib.sha256(f"{ex_id}:{name}".encode()).hexdigest()[:8].upper()
    return f"{FAKE_PREFIX}{digest}"


def _hints(secret: str, file: str, line: int) -> list[str]:
    where = f"{file}:{line}" if file and line else (file or "the linked file")
    return [
        "Scan every assignment: credential names are api_key, token, password, secret.",
        f"Look at {where}: exactly one line binds a secret value — quote it exactly.",
        f"Worked step: reply with the value alone (e.g. `{secret}`) or its line number.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a secret-scan card, or None when nothing is plantable.

    Found mode: first credential-shaped ``name = "value"`` assignment in
    the snippet becomes the leak. Planted mode: a deterministic
    ``[REDACTED]…`` line is inserted after the first snippet line.
    Returns None only when the snippet is empty AND the concept has no
    usable name — there is then no surface to find or plant on.
    """
    try:
        ctx = ctx or {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "") or "service"
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        lines = [str(l) for l in snippet if str(l).strip()]
        if not lines and not _concept_field(concept, "name", ""):
            return None  # no plantable surface: nothing to find or ground on
        if not lines:
            lines = [f"def {name}():", "    return True"]
        secret, leak_line, mode = "", 0, "planted"
        for i, text in enumerate(lines):
            m = _SECRET_NAME_RE.search(text)
            if m and m.group("val").strip():
                secret, leak_line, mode = m.group("val"), i + 1, "found"
                break
        if not secret:
            secret = _fake_token(str(ex_id), name)
            lines.insert(1 if len(lines) > 1 else len(lines),
                         f'{_PLANTED_NAME} = "{secret}"')
            leak_line = 2 if len(lines) > 2 else len(lines)
        numbered = "\n".join(f"{i + 1}: {l}" for i, l in enumerate(lines))
        front = (
            "One line below leaks a credential. Reply with the EXACT "
            "leaked value (or its line number).\n"
            f"```python\n{numbered[:800]}\n```"
        )
        back = f"Leaked value `{secret}` on line {leak_line} ({mode})."
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": _hints(secret, file, line),
            "front": front, "back": back,
            "payload": {"snippet": numbered[:800], "secret": secret,
                        "leak_line": leak_line, "mode": mode,
                        "grounded": True},
        }
    except Exception:
        return None  # grading-grade safety: generate never raises


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def normalize_value(text: str) -> str:
    """Strip surrounding whitespace and ONE layer of matching quotes."""
    t = str(text if text is not None else "").strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in ("'", '"'):
        t = t[1:-1].strip()
    return t


def _line_match(text: str, leak_line: int) -> bool:
    """True when the submission IS a line reference to the leak line.

    Strict by design (fuzztriage spirit): the stripped text must be just
    the number, optionally prefixed with "line"/"line #". Digits buried
    in a pasted snippet, a pasted secret, or prose never count — only an
    isolated line guess does. Never raises.
    """
    try:
        t = str(text or "").strip().lower()
        t = re.sub(r"^line\s*#?\s*", "", t)
        return t.isdigit() and int(t) == int(leak_line)
    except (TypeError, ValueError):
        return False


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact value-or-line match after quote/whitespace normalization."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        secret = str(payload.get("secret", "") or "")
        try:
            leak_line = int(payload.get("leak_line", 0) or 0)
        except (TypeError, ValueError):
            leak_line = 0
        if not secret or not leak_line:
            return _fail("Exercise payload is missing the leaked value.")
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Submit the exact leaked value or its line number.")
        value_ok = normalize_value(text) == normalize_value(secret)
        line_ok = _line_match(text, leak_line)
        if value_ok or line_ok:
            return {"pass": True, "score": 1.0,
                    "feedback": ("Exact secret value." if value_ok
                                 else f"Leak is on line {leak_line}.")}
        return _fail("Not the leak — quote the exact secret value or its line number.")
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit the exact value.")


def render(exercise: dict) -> str:
    """Exercise widget: numbered snippet plus a value/line answer box."""
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
        f"<p><small>Exact leaked value (quotes/whitespace ignored) or "
        f"exact line number — substrings do not count.</small></p></details>"
        f"<form method='post'><input name='answer' size='50' "
        f"placeholder='paste the exact secret or its line number'>"
        f"<button>Name the leak</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Secret-scan <small>(feature)</small></h3>"
        "<p>Find the leaked credential pattern in a snippet — name the exact "
        "value or its line. Graded by exact match after quote/whitespace "
        "normalization; planted secrets are always clearly-fake "
        "(<code>[REDACTED]…</code>). "
        "<code>groundwork/secretscan.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "secret-scan", "kind": "feature",
            "title": "Secret-scan",
            "blurb": "Spot the leaked credential in a snippet — quote the exact value or its line.",
            "path": "/status", "anchor": "status-b9-secretscan"}
