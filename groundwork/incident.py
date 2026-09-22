"""Incident-replay drill (type 77, F-73, bloom: evaluate).

A past-outage scenario reconstructed from repo-history signals
(decisions, diff hunks, commit in ctx) is replayed as a practice drill:
the learner reads a shuffled 4-event timeline and submits five
``key=value`` lines (signal, detect, mitigate, prevent, order). The
rubric grader scores five independent points with partial credit
(``score = hits/5``, pass at half or more — rubric family bar, types
5/6/24/25/71): the alerting signal, the detection step, the mitigation,
the prevention, and the true chronological order. Static and
deterministic, stdlib only.

``generate`` never returns None and never raises: thin input falls back
to the bad-deploy scenario on a generic ``api`` service; the card is
flagged ungrounded and the pipeline skips it.

Plugin API: ``gen_incident_replay(ex_id, concept, snippet, ctx)``,
``generate`` (alias), ``render(exercise) -> html``,
``grade(exercise, submission, runner)``. Import-safe standalone: stdlib
only, no groundwork imports. Registration lives in
``groundwork/exercises.py`` (TYPES, GENERATORS, BLOOM_TYPES,
grade/render branches) and ``groundwork/pipeline.py``
(BLOOM_DEFAULT_TYPES); status section and tour entry live below.
"""

from __future__ import annotations

import hashlib
import html
import random

TYPE_NUM = 77
TYPE_NAME = "incident-replay"
BLOOM = "evaluate"
STATUS_ANCHOR = "status-b18-incident"

POINTS = ("signal", "detect", "mitigate", "prevent", "order")
_PASS_FRACTION = 0.5

_SCENARIOS = (
    {"id": "bad-deploy",
     "title": "bad deploy pages at 02:00",
     "signal": "error-rate alert fires after the deploy",
     "events": ("error-rate alert fires after the deploy",
                "on-call diffs the release and finds the breaking change",
                "rollback to the previous release restores service",
                "deploy freeze plus canary gate lands in the postmortem"),
     "signal_kw": ("error", "alert", "5xx", "deploy"),
     "detect_kw": ("diff", "bisect", "log", "release"),
     "mitigate_kw": ("rollback", "revert", "previous release"),
     "prevent_kw": ("canary", "freeze", "gate", "postmortem")},
    {"id": "secret-leak",
     "title": "leaked secret in the repo history",
     "signal": "secret-scan flags a committed API key",
     "events": ("secret-scan flags a committed API key",
                "on-call traces which deploys baked the key in",
                "the key is rotated and the history is purged",
                "pre-commit secret hook plus rotation runbook lands"),
     "signal_kw": ("scan", "leak", "flag", "key"),
     "detect_kw": ("trace", "history", "deploy", "blame"),
     "mitigate_kw": ("rotat", "revok", "purg"),
     "prevent_kw": ("pre-commit", "hook", "runbook", "rotation")},
    {"id": "retry-storm",
     "title": "retry storm after a webhook outage",
     "signal": "ingest latency alert as deliveries replay 10x",
     "events": ("ingest latency alert as deliveries replay 10x",
                "on-call reads the queue depth and finds the retry loop",
                "idempotency keys plus backoff drain the queue",
                "jittered backoff with a circuit breaker lands"),
     "signal_kw": ("latency", "alert", "replay", "storm", "queue"),
     "detect_kw": ("queue", "depth", "metric", "retry"),
     "mitigate_kw": ("idempoten", "backoff", "drain"),
     "prevent_kw": ("jitter", "breaker", "backoff", "circuit")},
)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _scenario(ex_id):
    try:
        digest = hashlib.sha256(str(ex_id).encode()).hexdigest()
        return _SCENARIOS[int(digest[:2], 16) % len(_SCENARIOS)]
    except Exception:  # noqa: BLE001 — seeding must never raise
        return _SCENARIOS[0]


def _shuffle(ex_id, events):
    order = list(range(len(events)))
    try:
        rng = random.Random(hashlib.sha256(str(ex_id).encode()).hexdigest())
        rng.shuffle(order)
    except Exception:  # noqa: BLE001 — shuffle must never raise
        pass
    return order


def _front_text(service: str, sc: dict, shown: list[str]) -> str:
    letters = "\n".join(f"{chr(65 + i)}. {ev}"
                        for i, ev in enumerate(shown))
    return (
        f"Replay this past outage on `{service}` ({sc['id']}: "
        f"{sc['title']}). These four timeline events are shuffled:\n"
        f"{letters}\nSubmit five `key=value` lines: `signal=` (what "
        "alerted), `detect=` (how on-call found the cause), "
        "`mitigate=` (what restored service), `prevent=` (what stops "
        "recurrence), `order=` (the true chronological letter "
        "sequence, e.g. `order=C A B D`)."
    )


def _check_text(sc: dict, order: list[str]) -> str:
    # chronological: event k sits at shown-position order.index(k)
    seq = " ".join(chr(65 + order.index(k)) for k in range(len(order)))
    ev = sc["events"]
    return (
        f"signal={ev[0]}\ndetect={ev[1]}\nmitigate={ev[2]}\n"
        f"prevent={ev[3]}\norder={seq}"
    )


def _hints() -> list[str]:
    return [
        "Signals alert, detections diagnose — keep them apart.",
        "Mitigation restores service; prevention stops the next one.",
        "Worked step: `order=` lists shown letters oldest-first.",
    ]


def gen_incident_replay(ex_id, concept, snippet, ctx) -> dict:
    """Build an incident-replay card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        file = _concept_field(concept, "file", "") or "incidents.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        sc = _scenario(ex_id)
        service = (_concept_field(concept, "file", "").split("/")[-1]
                   .rsplit(".", 1)[0]) if name else "api"
        order = _shuffle(ex_id, sc["events"])
        shown = [sc["events"][i] for i in order]
        grounded = bool(name or any(str(l).strip() for l in snippet))
        check = _check_text(sc, order)
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", "incident"),
            "concept": name or service, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": _front_text(service, sc, shown),
            "back": check,
            "check": check,
            "payload": {"service": service, "scenario": sc["id"],
                        "shown": shown, "order": order,
                        "signal_kw": list(sc["signal_kw"]),
                        "detect_kw": list(sc["detect_kw"]),
                        "mitigate_kw": list(sc["mitigate_kw"]),
                        "prevent_kw": list(sc["prevent_kw"]),
                        "check": check, "grounded": grounded},
        }
    except Exception:
        sc = _SCENARIOS[0]
        order = [0, 1, 2, 3]
        check = _check_text(sc, order)
        return {  # generate never raises and never returns None
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "incident", "concept": "api",
            "file": "incidents.py", "line": 0, "commit": "",
            "hints": _hints(),
            "front": _front_text("api", sc, list(sc["events"])),
            "back": check, "check": check,
            "payload": {"service": "api", "scenario": sc["id"],
                        "shown": list(sc["events"]), "order": order,
                        "signal_kw": list(sc["signal_kw"]),
                        "detect_kw": list(sc["detect_kw"]),
                        "mitigate_kw": list(sc["mitigate_kw"]),
                        "prevent_kw": list(sc["prevent_kw"]),
                        "check": check, "grounded": False},
        }


generate = gen_incident_replay


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


def _hits_kw(text: str, kws) -> bool:
    low = str(text or "").lower()
    return any(k.lower() in low for k in kws)


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Rubric gate with partial credit; half or more passes."""
    _ = runner
    try:
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Submit five key=value lines "
                         "(signal, detect, mitigate, prevent, order).")
        fields = _keyed(text)
        if not fields:
            return _fail("Submit five key=value lines "
                         "(signal, detect, mitigate, prevent, order).")
        p = (exercise or {}).get("payload", {}) or {}
        missed = []
        if not _hits_kw(fields.get("signal", ""), p.get("signal_kw", ())):
            missed.append("the alerting signal")
        if not _hits_kw(fields.get("detect", ""), p.get("detect_kw", ())):
            missed.append("how on-call found the cause")
        if not _hits_kw(fields.get("mitigate", ""), p.get("mitigate_kw", ())):
            missed.append("what restored service")
        if not _hits_kw(fields.get("prevent", ""), p.get("prevent_kw", ())):
            missed.append("what stops recurrence")
        want = " ".join(
            chr(65 + list(p.get("order", [0, 1, 2, 3])).index(k))
            for k in range(len(p.get("shown", [0, 1, 2, 3]))))
        got = " ".join(fields.get("order", "").upper().split())
        if got != want:
            missed.append(f"the true order (want `{want}`)")
        hits = len(POINTS) - len(missed)
        score = hits / len(POINTS)
        if score >= _PASS_FRACTION:
            if not missed:
                return {"pass": True, "score": 1.0,
                        "feedback": "Incident replay 5/5: signal, "
                                    "detection, mitigation, prevention, "
                                    "and order all correct."}
            return {"pass": True, "score": score,
                    "feedback": f"Incident replay {hits}/5 — "
                                f"tighten: {'; '.join(missed)}."}
        return {"pass": False, "score": score,
                "feedback": f"Incident replay {hits}/5 — miss: "
                            f"{'; '.join(missed)}."}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — "
                     "submit key=value lines.")


def render(exercise: dict) -> str:
    """Exercise widget: shuffled timeline plus key=value textarea."""
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
        f"<p><small>Name the signal, detection, mitigation, and "
        f"prevention plus the true timeline order — partial credit "
        f"per point, half or more passes.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='70' "
        f"placeholder='signal=&#10;detect=&#10;mitigate=&#10;prevent=&#10;order='>"
        f"</textarea><br><button>Replay incident</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; home is groundwork/batch18.py (path /status)."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Incident replay <small>(feature)</small></h3>"
        "<p>Replay a past outage as a practice drill — name the signal, "
        "detection, mitigation, and prevention plus the true timeline "
        "order (rubric, partial credit, half-or-more passes). "
        "<code>groundwork/incident.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "incident-replay", "kind": "feature",
            "title": "Incident replay",
            "blurb": "Replay a past outage — signal, detection, mitigation, prevention, and timeline order, rubric-graded.",
            "path": "/status", "anchor": "status-b18-incident"}
