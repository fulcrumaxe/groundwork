"""Webhook verification exercise (type 72, F-49, bloom: apply).

The learner implements ``verify_signature(secret, body, timestamp,
signature, now) -> bool``: recompute HMAC-SHA256 over
``timestamp.body``, compare with ``hmac.compare_digest``, and enforce
a 300s replay window. The grader imports the learner's function from
the submission text (``hmac``/``hashlib`` pre-imported, restricted
builtins, per-phase wall timeout) and runs four fixed vectors: valid
passes; tampered body, wrong secret, and replayed timestamp are all
rejected. No partial credit — a signature check that admits one
forgery admits them all. Static fixtures, stdlib only.

``generate`` never returns None and never raises: the fixture is
fully synthetic (secret, timestamps, and vectors seed from ``ex_id``),
so every input yields a card; thin input yields an ungrounded card
the pipeline skips.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches) and
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES); status section and
tour entry live below.
"""

from __future__ import annotations

import ast
import hashlib
import hmac
import html
import re
import threading

TYPE_NUM = 72
TYPE_NAME = "webhook"
BLOOM = "apply"
STATUS_ANCHOR = "status-b11-webhook"

TOLERANCE_S = 300
_PHASE_SECS = 5

_SAFE_BUILTINS = {
    "abs": abs, "len": len, "range": range, "str": str, "int": int,
    "bool": bool, "isinstance": isinstance,
}


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _clean_word(name: str) -> str:
    words = re.findall(r"[a-z0-9]+", str(name or "").lower())
    return "_".join(words) or "push"


def _fixture(ex_id, body: str) -> dict:
    """Deterministic secret, timestamps, and signature vectors."""
    try:
        secret = hashlib.sha256(
            ("webhook-secret:" + str(ex_id)).encode()).hexdigest()[:32]
        stamp = hashlib.sha256(
            ("webhook-ts:" + str(ex_id)).encode()).hexdigest()[:8]
        ts0 = 1700000000 + int(stamp, 16) % 1000000
    except Exception:  # noqa: BLE001 — seeding must never raise
        secret = "0" * 32
        ts0 = 1700000000
    valid_sig = hmac.new(secret.encode(), f"{ts0}.{body}".encode(),
                         hashlib.sha256).hexdigest()
    other_sig = hmac.new(("x" + secret).encode(), f"{ts0}.{body}".encode(),
                         hashlib.sha256).hexdigest()
    return {"secret": secret, "ts": ts0, "now": ts0, "body": body,
            "valid": {"ts": ts0, "sig": valid_sig},
            "tampered": {"body": body + " ", "ts": ts0, "sig": valid_sig},
            "wrong_secret": {"ts": ts0, "sig": other_sig},
            "replay": {"ts": ts0 - 3 * TOLERANCE_S, "sig": valid_sig}}


def _signed(secret, body, ts) -> str:
    """HMAC-SHA256 hex over `ts.body`; test/grade helper, never raises."""
    try:
        return hmac.new(str(secret).encode(), f"{int(ts)}.{body}".encode(),
                        hashlib.sha256).hexdigest()
    except (TypeError, ValueError):
        return ""


def _verify(secret, body, timestamp, signature, now) -> bool:
    """Reference check: HMAC over `timestamp.body`, digest compare, window."""
    try:
        ts = int(timestamp)
        moment = int(now)
    except (TypeError, ValueError):
        return False
    if abs(moment - ts) > TOLERANCE_S:
        return False
    expected = hmac.new(str(secret).encode(),
                        f"{ts}.{body}".encode(),
                        hashlib.sha256).hexdigest()
    try:
        return hmac.compare_digest(expected, str(signature))
    except (TypeError, ValueError):
        return False


_REFERENCE_SRC = (
    "def verify_signature(secret, body, timestamp, signature, now):\n"
    "    try:\n"
    "        ts = int(timestamp)\n"
    "        moment = int(now)\n"
    "    except (TypeError, ValueError):\n"
    "        return False\n"
    "    if abs(moment - ts) > 300:\n"
    "        return False\n"
    "    expected = hmac.new(str(secret).encode(),\n"
    "                        f\"{ts}.{body}\".encode(),\n"
    "                        hashlib.sha256).hexdigest()\n"
    "    try:\n"
    "        return hmac.compare_digest(expected, str(signature))\n"
    "    except (TypeError, ValueError):\n"
    "        return False\n"
)


def _front_text(body: str, secret_fp: str) -> str:
    return (
        "Verify this HMAC-signed webhook delivery. Shared-secret fixture "
        f"`{secret_fp}` (full secret travels with the vectors, never in "
        "your reply). Write "
        "`verify_signature(secret, body, timestamp, signature, now) -> bool`: "
        "recompute HMAC-SHA256 over `f\"{timestamp}.{body}\"`, compare in "
        "constant time, and reject timestamps outside a 300s window.\n"
        f"Sample body: `{body}` (`hmac` and `hashlib` are pre-imported)."
    )


def _hints() -> list[str]:
    return [
        "Sign `timestamp.body` — the dot matters, order matters.",
        "Compare digests with `hmac.compare_digest`, never `==`.",
        "Worked step: `abs(now - ts) <= 300` bounds replay without clocks.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a webhook-verify card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        file = _concept_field(concept, "file", "") or "webhooks.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        body = ('{"event":"%s"}' % _clean_word(name)) if name \
            else '{"event":"push"}'
        fix = _fixture(ex_id, body)
        grounded = bool(name or any(str(l).strip() for l in snippet))
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", "webhook"),
            "concept": name or "webhook", "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": _front_text(body, fix["secret"][:8] + "…"),
            "back": _REFERENCE_SRC,
            "payload": {"secret": fix["secret"], "body": body,
                        "ts": fix["ts"], "now": fix["now"],
                        "valid": fix["valid"], "tampered": fix["tampered"],
                        "wrong_secret": fix["wrong_secret"],
                        "replay": fix["replay"],
                        "tolerance": TOLERANCE_S,
                        "reference": _REFERENCE_SRC,
                        "grounded": grounded},
        }
    except Exception:
        return {  # generate never raises and never returns None
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "webhook", "concept": "webhook",
            "file": "webhooks.py", "line": 0, "commit": "",
            "hints": _hints(),
            "front": _front_text('{"event":"push"}', "00000000…"),
            "back": _REFERENCE_SRC,
            "payload": {"secret": "0" * 32, "body": '{"event":"push"}',
                        "ts": 1700000000, "now": 1700000000,
                        "valid": {"ts": 1700000000, "sig": ""},
                        "tampered": {"body": " ", "ts": 1700000000, "sig": ""},
                        "wrong_secret": {"ts": 1700000000, "sig": ""},
                        "replay": {"ts": 1699999100, "sig": ""},
                        "tolerance": TOLERANCE_S,
                        "reference": _REFERENCE_SRC, "grounded": False},
        }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _load_verify(text: str):
    """Import verify_signature from submission text with a timeout."""
    box: dict = {}

    def target() -> None:
        try:
            namespace: dict = {"__builtins__": dict(_SAFE_BUILTINS),
                               "hashlib": hashlib, "hmac": hmac}
            exec(compile(text, "<submission>", "exec"), namespace)  # noqa: S102
            fn = namespace.get("verify_signature")
            box["fn"] = fn if callable(fn) else None
        except Exception as exc:  # noqa: BLE001 — report, don't raise
            box["error"] = f"{type(exc).__name__}: {exc}"

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(_PHASE_SECS)
    if thread.is_alive():
        return None, "did not finish"
    if "error" in box:
        return None, box["error"]
    if box.get("fn") is None:
        return None, "no callable verify_signature"
    return box["fn"], ""


def _call(fn, secret, body, ts, sig, now):
    """One vector call with a wall timeout; (timed_out, result)."""
    box: dict = {}

    def target() -> None:
        try:
            box["out"] = bool(fn(secret, body, ts, sig, now))
        except Exception:  # noqa: BLE001 — exceptions count as reject
            box["out"] = False

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(_PHASE_SECS)
    if thread.is_alive():
        return True, False
    return False, box.get("out", False)


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Four-vector signature gate; no partial credit."""
    _ = runner
    try:
        return _grade(exercise, submission)
    except Exception as exc:  # noqa: BLE001 — grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    secret = p.get("secret")
    body = p.get("body", "")
    now = p.get("now")
    vectors = {k: p.get(k) for k in
               ("valid", "tampered", "wrong_secret", "replay")}
    text = str(submission if submission is not None else "")
    if not text.strip():
        return _fail("Submit verify_signature — valid passes, forgeries fail.")
    if not secret or now is None or any(not isinstance(v, dict)
                                        for v in vectors.values()):
        return _fail("No signature vectors recorded on this card.")
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return _fail("Submission does not parse — resubmit valid Python.")
    if "verify_signature" not in {
            n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}:
        return _fail("Define `verify_signature(secret, body, timestamp, "
                     "signature, now)`.")
    fn, err = _load_verify(text)
    if fn is None:
        return _fail(f"Submission failed to load ({err}; hmac and hashlib "
                      "are pre-imported, no import needed).")
    timed_out, ok_valid = _call(fn, secret, body,
                                vectors["valid"]["ts"],
                                vectors["valid"]["sig"], now)
    if timed_out or not ok_valid:
        return _fail("The valid delivery must verify True.")
    names = {"tampered": "tampered body", "wrong_secret": "wrong secret",
             "replay": "replayed timestamp"}
    for key, label in names.items():
        vec = vectors[key]
        vec_body = vec.get("body", body)
        timed_out, out = _call(fn, secret, vec_body, vec.get("ts"),
                               vec.get("sig"), now)
        if timed_out or out:
            return _fail(f"Forged delivery accepted ({label}) — reject it.")
    return {"pass": True, "score": 1.0,
            "feedback": "All four vectors green: valid passes, "
                        "forgeries rejected."}


def render(exercise: dict) -> str:
    """Exercise widget: webhook spec plus verifier textarea."""
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
        f"<p><small>All four signature vectors must verify correctly — "
        f"valid passes, tampered body, wrong secret, and replayed "
        f"timestamp all rejected; no partial credit.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='12' cols='70' "
        f"placeholder='def verify_signature(secret, body, timestamp, "
        f"signature, now):'>"
        f"</textarea><br><button>Verify vectors</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Webhook verify <small>(feature)</small></h3>"
        "<p>Verify an HMAC-signed webhook — valid passes, tampered body, "
        "wrong secret, and replayed timestamp all rejected (constant-time "
        "compare, 300s replay window; no partial credit). "
        "<code>groundwork/webhook.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "webhook-verify", "kind": "feature",
            "title": "Webhook verify",
            "blurb": "Verify an HMAC-signed webhook — valid passes, tampered, wrong-secret, and replayed deliveries rejected.",
            "path": "/status", "anchor": "status-b11-webhook"}
