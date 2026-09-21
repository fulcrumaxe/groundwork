"""Rate-limit design exercise (type 71, F-48, bloom: evaluate).

The learner judges tradeoffs for a traffic profile under an abuse
scenario and submits five ``key=value`` lines (scope, window, burst,
retry, why). The rubric grader scores five independent points with
partial credit (``score = hits/5``, pass at half or more — rubric
family bar, types 5/6/24/25): scoped per-key plus global limits, a
concrete window, burst handling, ``429`` + ``Retry-After``, and a
reason. Static and deterministic, stdlib only.

``generate`` never returns None and never raises: thin input falls
back to the login profile on a generic ``api`` service.

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

TYPE_NUM = 71
TYPE_NAME = "ratelimit"
BLOOM = "evaluate"
STATUS_ANCHOR = "status-b11-ratelimit"

POINTS = ("scope", "window", "burst", "retry", "why")
_PASS_FRACTION = 0.5

_PROFILES = (
    {"id": "login", "service": "auth",
     "baseline": "20 req/min/user",
     "abuse": ("one IP tries 500 logins/min; a botnet spreads "
               "2000 req/min over 500 IPs (credential stuffing)")},
    {"id": "read-api", "service": "api",
     "baseline": "200 req/min/key",
     "abuse": ("scrapers pull 5000 pages/min from a handful of keys, "
               "starving legitimate readers")},
    {"id": "webhooks", "service": "ingest",
     "baseline": "bursty 1000 events/min",
     "abuse": ("a retry storm replays 10000 deliveries/min after "
               "an outage, overloading parsers")},
)

_WHY_WORDS = ("fair", "abuse", "capacity", "overload", "starv",
              "recover", "backoff", "legitimate", "neighbor")

_SCOPE_KEY_RE = re.compile(r"per[ -]?(ip|user|key|token)", re.IGNORECASE)
_WINDOW_RE = re.compile(
    r"\d+\s*(s|sec|secs|second|seconds|m|min|mins|minute|minutes|"
    r"h|hour|hours)\b", re.IGNORECASE)
_BURST_RE = re.compile(
    r"burst|token[\s_-]?bucket|leaky[\s_-]?bucket|allow\s+\d+\s+extra",
    re.IGNORECASE)
_RETRY_AFTER_RE = re.compile(r"retry[\s_-]?after", re.IGNORECASE)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _clean_service(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", str(name or "").lower()).strip("-")
    return cleaned or "api"


def _profile(ex_id):
    try:
        digest = hashlib.sha256(str(ex_id).encode()).hexdigest()
        return _PROFILES[int(digest[:2], 16) % len(_PROFILES)]
    except Exception:  # noqa: BLE001 — seeding must never raise
        return _PROFILES[0]


def _front_text(service: str, profile: dict) -> str:
    return (
        f"Design rate limits for `{service}` ({profile['id']}): legit "
        f"peak {profile['baseline']}; abuse: {profile['abuse']}. "
        "Submit five `key=value` lines: `scope=` (per-key AND global "
        "limits), `window=` (concrete window), `burst=` (burst handling), "
        "`retry=` (429 behavior), `why=` (one-line reason)."
    )


def _back_text(profile: dict) -> str:
    return (
        "scope=10/min per IP plus 1000/min global | window=60s fixed | "
        "burst=token bucket 5 | retry=429 with Retry-After: 60 | "
        "why=per-IP stops one abuser while the global cap guards total "
        "capacity; Retry-After forces backoff"
    )


def _hints() -> list[str]:
    return [
        "Scope both axes: one abuser (per-IP) and total capacity (global).",
        "Windows need numbers: `60s` beats `short`.",
        "Worked step: `retry=429 with Retry-After: 60` tells clients to back off.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a rate-limit card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        file = _concept_field(concept, "file", "") or "limits.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        profile = _profile(ex_id)
        service = _clean_service(name) if name else profile["service"]
        grounded = bool(name or any(str(l).strip() for l in snippet))
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", service),
            "concept": name or service, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": _front_text(service, profile),
            "back": _back_text(profile),
            "payload": {"service": service,
                        "profile": profile["id"],
                        "baseline": profile["baseline"],
                        "abuse": profile["abuse"],
                        "grounded": grounded},
        }
    except Exception:
        return {  # generate never raises and never returns None
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "api", "concept": "api",
            "file": "limits.py", "line": 0, "commit": "",
            "hints": _hints(),
            "front": _front_text("api", _PROFILES[0]),
            "back": _back_text(_PROFILES[0]),
            "payload": {"service": "api", "profile": "login",
                        "baseline": _PROFILES[0]["baseline"],
                        "abuse": _PROFILES[0]["abuse"],
                        "grounded": False},
        }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _keyed(text: str) -> dict:
    """Parse `key=value` lines; never raises."""
    out: dict = {}
    try:
        for line in str(text).splitlines():
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip().lower()
            if key in POINTS and key not in out:
                out[key] = val.strip()
    except Exception:  # noqa: BLE001 — parsing must never raise
        pass
    return out


def _misses(fields: dict) -> list[str]:
    """Rubric points the submission misses."""
    missed = []
    try:
        scope = fields.get("scope", "")
        if not (_SCOPE_KEY_RE.search(scope)
                and "global" in scope.lower()):
            missed.append("scoped per-key + global limits")
        if not _WINDOW_RE.search(fields.get("window", "")):
            missed.append("a concrete window with a number")
        if not _BURST_RE.search(fields.get("burst", "")):
            missed.append("burst handling")
        retry = fields.get("retry", "")
        if not ("429" in retry and _RETRY_AFTER_RE.search(retry)):
            missed.append("429 + Retry-After")
        why = fields.get("why", "").lower()
        if not any(w in why for w in _WHY_WORDS):
            missed.append("a reason (fairness, capacity, backoff, …)")
    except Exception:  # noqa: BLE001 — rubric must never raise
        return list(POINTS)
    return missed


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Rubric gate with partial credit; half or more passes."""
    _ = runner
    try:
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Submit five key=value lines "
                         "(scope, window, burst, retry, why).")
        fields = _keyed(text)
        if not fields:
            return _fail("Submit five key=value lines "
                         "(scope, window, burst, retry, why).")
        missed = _misses(fields)
        hits = len(POINTS) - len(missed)
        score = hits / len(POINTS)
        if score >= _PASS_FRACTION:
            if not missed:
                return {"pass": True, "score": 1.0,
                        "feedback": "Rate-limit rubric 5/5: scoped limits, "
                                    "sane window, burst plan, 429+Retry-After, "
                                    "reasoned."}
            return {"pass": True, "score": score,
                    "feedback": f"Rate-limit rubric {hits}/5 — "
                                f"tighten: {'; '.join(missed)}."}
        return {"pass": False, "score": score,
                "feedback": f"Rate-limit rubric {hits}/5 — miss: "
                            f"{'; '.join(missed)}."}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — "
                     "submit key=value lines.")


def render(exercise: dict) -> str:
    """Exercise widget: traffic profile plus key=value textarea."""
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
        f"<p><small>Name scoped limits, a concrete window, burst handling, "
        f"and 429 + Retry-After with a reason — partial credit per point, "
        f"half or more passes.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='70' "
        f"placeholder='scope=&#10;window=&#10;burst=&#10;retry=&#10;why='>"
        f"</textarea><br><button>Propose limits</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Rate-limit it <small>(feature)</small></h3>"
        "<p>Design rate limits for a traffic profile under an abuse "
        "scenario — per-key plus global scope, a concrete window, burst "
        "handling, and 429 + Retry-After with reasoning (rubric, partial "
        "credit, half-or-more passes). "
        "<code>groundwork/ratelimit.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "rate-limit-it", "kind": "feature",
            "title": "Rate-limit it",
            "blurb": "Pick per-key + global limits, a window, burst handling, and 429 + Retry-After — rubric-graded with partial credit.",
            "path": "/status", "anchor": "status-b11-ratelimit"}
