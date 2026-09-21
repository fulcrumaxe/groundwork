"""Idempotency double-run exercise (type 70, F-47, bloom: modify).

The learner rewrites a non-idempotent handler into a re-runnable one:
``handle(store, event, emit)`` must apply its effect exactly once per
key. The grader runs the submitted handler twice on the same store
with the same key (same end state AND zero new side effects), then
checks liveness on fresh stores (same key reproduces the first run;
a distinct key still applies and records its own key). All-or-nothing
1.0/0.0 — a retry that double-charges fails the card. Execution is
in-process with a restricted-builtins namespace and a per-phase wall
timeout (``runner`` accepted and ignored, containerize pattern).

``generate`` never returns None and never raises: thin input yields
an ungrounded fallback card the pipeline skips.

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
import copy
import hashlib
import html
import re
import threading

TYPE_NUM = 70
TYPE_NAME = "idempotency-fix"
BLOOM = "modify"
STATUS_ANCHOR = "status-b11-idempot"

_PHASE_SECS = 5

_SAFE_BUILTINS = {
    "len": len, "range": range, "str": str, "int": int,
    "float": float, "bool": bool, "dict": dict, "list": list,
    "set": set, "tuple": tuple, "isinstance": isinstance,
    "enumerate": enumerate, "sorted": sorted, "min": min, "max": max,
}

E2E = [
    "def handle(store, event, emit):\n"
    "    seen = store.setdefault(\"seen\", set())\n"
    "    if event[\"key\"] in seen:\n"
    "        return\n"
    "    seen.add(event[\"key\"])\n"
    "    store.setdefault(\"log\", []).append(event[\"item\"])\n"
    "    emit(\"charged\")\n",
    "def handle(store, event, emit):\n"
    "    items = store.setdefault(\"items\", {})\n"
    "    if event[\"key\"] not in items:\n"
    "        items[event[\"key\"]] = event[\"item\"]\n"
    "        emit(\"charged\")\n",
    "def handle(store, event, emit):\n"
    "    items = store.setdefault(\"items\", {})\n"
    "    if event[\"key\"] in items:\n"
    "        return\n"
    "    items[event[\"key\"]] = event[\"item\"]\n"
    "    emit(\"charged\")\n",
]


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _func_name(name: str) -> str:
    cleaned = re.sub(r"\W", "_", str(name or "")).strip("_") or "handle"
    if cleaned[0].isdigit():
        cleaned = "handle_" + cleaned
    return cleaned or "handle"


def _event_key(ex_id) -> str:
    try:
        digest = hashlib.sha256(str(ex_id).encode()).hexdigest()[:8]
        return "evt-" + digest
    except Exception:  # noqa: BLE001 — seeding must never raise
        return "evt-00000000"


def _starter(func: str) -> str:
    return (
        f"def {func}(store, event, emit):\n"
        "    store.setdefault(\"log\", []).append(event[\"item\"])\n"
        "    emit(\"charged\")\n"
    )


def _hints() -> list[str]:
    return [
        "Retry with the same key must change nothing the second time.",
        "Record which keys you already applied — then check before acting.",
        "Worked step: keep a `seen` set; return early on repeats.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build an idempotency card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        file = _concept_field(concept, "file", "") or "handlers.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        if name or any(str(l).strip() for l in snippet):
            func = _func_name(name or "handle")
            grounded = True
        else:
            func = "count"
            grounded = False
        key = _event_key(ex_id)
        starter = _starter(func)
        front = (
            f"Make `{func}(store, event, emit)` re-runnable: applying "
            f"event key `{key}` twice must leave the same end state with "
            "no duplicate side effects, and a fresh key must still apply.\n"
            f"```python\n{starter}```"
        )
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", func),
            "concept": name or func, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": front, "back": E2E[0],
            "payload": {"key": key, "handler": func, "starter": starter,
                        "grounded": grounded},
        }
    except Exception:
        return {  # generate never raises and never returns None
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "count", "concept": "count",
            "file": "handlers.py", "line": 0, "commit": "",
            "hints": _hints(),
            "front": "Make the handler re-runnable for a repeated key.",
            "back": E2E[0],
            "payload": {"key": "evt-00000000", "handler": "count",
                        "starter": _starter("count"), "grounded": False},
        }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _defines_handler(text: str, handler: str) -> bool:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return False
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name == handler for n in ast.walk(tree))


def _run_phase(fn, store: dict, event: dict, effects: list) -> tuple:
    """Run fn(store, event, emit) with a wall timeout; never raises.

    Returns (timed_out, error_message). State changes on timeout are
    discarded by the caller comparing snapshots.
    """
    box: dict = {}

    def target() -> None:
        try:
            fn(store, event, lambda e: effects.append(e))
        except Exception as exc:  # noqa: BLE001 — report, don't raise
            box["error"] = f"{type(exc).__name__}: {exc}"

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(_PHASE_SECS)
    if thread.is_alive():
        return True, ""
    return False, box.get("error", "")


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Double-run gate: same state, no duplicate effects, liveness."""
    _ = runner
    try:
        return _grade(exercise, submission)
    except Exception as exc:  # noqa: BLE001 — grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    handler = str(p.get("handler", "") or "")
    key = str(p.get("key", "") or "")
    text = str(submission if submission is not None else "")
    if not text.strip():
        return _fail("Submit the re-runnable handler.")
    if not handler or not key:
        return _fail("No handler recorded on this card.")
    if not _defines_handler(text, handler):
        return _fail(f"Define `def {handler}(store, event, emit):`.")
    namespace: dict = {"__builtins__": dict(_SAFE_BUILTINS)}
    try:
        exec(compile(text, "<submission>", "exec"), namespace)  # noqa: S102
    except Exception as exc:
        return _fail(f"Submission failed to load ({exc}).")
    fn = namespace.get(handler)
    if not callable(fn):
        return _fail(f"`{handler}` is not callable.")
    item = {"name": "widget", "price": 9}
    store: dict = {}
    effects: list = []
    event = {"key": key, "item": item}
    timed_out, err = _run_phase(fn, store, event, effects)
    if timed_out:
        return _fail("Handler did not finish — check for endless loops.")
    if err:
        return _fail(f"First run raised: {err[:200]}")
    state1 = copy.deepcopy(store)
    effects1 = len(effects)
    timed_out, err = _run_phase(fn, store, event, effects)
    if timed_out:
        return _fail("Retry did not finish — check for endless loops.")
    if err:
        return _fail(f"Retry raised: {err[:200]}")
    if store != state1:
        return _fail("Retry changed the end state — apply once per key.")
    if len(effects) != effects1:
        return _fail("Retry caused duplicate side effects.")
    fresh: dict = {}
    fresh_effects: list = []
    timed_out, err = _run_phase(fn, fresh, dict(event), fresh_effects)
    if timed_out or err:
        return _fail("Fresh-store run failed — handler must stand alone.")
    if fresh != state1:
        return _fail("Same key on a fresh store must reproduce the first run.")
    other: dict = {}
    other_effects: list = []
    event2 = {"key": key + "-again", "item": {"name": "gadget", "price": 4}}
    timed_out, err = _run_phase(fn, other, event2, other_effects)
    if timed_out or err:
        return _fail("A fresh key must still apply cleanly.")
    if other == {}:
        return _fail("A fresh key must still apply — no-op rejected.")
    if other == state1:
        return _fail("The key must matter — a fresh key must record itself.")
    return {"pass": True, "score": 1.0,
            "feedback": "Double-run green: same state, no duplicates, keys apply."}


def render(exercise: dict) -> str:
    """Exercise widget: handler spec plus starter textarea."""
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    starter = html.escape(str((exercise.get("payload", {}) or {})
                              .get("starter", "")))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Double-run gate: your handler runs twice on the same "
        f"store with the same key — same end state and no duplicate side "
        f"effects; a fresh key must still apply; no partial credit.</small>"
        f"</p></details>"
        f"<form method='post'><textarea name='answer' rows='12' cols='70'>"
        f"{starter}</textarea><br><button>Run twice</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Idempotency double-run <small>(feature)</small></h3>"
        "<p>Make a webhook handler re-runnable — the grader runs it twice "
        "on the same store with the same key and needs the same end state "
        "plus zero duplicate side effects (key-based dedupe or upsert; no "
        "partial credit). <code>groundwork/idempot.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "idempotency-double-run", "kind": "feature",
            "title": "Idempotency double-run",
            "blurb": "Make the handler re-runnable — the grader runs it twice and both runs must agree.",
            "path": "/status", "anchor": "status-b11-idempot"}
