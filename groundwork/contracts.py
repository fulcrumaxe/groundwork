"""Contract authoring (type 90, F-86, bloom: create).

The card shows a function plus measured input/output pairs and asks
for two one-liners: ``requires(x)`` (when it may be called) and
``ensures(x, out)`` (what holds after). Both predicates run against
the measured pairs plus one planted mutant in a restricted namespace
(the counterex ``__builtins__``-subset precedent); requires must
accept every valid input and reject a failing one, ensures must
accept every measured pair and reject the mutant. Both halves must
pass (the type-84 shape); score is the mean.

Only single-positional-parameter public functions qualify, measured
with JSON-scalar probes. Anything else — no def, unmeasurable body,
unsynthesizable reference — yields an ungrounded card the pipeline
skips. ``generate`` never returns None and never raises.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``grade(exercise, submission, runner)`` (runner accepted, ignored),
``render(exercise) -> html``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 90),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES),
``groundwork/cards.py`` (two-line textarea widget) and
``groundwork/__main__.py`` (cmd_e2e fixture); status section and
tour entry live below.
"""
from __future__ import annotations

import ast
import html

TYPE_NUM = 90
TYPE_NAME = "contract-author"
BLOOM = "create"
STATUS_ANCHOR = "status-b20-contracts"

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

_PROBES = ("bob", "", "ann", 0, 1, 2, -1, 3.5, True, None, "x", 7)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _target(code: str):
    """First public single-arg def: (name, source) else (None, None)."""
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return (None, None)
    try:
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if node.name.startswith("_"):
                continue
            pos = [a for a in node.args.args]
            if len(pos) != 1 or node.args.vararg or node.args.kwarg:
                continue
            try:
                src = ast.get_source_segment(code, node) or ""
            except Exception:  # noqa: BLE001
                src = ""
            if src:
                return (node.name, src)
        return (None, None)
    except Exception:  # noqa: BLE001
        return (None, None)


def _exec_func(source: str, func: str):
    """Define func from source in a restricted namespace; None on failure."""
    try:
        globs: dict = {"__builtins__": SAFE_BUILTINS}
        exec(compile(source, "<exercise>", "exec"), globs)  # noqa: S102 -- restricted ns
        fn = globs.get(func)
        return fn if callable(fn) else None
    except Exception:  # noqa: BLE001
        return None


def _scalar(value) -> bool:
    return value is None or isinstance(value, (bool, int, float, str))


def _measure(fn):
    """(valid pairs, invalid inputs) over the probe pool; never raises."""
    valid, invalid, seen = [], [], set()
    try:
        for probe in _PROBES:
            try:
                out = fn(probe)
            except Exception:  # noqa: BLE001 -- probe fails are data
                if _scalar(probe) and probe not in seen:
                    seen.add(probe)
                    invalid.append(probe)
                continue
            if not _scalar(out) or not _scalar(probe):
                continue
            if probe in seen:
                continue
            seen.add(probe)
            valid.append([probe, out])
            if len(valid) >= 4 and invalid:
                break
        return (valid, invalid)
    except Exception:  # noqa: BLE001
        return ([], [])


def _mutant_out(outs):
    """A wrong output distinct from every measured one; None if impossible."""
    try:
        first = outs[0]
        cand = (first + 1 if isinstance(first, int) and not isinstance(first, bool)
                else first + "!" if isinstance(first, str)
                else str(first) + "!")
        return cand if all(c != cand for c in outs) else None
    except Exception:  # noqa: BLE001
        return None


def _pred_ok(expr: str, bindings: dict) -> bool:
    """Expression evaluates truthy under bindings; False on any failure."""
    try:
        if not isinstance(expr, str) or not expr.strip():
            return False
        code = compile(expr.strip(), "<contract>", "eval")
        globs: dict = {"__builtins__": SAFE_BUILTINS}
        return bool(eval(code, globs, dict(bindings)))  # noqa: S307 -- restricted ns
    except Exception:  # noqa: BLE001
        return False


def _requires_ok(expr, valid, invalid) -> bool:
    try:
        for x, _ in valid:
            if not _pred_ok(expr, {"x": x}):
                return False
        if invalid and all(_pred_ok(expr, {"x": v}) for v in invalid):
            return False
        return True
    except Exception:  # noqa: BLE001
        return False


def _ensures_ok(expr, valid, mutant) -> bool:
    try:
        for x, out in valid:
            if not _pred_ok(expr, {"x": x, "out": out}):
                return False
        if mutant is not None and _pred_ok(expr, {"x": mutant[0], "out": mutant[1]}):
            return False
        return True
    except Exception:  # noqa: BLE001
        return False


def _reference(valid, invalid, mutant):
    """Passing-by-construction reference pair; None when impossible."""
    try:
        if invalid:
            conds = " and ".join(f"x != {v!r}" for v in invalid)
        else:
            conds = "True"
        outs = " or ".join(f"out == {o!r}" for _, o in valid)
        req, ens = f"({conds})", f"({outs})"
        if not _requires_ok(req, valid, invalid):
            return None
        if not _ensures_ok(ens, valid, mutant):
            return None
        return (req, ens)
    except Exception:  # noqa: BLE001
        return None


def _hints() -> list:
    return [
        "Line 1 needs requires(x); line 2 needs ensures(x, out).",
        "requires accepts every measured input and rejects a failing one.",
        "ensures accepts every measured pair and rejects the mutant.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a contract-author card; never None, never raises."""
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
        func, source = _target(code)
        if func is None:
            return _ungrounded(ex_id, name, file, line, commit)
        fn = _exec_func(source, func)
        if fn is None:
            return _ungrounded(ex_id, name, file, line, commit)
        valid, invalid = _measure(fn)
        if len(valid) < 2:
            return _ungrounded(ex_id, name, file, line, commit)
        mutant = None
        mout = _mutant_out([o for _, o in valid])
        if mout is not None:
            mutant = [valid[0][0], mout]
        ref = _reference(valid, invalid, mutant)
        if ref is None:
            return _ungrounded(ex_id, name, file, line, commit)
        pairs = "\n".join(f"{func}({x!r}) -> {o!r}" for x, o in valid)
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": node_id or "contracts",
            "concept": name or "contracts", "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": (f"Author the contract for `{func}`.\n"
                      f"```python\n{source[:600]}\n```\n"
                      f"Measured:\n{pairs}\n"
                      "Line 1: requires(x) — when may it be called?\n"
                      "Line 2: ensures(x, out) — what holds after?"),
            "back": (f"requires: {ref[0]} — accepts the measured inputs.\n"
                     f"ensures: {ref[1]} — accepts the measured pairs, "
                     "rejects the mutant."),
            "payload": {"valid": valid, "invalid": invalid,
                        "mutant": mutant, "reference": f"{ref[0]}\n{ref[1]}",
                        "grounded": True},
        }
    except Exception:
        return _ungrounded(ex_id, "", "app.py", 0, "")


def _ungrounded(ex_id, name, file, line, commit) -> dict:
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": "contracts",
        "concept": name or "contracts", "file": file, "line": line,
        "commit": commit, "hints": _hints(),
        "front": "No measurable single-argument function found here.",
        "back": "Skipped by the pipeline.",
        "payload": {"valid": [], "invalid": [], "mutant": None,
                    "reference": "", "grounded": False},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _split(submission) -> tuple:
    try:
        lines = str(submission or "").splitlines()
        req = lines[0] if len(lines) > 0 else ""
        ens = lines[1] if len(lines) > 1 else ""
        return (req, ens)
    except Exception:  # noqa: BLE001
        return ("", "")


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Both halves must pass; score is the mean."""
    _ = runner
    try:
        return _grade(exercise, submission)
    except Exception as exc:  # noqa: BLE001 -- grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    valid = p.get("valid") or []
    invalid = p.get("invalid") or []
    mutant = p.get("mutant")
    if not valid:
        return _fail("No contract staged on this card.")
    if not str(submission or "").strip():
        return _fail("Author both lines — requires, then ensures.")
    req, ens = _split(submission)
    req_ok = _requires_ok(req, valid, invalid)
    ens_ok = _ensures_ok(ens, valid, mutant)
    score = round(((1.0 if req_ok else 0.0) + (1.0 if ens_ok else 0.0)) / 2, 2)
    if req_ok and ens_ok:
        return {"pass": True, "score": score,
                "feedback": "Contract holds — measured cases and mutant agree."}
    bits = []
    if not req_ok:
        bits.append("requires misses a measured input or keeps a failing one")
    if not ens_ok:
        bits.append("ensures misses a measured pair or keeps the mutant")
    return {"pass": False, "score": score,
            "feedback": "Not yet — " + "; ".join(bits) + "."}


def disclosure() -> str:
    """One-line grading contract (also copied into the grading table)."""
    return ("Author requires/ensures one-liners — each must accept every "
            "measured case and reject the planted mutant; both halves "
            "must pass.")


def render(exercise: dict) -> str:
    """Exercise widget: contract question plus a two-line answer box."""
    p = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    _ = p
    return (
        f"<article><h3>{type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>{html.escape(disclosure())}</small></p>"
        f"</details>"
        f"<form method='post'><textarea name='answer' rows='3' cols='70' "
        f"placeholder='requires(x)…, then ensures(x, out)…'></textarea><br>"
        f"<button>Author it</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Contract authoring <small>(feature)</small></h3>"
        "<p>Author requires/ensures one-liners graded live against "
        "measured tests. Type 90 drills design-by-contract on the Due "
        "queue — <code>groundwork/contracts.py</code> measures probe "
        "pairs, plants one mutant, and both halves must pass.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "contract-author", "kind": "feature",
            "title": "Contract authoring",
            "blurb": "Write requires/ensures one-liners; measured tests grade them.",
            "path": "/due", "anchor": "up-next"}
