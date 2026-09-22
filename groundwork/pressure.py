"""Timed pressure-drill exercise (type 76, F-72, bloom: analyze).

The learner gets ~18 lines of production-style log (millis timestamps,
request ids, three services) describing exactly ONE root cause and a
90s drill budget. They must name the exact cause phrase. Two WARN red
herrings plus one failing-but-unrelated request (ERROR-level herring)
compete for attention; all herrings fail closed.

The budget is advisory: it travels in the payload and renders as a
countdown, but grading is a deterministic exact-phrase match (same
normalization contract as logread). No wall clock, no sandbox.

``generate`` never returns None and never raises: the fixture is fully
synthetic (cause, log, herrings seed from ``ex_id``), so every input —
grounded from snippet signals or synthesized from the seed — yields a
self-contained gradeable card.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``,
``check(exercise, submission) -> bool`` (pure phrase predicate used by
``grade``). Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES), ``groundwork/grading.py``
(disclosure 76) and ``groundwork/__main__.py`` (cmd_e2e fixture answer);
status section and tour entry below join the ``groundwork/batch18.py``
home module (anchor ``status-b18-pressure``, path /status).
"""

from __future__ import annotations

import hashlib
import html
import random
import re

TYPE_NUM = 76
TYPE_NAME = "pressure-drill"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b18-pressure"
BUDGET_S = 90

CAUSES = (
    {"key": "database connection refused",
     "aliases": ("connection refused", "db connection refused",),
     "signals": ("connection refused", "econnrefused", "could not connect"),
     "msgs": ("pg-connector: dial postgres://db:5432/app: connection refused",
              "checkout-api: POST /orders failed: upstream db unreachable",
              "order-worker: no healthy database backend, draining queue")},
    {"key": "upstream timeout",
     "aliases": ("timeout", "timed out", "gateway timeout", "504"),
     "signals": ("timed out", "timeout", "deadline exceeded", " 504 "),
     "msgs": ("search-api: GET /search exceeded 3000ms deadline (search-svc)",
              "edge-gw: upstream search-svc timed out after 3 attempts",
              "edge-gw: 504 Gateway Timeout on /search, circuit open")},
    {"key": "auth token expired",
     "aliases": ("token expired", "jwt expired", "unauthorized", "401"),
     "signals": ("token expired", "jwt expired", "unauthorized", " 401 "),
     "msgs": ("auth-svc: token for svc-billing rejected: jwt expired",
              "billing-api: GET /invoices failed: upstream 401",
              "edge-gw: billing requests denied, auth refresh failing")},
    {"key": "disk full",
     "aliases": ("no space left", "disk is full", "enospc"),
     "signals": ("no space left", "disk full", "enospc"),
     "msgs": ("store-svc: write /data/wal/00041: No space left on device",
              "upload-api: POST /upload failed: cannot spool request body",
              "store-svc: disk usage 100% (/data), refusing writes")},
)

HERRING_WARNS = (
    "search-api: deprecated v1 endpoint /old-search called 12 times",
    "edge-gw: cache miss rate 41% above baseline on products:*",
    "order-worker: slow query 512ms on orders_by_user (threshold 500ms)",
    "billing-api: retry 1/3 to partner ping (flaky, non-blocking)",
    "auth-svc: clock skew 120ms vs ntp (tolerance 500ms)",
)
HERRING_ERRORS = (
    "metrics-agent: push to stats-sink failed: dial tcp: i/o timeout (non-blocking)",
    "audit-tail: drop 3 lines: backpressure on debug sink (lossy by design)",
)

_ERROR_RE = re.compile(
    r"(?i)\b(error|exception|traceback|failed|refused|timeout|timed out"
    r"|expired|unauthorized|full|enospc|oom|killed|panic|fatal|denied)\b"
    r"|\b(5\d\d|401|504)\b")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _seed(ex_id: str, name: str) -> random.Random:
    digest = hashlib.sha256(f"pressure:{ex_id}:{name}".encode()).hexdigest()
    return random.Random(int(digest, 16) & 0xFFFFFFFF)


def _ground_cause(snippet: list[str]) -> int | None:
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


def _build_log(rng: random.Random, cause_ix: int) -> tuple[str, str, str]:
    """Production-style log; returns (log_text, victim_req, decoy_req)."""
    cause = CAUSES[cause_ix]
    victim = f"req-{rng.randrange(0x1000, 0xFFFF):04x}"
    decoy = f"req-{rng.randrange(0x1000, 0xFFFF):04x}"
    while decoy == victim:
        decoy = f"req-{rng.randrange(0x1000, 0xFFFF):04x}"
    warns = rng.sample(list(HERRING_WARNS), 2)
    err_herring = rng.choice(list(HERRING_ERRORS))
    t = 14 * 3600 + rng.randrange(60)
    ts = lambda d: (f"{(t + d) // 3600:02d}:{((t + d) // 60) % 60:02d}:"
                    f"{(t + d) % 60:02d}.{(rng.randrange(1000)):03d}")

    def svc(n: int) -> str:
        return ("checkout-api", "order-worker", "edge-gw")[n % 3]

    lines = [
        f"{ts(0)} INFO  edge-gw: listening on :8080 ({victim} warmup)",
        f"{ts(1)} INFO  {svc(cause_ix)}: pool ready (8 workers)",
        f"{ts(4)} WARN  {svc(1)}: {warns[0]}",
        f"{ts(6)} INFO  edge-gw: {decoy} GET /stats 200 4ms",
        f"{ts(7)} WARN  {svc(2)}: {warns[1]}",
        f"{ts(9)} INFO  edge-gw: {victim} POST /orders accepted",
        f"{ts(11)} ERROR {svc(3)}: {err_herring} [{decoy}]",
        f"{ts(13)} ERROR {svc(cause_ix)}: {cause['msgs'][0]} [{victim}]",
        f"{ts(15)} ERROR {svc(cause_ix + 1)}: {cause['msgs'][1]} [{victim}]",
        f"{ts(17)} FATAL {svc(cause_ix + 2)}: {cause['msgs'][2]} [{victim}]",
    ]
    return "\n".join(lines), victim, decoy


def _hints(key: str, victim: str) -> list[str]:
    return [
        "Follow ONE request id: the FATAL line's id is the victim, the rest is noise.",
        f"ERROR lines without [{victim}] belong to another request — ignore them.",
        f"Worked step: reply with exactly one listed phrase (e.g. `{key}`); "
        f"you have {BUDGET_S}s on the clock.",
    ]


def normalize(text: str) -> str:
    """Lowercase; trim; strip ONE matching quote layer; ``-``/``_`` to
    spaces; collapse whitespace; drop a leading ``cause:``/``answer:``
    label and one trailing period. Mirrors logread.normalize."""
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


def gen_pressure_drill(ex_id, concept, snippet, ctx) -> dict:
    """Build a pressure-drill card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = [str(l) for l in (snippet or []) if str(l).strip()]
        name = _concept_field(concept, "name", "") or "service"
        file = _concept_field(concept, "file", "") or "service.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        rng = _seed(str(ex_id), name)
        hit = _ground_cause(snippet)
        if hit is None:
            seed_n = int(hashlib.sha256(
                f"pressure:{ex_id}:{name}".encode()).hexdigest(), 16)
            hit = seed_n % len(CAUSES)
            mode = "synthesized"
        else:
            mode = "grounded"
        cause = CAUSES[hit]
        log, victim, decoy = _build_log(rng, hit)
        choices = [c["key"] for c in CAUSES]
        front = (
            f"DRILL — {BUDGET_S}s budget. Read ONLY this production log and "
            f"name the exact ROOT CAUSE (one phrase from the list). "
            f"Follow the failing request id; every other request is noise.\n"
            f"Choices: {'; '.join(choices)}\n"
            f"```log\n{log[:1600]}\n```"
        )
        back = f"Root cause: `{cause['key']}` (victim {victim})."
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": _hints(cause["key"], victim),
            "front": front, "back": back,
            "payload": {"log": log[:1600], "cause": cause["key"],
                        "answer": cause["key"],
                        "aliases": list(cause["aliases"]),
                        "choices": choices, "victim": victim,
                        "decoy": decoy, "budget_s": BUDGET_S,
                        "mode": mode, "grounded": True},
        }
    except Exception:
        return {  # generate never raises and never returns None
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "service", "concept": "service",
            "file": "service.py", "line": 0, "commit": "",
            "hints": _hints("upstream timeout", "req-0000"),
            "front": "DRILL — name the exact ROOT CAUSE (one listed phrase).",
            "back": "Root cause: `upstream timeout`.",
            "payload": {"log": "", "cause": "upstream timeout",
                        "answer": "upstream timeout", "aliases": ["timeout"],
                        "choices": [c["key"] for c in CAUSES],
                        "victim": "req-0000", "decoy": "req-ffff",
                        "budget_s": BUDGET_S, "mode": "synthesized",
                        "grounded": False},
        }


generate = gen_pressure_drill


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def check(exercise: dict, submission: str) -> bool:
    """Pure phrase predicate: True iff submission names the card's cause."""
    payload = (exercise or {}).get("payload", {}) or {}
    cause_key = str(payload.get("cause", "") or "")
    cause = next((c for c in CAUSES if c["key"] == cause_key), None)
    if cause is None:
        return False
    text = str(submission if submission is not None else "")
    if not text.strip() or "\n" in text.strip():
        return False
    return normalize(text) in _answers_for(cause)


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact root-cause phrase match after ``normalize``; never raises."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        cause_key = str(payload.get("cause", "") or "")
        cause = next((c for c in CAUSES if c["key"] == cause_key), None)
        if cause is None:
            return _fail("Exercise payload is missing the root cause.")
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail(f"Name the exact root cause in under {BUDGET_S}s "
                          "(one listed phrase).")
        if "\n" in text.strip():
            return _fail("Reply with ONE phrase — a pasted log never isolates "
                         "the cause, however fast you paste it.")
        if check(exercise, submission):
            return {"pass": True, "score": 1.0,
                    "feedback": f"Correct: {cause_key} — inside the "
                                f"{BUDGET_S}s drill budget."}
        return _fail("Not the root cause — follow the victim request id; "
                     "WARN lines and the decoy request are noise.")
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — name one phrase.")


def render(exercise: dict) -> str:
    """Exercise widget: production log, countdown, root-cause answer box."""
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    budget = int((exercise.get("payload", {}) or {}).get("budget_s", BUDGET_S))
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p data-budget='{budget}'><b><span class='drill-clock'>{budget}</span>s</b> "
        f"drill budget (advisory — grading is exact-phrase).</p>"
        f"<pre>{front}</pre>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Exact root-cause phrase within the {budget}s drill "
        f"budget (case, quotes, and whitespace ignored; listed aliases "
        f"accepted) — herrings, decoy requests, and pasted logs never "
        f"count.</small></p></details>"
        f"<form method='post'><input name='answer' size='50' "
        f"placeholder='name the exact root cause'>"
        f"<button>Diagnose under pressure</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; anchor owned by groundwork/batch18.py."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Pressure drill <small>(feature)</small></h3>"
        "<p>Diagnose a production-style log against a 90s drill budget — "
        "follow the victim request id past WARN noise and a decoy failing "
        "request, then name the exact root cause. "
        "<code>groundwork/pressure.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (parent wires anchor via batch18.py)."""
    return {"id": "pressure-drill", "kind": "feature",
            "title": "Pressure drill",
            "blurb": "Diagnose a production-style log against a 90s clock — follow the victim request, not the noise.",
            "path": "/status", "anchor": "status-b18-pressure"}
