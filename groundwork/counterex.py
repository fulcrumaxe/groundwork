"""Counterexample-hunt drills (type 87, F-83, bloom: analyse).

State the belief, then break it: the card states one universal claim
about a real function ("`clamp` returns a truthy value for every
input"), shows the snippet, and asks for one concrete input
expression that breaks the claim. The back names the known breaker
and what actually happens.

Ground truth is measured, not invented: `generate` evaluates probe
inputs against the claim in a restricted namespace (same
``__builtins__``-subset pattern as `proptest.grade`) and records the
first breaker; `grade` replays the learner's submission the same way.
No breaker found (or no suitable def) yields an ungrounded card the
pipeline skips.

``generate`` never returns None and never raises.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``grade(exercise, submission, runner)`` (runner accepted, ignored —
pure stdlib like `proptest.grade`), ``render(exercise) -> html``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 87),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES) and
``groundwork/__main__.py`` (cmd_e2e fixture); status section and
tour entry live below.
"""
from __future__ import annotations

import ast
import hashlib
import html

TYPE_NUM = 87
TYPE_NAME = "counterexample-hunt"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b19-counterex"

SAFE_BUILTINS = {
    "abs": abs, "all": all, "any": any, "bool": bool, "dict": dict,
    "enumerate": enumerate, "filter": filter, "float": float,
    "frozenset": frozenset, "int": int, "isinstance": isinstance,
    "len": len, "list": list, "map": map, "max": max, "min": min,
    "range": range, "repr": repr, "reversed": reversed, "round": round,
    "set": set, "slice": slice, "sorted": sorted, "str": str,
    "sum": sum, "tuple": tuple, "zip": zip, "Exception": Exception,
    "ValueError": ValueError, "TypeError": TypeError,
    "IndexError": IndexError, "KeyError": KeyError,
}

PROBES = ("0", "1", "-1", "2", '""', '"x"', "[]", "[0]",
          "None", "True", "()")

MAX_PROBES = 6


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _seed(ex_id) -> int:
    try:
        return int(hashlib.sha256(str(ex_id).encode()).hexdigest(), 16)
    except Exception:  # noqa: BLE001 -- seeding must never raise
        return 0


def _target(code: str):
    """(func_name, arity) of the first public multi-arg def; else None."""
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return None
    try:
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue
            args = [a for a in node.args.args if a.arg not in ("self", "cls")]
            if len(args) >= 1:
                return (node.name, len(args))
        return None
    except Exception:  # noqa: BLE001
        return None


def _claims(func: str, arity: int) -> list:
    """(label, claim, check-name) rotated by seed at pick time."""
    return [
        ("truthy-myth",
         f"`{func}` returns a truthy value for every input.",
         "truthy"),
        ("never-raises-myth",
         f"`{func}` never raises for small inputs.",
         "no-raise"),
        ("identity-myth" if arity == 1 else "stable-myth",
         (f"`{func}` returns its input unchanged."
          if arity == 1 else
          f"`{func}` returns the same value for the same inputs twice."),
         "identity" if arity == 1 else "stable"),
    ]


def _exec_func(code: str, func: str):
    """Define func from code in a restricted namespace; (callable|None)."""
    try:
        globs: dict = {"__builtins__": SAFE_BUILTINS}
        exec(compile(code, "<exercise>", "exec"), globs)  # noqa: S102 -- restricted ns
        fn = globs.get(func)
        return fn if callable(fn) else None
    except Exception:  # noqa: BLE001 -- the snippet itself is on trial
        return None


def _value_of(text: str):
    """Probe expression -> (value, ok); literal first, restricted eval."""
    try:
        return (ast.literal_eval(text), True)
    except (ValueError, SyntaxError, TypeError, MemoryError,
            RecursionError):
        pass
    except Exception:  # noqa: BLE001
        return (None, False)
    try:
        globs: dict = {"__builtins__": SAFE_BUILTINS}
        return (eval(text, {"__builtins__": SAFE_BUILTINS}, {}), True)  # noqa: S307 -- literal-shaped
    except Exception:  # noqa: BLE001
        return (None, False)


def _trial(fn, value, arity: int, check: str):
    """(broken?, what-happened); never raises."""
    try:
        if check == "stable":
            if arity != 1:
                return (False, "needs one input")
            try:
                first, second = fn(value), fn(value)
            except Exception as exc:  # noqa: BLE001
                return (True, f"raised {type(exc).__name__}")
            if first != second:
                return (True, f"returned {first!r} then {second!r}")
            return (False, f"stable so far ({first!r} twice) — try again")
        if arity == 1:
            args = (value,)
        elif isinstance(value, tuple):
            args = value
        else:
            return (False, "needs one input per argument")
        try:
            result = fn(*args)
        except Exception as exc:  # noqa: BLE001 -- raising breaks truthy/identity
            if check == "no-raise":
                return (True, f"raised {type(exc).__name__}")
            return (True, f"raised {type(exc).__name__} instead of a value")
        return _check_result(result, value, check)
    except Exception as exc:  # noqa: BLE001
        return (False, f"harness fault: {exc}")


def _check_result(result, value, check: str):
    if check == "truthy":
        if bool(result) is True:
            return (False, f"returned {result!r} — claim survives; try again")
        return (True, f"returned {result!r} — falsy, claim broken")
    if check == "no-raise":
        return (False, f"returned {result!r} — claim survives; try again")
    if check == "identity":
        if result == value:
            return (False, f"returned {result!r} — unchanged, claim survives")
        return (True, f"returned {result!r} for {value!r} — claim broken")
    return (False, f"returned {result!r} — claim survives; try again")


def _find_breaker(code: str, func: str, arity: int, check: str,
                  seed: int):
    """First probe falsifying the check; (expr, what) or (None, "")."""
    try:
        fn = _exec_func(code, func)
        if fn is None:
            return (None, "")
        order = list(range(len(PROBES)))
        rng_seed = seed & 0xFFFFFFFF
        order = order[rng_seed % len(order):] + order[:rng_seed % len(order)]
        tried = 0
        for i in order:
            if tried >= MAX_PROBES:
                break
            tried += 1
            value, ok = _value_of(PROBES[i])
            if not ok:
                continue
            broken, what = _trial(fn, value, arity, check)
            if broken:
                return (PROBES[i], what)
        return (None, "")
    except Exception:  # noqa: BLE001 -- search never raises
        return (None, "")


def _hints() -> list[str]:
    return [
        "State the belief in your own words first.",
        "Try the edges: zero, empty, negative, None.",
        "One input expression is enough — then verify.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a counterexample-hunt card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        node_id = _concept_field(concept, "node_id", name)
        file = _concept_field(concept, "file", "") or "app.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        code = "\n".join(str(l) for l in snippet)
        found = _target(code)
        if not found:
            return _ungrounded(ex_id, name, file, line, commit)
        func, arity = found
        claims = _claims(func, arity)
        seed = _seed(ex_id)
        pick = claims[seed % len(claims)]
        for offset in range(len(claims)):
            label, claim, check = claims[(seed + offset) % len(claims)]
            breaker, what = _find_breaker(code, func, arity, check, seed)
            if breaker is not None:
                return {
                    "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
                    "bloom": BLOOM,
                    "concept_id": node_id or "counterex",
                    "concept": name or func, "file": file, "line": line,
                    "commit": commit,
                    "hints": _hints(),
                    "front": (f"Claim: {claim}\nBreak it with one input "
                              "expression.\n"
                              f"```python\n{code[:600]}\n```"),
                    "back": (f"Breaker: `{breaker}` — {what}"),
                    "payload": {"func": func, "arity": arity,
                                "claim": claim, "code": code[:2000],
                                "check": check, "choices": None,
                                "answer": breaker, "reference": breaker,
                                "grounded": True},
                }
        return _ungrounded(ex_id, name or func, file, line, commit)
    except Exception:
        return _ungrounded(ex_id, "", "app.py", 0, "")


def _ungrounded(ex_id, name, file, line, commit) -> dict:
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": "counterex",
        "concept": name or "counterex", "file": file, "line": line,
        "commit": commit, "hints": _hints(),
        "front": "No breakable claim found here.",
        "back": "Skipped by the pipeline.",
        "payload": {"func": "", "arity": 0, "claim": "", "code": "",
                    "check": "", "choices": None, "answer": "",
                    "reference": "", "grounded": False},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Replay the submitted input; falsifying the check passes."""
    _ = runner
    try:
        return _grade(exercise, submission)
    except Exception as exc:  # noqa: BLE001 -- grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    func = str(p.get("func", "") or "")
    code = str(p.get("code", "") or "")
    check = str(p.get("check", "") or "")
    try:
        arity = int(p.get("arity", 1))
    except (TypeError, ValueError):
        arity = 1
    text = str(submission if submission is not None else "").strip()
    if not text:
        return _fail("Submit one input expression that breaks the claim.")
    if not func or not code or not check:
        return _fail("No breakable claim recorded on this card.")
    value, ok = _value_of(text)
    if not ok:
        return _fail("That does not parse as an input — try a plain "
                     "value like 0, -1, \"\", or [0].")
    fn = _exec_func(code, func)
    if fn is None:
        return _fail("The shown code does not run here.")
    broken, what = _trial(fn, value, arity, check)
    if broken:
        return {"pass": True, "score": 1.0,
                "feedback": f"Claim broken — {what}."}
    return {"pass": False, "score": 0.0,
            "feedback": f"Claim survives: {what}."}


def render(exercise: dict) -> str:
    """Exercise widget: claim, snippet, one breaker input."""
    front = html.escape(str(exercise.get("front", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>One input that breaks the claim passes — replayed "
        f"live against the code.</small></p>"
        f"</details>"
        f"<form method='post'><label>One input that breaks it "
        f"(e.g. 0): <input name='answer' size='30'></label> "
        f"<button>Break it</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Counterexample hunting <small>(feature)</small></h3>"
        "<p>State the belief, then break it: name one input where the "
        "claim about a real function fails. "
        "<code>groundwork/counterex.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "counterexample-hunt", "kind": "feature",
            "title": "Counterexample hunting",
            "blurb": "State the belief, then break it: name one input where the claim about a real function fails.",
            "path": "/status", "anchor": STATUS_ANCHOR}
