"""Log-reading exercise (type 58, F-35, bloom: analyse).

The learner reads a short synthetic log describing exactly ONE root
cause from a fixed taxonomy and must name that exact cause. Two WARN
red herrings share vocabulary with real incidents but explain nothing;
they are never accepted answers.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only (``hashlib``/``html``/``random``/
``re``), no groundwork imports. Registration lives in
``groundwork/exercises.py`` (TYPES, GENERATORS, BLOOM_TYPES) plus
``pipeline.py`` BLOOM_DEFAULT_TYPES[``"analyse"``].

``generate`` never raises and (unlike find-or-plant types) always has
a plantable surface: a log is synthesizable from ``ex_id`` alone, so
the normal path never returns ``None``. ``None`` is returned only when
the call itself is unusable (missing ``ex_id`` AND no concept name to
seed on) or on unexpected error; the parent pipeline splice skips it.
Grounding: snippet lines containing an error signal (``error``,
``exception``, ``refused``, ``timeout``, ``expired``, ``full``, ...)
select the matching taxonomy cause (mode ``"grounded"``); otherwise
the cause is picked deterministically from ``ex_id`` (``"synthesized"``).
Both modes set ``grounded: True`` — the card is always self-contained.

Grading is exact-phrase match after documented normalization
(``normalize``): lowercase, trim, strip ONE layer of matching quotes,
``-``/``_`` to spaces, collapse whitespace, drop one trailing period
and a leading ``cause:``/``answer:`` label. The canonical phrase or a
listed alias of the card's cause passes; red herrings, pasted logs
(multi-line submissions always fail), and garbage fail closed.
"""
from __future__ import annotations

import hashlib
import html
import random
import re

TYPE_NUM = 58
TYPE_NAME = "log-reading"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b10-logread"

CAUSES = (
    {"key": "database connection refused",
     "aliases": ("connection refused", "db connection refused",
                 "postgres is down"),
     "signals": ("connection refused", "econnrefused",
                 "could not connect"),
     "msgs": ("db: connect postgres://db:5432/app failed: connection refused",
              "api: request GET /orders failed: upstream db unreachable",
              "worker: no healthy database backend, shutting down")},
    {"key": "out of memory",
     "aliases": ("oom", "oom kill", "memory exhausted"),
     "signals": ("out of memory", "oom", "memory exhausted",
                 "killed process"),
     "msgs": ("worker: memory usage 97% (1498/1536 MB)",
              "kernel: Out of memory: Killed process 412 (worker)",
              "worker: process exited (signal KILL), restart loop")},
    {"key": "disk full",
     "aliases": ("no space left", "disk is full", "enospc"),
     "signals": ("no space left", "disk full", "enospc"),
     "msgs": ("store: write /data/wal/00041 failed: No space left on device",
              "api: POST /upload failed: cannot spool request body",
              "store: disk usage 100% (/data), refusing writes")},
    {"key": "auth token expired",
     "aliases": ("token expired", "jwt expired", "unauthorized", "401"),
     "signals": ("token expired", "jwt expired", "unauthorized", " 401 "),
     "msgs": ("auth: token for svc-billing rejected: jwt expired",
              "api: GET /invoices failed: upstream 401 Unauthorized",
              "gateway: billing requests denied, auth refresh failing")},
    {"key": "upstream timeout",
     "aliases": ("timeout", "timed out", "gateway timeout", "504"),
     "signals": ("timed out", "timeout", "deadline exceeded", " 504 "),
     "msgs": ("api: GET /search exceeded 3000ms deadline (upstream search-svc)",
              "gateway: upstream search-svc timed out after 3 attempts",
              "gateway: 504 Gateway Timeout on /search, circuit open")},
    {"key": "tls certificate expired",
     "aliases": ("certificate expired", "cert expired", "certificate has expired"),
     "signals": ("certificate expired", "certificate has expired",
                 "cert expired"),
     "msgs": ("gateway: tls handshake with cdn-edge failed: certificate has expired",
              "api: webhook delivery failed: x509 certificate expired",
              "gateway: no valid serving certificate, https listener stopped")},
)

HERRINGS = (
    "api: deprecated v1 endpoint /old-search called 12 times",
    "cache: miss rate 41% above baseline on products:*",
    "worker: slow query 512ms on orders_by_user (threshold 500ms)",
    "webhook: retry 1/3 to partner ping (flaky, non-blocking)",
    "clock: skew 120ms vs ntp (tolerance 500ms)",
)

_ERROR_RE = re.compile(
    r"(?i)\b(error|exception|traceback|failed|refused|timeout|timed out"
    r"|expired|unauthorized|full|enospc|oom|killed|panic|fatal|denied)\b"
    r"|\b(5\d\d|401|504)\b")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _seed(ex_id: str, name: str) -> random.Random:
    digest = hashlib.sha256(f"{ex_id}:{name}".encode()).hexdigest()
    return random.Random(int(digest, 16) & 0xFFFFFFFF)


def _ground_cause(snippet: list[str]) -> int | None:
    """Index of the first taxonomy cause whose signal appears in the
    snippet, else None. Never raises."""
    try:
        blob = "\n".join(snippet).lower()
    except Exception:
        return None
    if not _ERROR_RE.search(blob):
        return None
    for i, cause in enumerate(CAUSES):
        if any(s in blob for s in cause["signals"]):
            return i
    return None


def _build_log(rng: random.Random, cause_ix: int) -> tuple[str, list[str]]:
    """Deterministic synthetic log; returns (log_text, herrings_used)."""
    cause = CAUSES[cause_ix]
    herrings = rng.sample(list(HERRINGS), 2)
    t = 10 * 3600 + rng.randrange(60)
    lines = [
        f"{t // 3600:02d}:{(t // 60) % 60:02d}:{t % 60:02d} INFO api: listening on :8080",
        f"{(t + 2) // 3600:02d}:{((t + 2) // 60) % 60:02d}:{(t + 2) % 60:02d} INFO worker: pool ready (4 workers)",
        f"{(t + 9) // 3600:02d}:{((t + 9) // 60) % 60:02d}:{(t + 9) % 60:02d} WARN {herrings[0]}",
        f"{(t + 14) // 3600:02d}:{((t + 14) // 60) % 60:02d}:{(t + 14) % 60:02d} WARN {herrings[1]}",
        f"{(t + 21) // 3600:02d}:{((t + 21) // 60) % 60:02d}:{(t + 21) % 60:02d} ERROR {cause['msgs'][0]}",
        f"{(t + 22) // 3600:02d}:{((t + 22) // 60) % 60:02d}:{(t + 22) % 60:02d} ERROR {cause['msgs'][1]}",
        f"{(t + 23) // 3600:02d}:{((t + 23) // 60) % 60:02d}:{(t + 23) % 60:02d} FATAL {cause['msgs'][2]}",
    ]
    return "\n".join(lines), herrings


def _hints(key: str, file: str, line: int) -> list[str]:
    where = f"{file}:{line}" if file and line else (file or "the linked file")
    return [
        "Read bottom-up: the FATAL line states the outcome, the ERROR lines state why.",
        f"WARN lines are noise ({where} context aside) — a warning that explains nothing is a red herring.",
        f"Worked step: reply with exactly one listed phrase (e.g. `{key}`).",
    ]


def normalize(text: str) -> str:
    """Lowercase; trim; strip ONE matching quote layer; ``-``/``_`` to
    spaces; collapse whitespace; drop a leading ``cause:``/``answer:``
    label and one trailing period."""
    t = str(text if text is not None else "").strip().lower()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in ("'", '"'):
        t = t[1:-1].strip()
    t = re.sub(r"^((root\s+)?cause|answer)\s*:\s*", "", t)
    t = re.sub(r"[-_]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    if t.endswith("."):
        t = t[:-1].strip()
    return t


def _answers_for(cause: dict) -> set[str]:
    return {normalize(p) for p in (cause["key"],) + tuple(cause["aliases"])}


def generate(ex_id, concept, snippet, ctx):
    """Build a log-reading card; None only when unseedable or on error."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = [str(l) for l in (snippet or []) if str(l).strip()]
        name = _concept_field(concept, "name", "")
        if not str(ex_id or "") and not name:
            return None  # nothing to seed determinism on
        name = name or "service"
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        rng = _seed(str(ex_id), name)
        hit = _ground_cause(snippet)
        if hit is None:
            seed_n = int(hashlib.sha256(
                f"{ex_id}:{name}".encode()).hexdigest(), 16)
            hit = seed_n % len(CAUSES)
            mode = "synthesized"
        else:
            mode = "grounded"
        cause = CAUSES[hit]
        log, herrings = _build_log(rng, hit)
        choices = [c["key"] for c in CAUSES]
        front = (
            "Read ONLY this log and name the exact ROOT CAUSE "
            "(one phrase from the list). WARN lines that explain "
            "nothing are red herrings.\n"
            f"Choices: {'; '.join(choices)}\n"
            f"```log\n{log[:1200]}\n```"
        )
        back = f"Root cause: `{cause['key']}` (see the FATAL line)."
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": _hints(cause["key"], file, line),
            "front": front, "back": back,
            "payload": {"log": log[:1200], "cause": cause["key"],
                        "choices": choices, "herrings": herrings,
                        "mode": mode, "grounded": True},
        }
    except Exception:
        return None  # grading-grade safety: generate never raises


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact root-cause phrase match after ``normalize``."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        cause_key = str(payload.get("cause", "") or "")
        cause = next((c for c in CAUSES if c["key"] == cause_key), None)
        if cause is None:
            return _fail("Exercise payload is missing the root cause.")
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Name the exact root cause (one listed phrase).")
        if "\n" in text.strip():
            return _fail("Reply with ONE phrase — a pasted log never isolates the cause.")
        if normalize(text) in _answers_for(cause):
            return {"pass": True, "score": 1.0,
                    "feedback": f"Correct: {cause_key}."}
        return _fail("Not the root cause — the WARN lines are red herrings; "
                     "follow the ERROR/FATAL chain.")
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — name one phrase.")


def render(exercise: dict) -> str:
    """Exercise widget: log plus a root-cause answer box."""
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
        f"<p><small>Exact root-cause phrase (case, quotes, and "
        f"whitespace ignored; listed aliases accepted) — red herrings "
        f"and pasted logs do not count.</small></p></details>"
        f"<form method='post'><input name='answer' size='50' "
        f"placeholder='name the exact root cause'>"
        f"<button>Diagnose</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Log reading <small>(feature)</small></h3>"
        "<p>Diagnose an outage from logs alone — name the exact root cause "
        "from a fixed taxonomy while WARN red herrings try to mislead. "
        "Graded by exact-phrase match after documented normalization. "
        "<code>groundwork/logread.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "log-reading", "kind": "feature",
            "title": "Log reading",
            "blurb": "Diagnose an outage from logs alone — name the exact root cause, not a red herring.",
            "path": "/status", "anchor": "status-b10-logread"}
