"""Input-validation audit: list unvalidated inputs (F-28, type 51).

Bloom: analyse. The learner reads one function and lists which inputs
reach sensitive sinks without validation; graded against a static
checklist with tolerant normalization and per-item partial credit.

AST-based and pure: function params/inputs vs validation constructs
(if/try/assert/regex/length checks) vs sink calls
(eval/exec/open/subprocess/SQL). No sandbox runner. Stdlib only
(ast/html), no groundwork imports: import-safe standalone.

generate() returns None when no function is found (documented, never
raises); the pipeline must skip None cards. A function
that parses but yields no unvalidated input returns a card with
grounded=False, which the existing grounded check already drops.

Plugin API: generate(ex_id, concept, snippet, ctx),
render(exercise) -> html, grade(exercise, submission, runner).
Registration lives in groundwork/exercises.py (TYPES, GENERATORS,
BLOOM_TYPES); pipeline BLOOM_DEFAULT_TYPES["analyse"] gains 51 with no
harness/mutation guard (pure checklist, like type 29).

Sibling contrast: logretro (29) is the checklist-graded template whose
normalization this mirrors; errbranch (28) is the fail-closed model.
"""
from __future__ import annotations

import ast
import html

TYPE_NUM = 51
TYPE_NAME = "input-validation"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b9-inputaudit"

SINKS = ("eval", "exec", "open", "subprocess", "sql")
_SUBPROCESS_CALLS = {"call", "run", "Popen", "check_output", "check_call"}
_OS_CALLS = {"system", "popen"}
_SQL_CALLS = {"execute", "executemany", "executescript"}
_VALID_RE_CALLS = {"match", "search", "fullmatch"}

_MAX_ITEMS = 4


def _func_node(src: str):
    """First top-level function in src, or None (never raises)."""
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node
    return None


def _inputs_of(fn) -> list[str]:
    """Params (minus self/cls) plus input()/sys.argv assignees, in order."""
    names: list[str] = []
    args = list(getattr(fn.args, "posonlyargs", [])) + list(fn.args.args)
    args += list(fn.args.kwonlyargs)
    for a in args:
        if a.arg not in ("self", "cls") and a.arg not in names:
            names.append(a.arg)
    for node in ast.walk(fn):
        if not isinstance(node, ast.Assign):
            continue
        ids = {n.id for n in ast.walk(node.value)
               if isinstance(n, ast.Name)}
        if "input" in ids or "argv" in ids:
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id not in names:
                    names.append(t.id)
    return names


def _names_under(node) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _validated(fn, inputs: set[str]) -> set[str]:
    """Inputs appearing in a validation construct (documented rule).

    Counts as validated: named in an if/assert test, used anywhere
    under a try (guarded use), passed to re.match/search/fullmatch,
    or measured with len() inside an if/assert test.
    """
    ok: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, (ast.If, ast.Assert)):
            ok |= _names_under(node.test) & inputs
            for sub in ast.walk(node.test):
                if (isinstance(sub, ast.Call)
                        and isinstance(sub.func, ast.Name)
                        and sub.func.id == "len"):
                    ok |= _names_under(sub) & inputs
        elif isinstance(node, ast.Try):
            ok |= _names_under(node) & inputs
        elif isinstance(node, ast.Call):
            f = node.func
            base = f.attr if isinstance(f, ast.Attribute) else (
                f.id if isinstance(f, ast.Name) else "")
            if base in _VALID_RE_CALLS:
                ok |= _names_under(node) & inputs
    return ok


def _sink_label(call) -> str | None:
    """Sink label for a call node, or None when not a sink."""
    f = call.func
    if isinstance(f, ast.Name):
        if f.id in ("eval", "exec", "open", "compile"):
            return f.id
        return None
    if isinstance(f, ast.Attribute):
        if isinstance(f.value, ast.Name):
            if (f.value.id == "subprocess"
                    and f.attr in _SUBPROCESS_CALLS):
                return "subprocess." + f.attr
            if f.value.id == "os" and f.attr in _OS_CALLS:
                return "os." + f.attr
        if f.attr in _SQL_CALLS:
            return "sql." + f.attr
    return None


def _reaches(fn, inputs: set[str]) -> dict:
    """Map each input to (sink label, call line) for its first sink use."""
    hits: dict = {}
    for node in ast.walk(fn):
        if not isinstance(node, ast.Call):
            continue
        label = _sink_label(node)
        if label is None:
            continue
        for name in _names_under(node) & inputs:
            hits.setdefault(name, (label, node.lineno))
    return hits


def _concept_field(concept, name: str, default=""):
    return getattr(concept, name, default) or default


def _hints(concept, snippet: list[str], first: dict) -> list[str]:
    where = f"{concept.file}:{concept.line}" if getattr(
        concept, "line", 0) else getattr(concept, "file", "")
    pointer = (f"Look at {where}: `{snippet[0].strip()}`"
               if snippet and where else "Re-read the snippet.")
    return [f"Trace each input to its sink: {', '.join(SINKS)}. "
            f"An input is safe only with an if/try/assert/regex/length "
            f"check on it first.",
            pointer,
            f"Worked step: `{first['name']}` reaches "
            f"`{first['sink']}` (line {first['line']}) unvalidated. "
            f"Now list the rest."]


def generate(ex_id, concept, snippet, ctx):
    """Build the type-51 card; None when no function found, never raises."""
    try:
        ctx = ctx or {}
        src = "\n".join(snippet or []) or str(ctx.get("code_block", "") or "")
        fn = _func_node(src)
        if fn is None:
            return None  # no function to audit: caller skips this card
        inputs = _inputs_of(fn)
        hits = _reaches(fn, set(inputs))
        valid = _validated(fn, set(inputs))
        bad = [n for n in inputs if n in hits and n not in valid]
        items = [{"id": i, "name": n, "sink": hits[n][0],
                  "line": hits[n][1]}
                 for i, n in enumerate(bad[:_MAX_ITEMS])]
        grounded = bool(items)
        lines = src.splitlines()
        numbered = "\n".join(f"{n}: {l}" for n, l in enumerate(lines, 1))
        want = "\n".join(f"{it['id']}={it['name']}" for it in items)
        first = items[0] if items else {"name": "—", "sink": "—", "line": 0}
        hints = _hints(concept, list(snippet or []), first)
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", ""),
            "concept": _concept_field(concept, "name", ""),
            "file": _concept_field(concept, "file", ""),
            "line": _concept_field(concept, "line", 0),
            "commit": ctx.get("commit", ""),
            "hints": hints,
            "front": ("Audit the inputs: list every input that reaches a "
                      f"sensitive sink ({', '.join(SINKS)}) WITHOUT "
                      f"validation — one name per line.\n"
                      f"```python\n{numbered[:800]}\n```"),
            "back": want,
            "payload": {"checklist": items, "sinks": list(SINKS),
                        "grounded": grounded},
        }
    except Exception:  # noqa: BLE001 — generate never raises
        return None


def _norm_name(raw: str) -> str:
    """Case/whitespace fold like logretro (identifiers: lower + strip)."""
    return str(raw).strip().strip("`'\"").lower()


def _parse_names(submission) -> list[str]:
    """Bare names (comma/semicolon/newline separated); id=name also ok."""
    text = str(submission if submission is not None else "")
    text = text.replace(",", "\n").replace(";", "\n")
    out: list[str] = []
    for chunk in text.splitlines():
        if "=" in chunk:
            chunk = chunk.split("=", 1)[1]
        name = _norm_name(chunk)
        if name:
            out.append(name)
    return out


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Checklist match: pass iff the unvalidated set matches exactly.

    Partial score = hits / max(len(expected), len(given)). Empty or
    hostile submissions fail closed, never raise; runner unused (pure).
    """
    _ = runner
    try:
        items = ((exercise or {}).get("payload", {}) or {}).get("checklist", [])
        if not items:
            return _fail("No checklist to grade.")
        expected = {_norm_name(it.get("name", "")) for it in items}
        expected.discard("")
        if not expected:
            return _fail("No checklist to grade.")
        given = _parse_names(submission)
        if not given:
            return _fail("List the unvalidated input names, one per line.")
        gset = set(given)
        if gset == expected:
            return {"pass": True, "score": 1.0,
                    "feedback": f"Full audit ({len(expected)}/{len(expected)} "
                                f"unvalidated inputs found)."}
        hits = len(gset & expected)
        missing = sorted(expected - gset)
        extra = sorted(gset - expected)
        score = hits / max(len(expected), len(gset))
        detail = (f"{hits}/{max(len(expected), len(gset))} inputs right. ")
        if missing:
            detail += f"Missed: {', '.join(missing)}. "
        if extra:
            detail += f"Not unvalidated: {', '.join(extra)}."
        return {"pass": False, "score": score, "feedback": detail.strip()}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — list input names.")


def render(exercise: dict) -> str:
    """Article HTML: numbered function, name textarea, hints, file footer."""
    payload = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Exact unvalidated-input set required to pass; partial "
        f"credit per correct name (case-insensitive). No sandbox.</small></p>"
        f"</details>"
        f"<form method='post'><textarea name='answer' rows='6' cols='40' "
        f"placeholder='one input name per line'></textarea><br>"
        f"<button>Submit audit</button></form>{hints}"
        f"<p><small>{html.escape(str(exercise.get('file', '')))}:"
        f"{exercise.get('line', 0)}</small></p></article>")


def section_html(db_path: str = "") -> str:
    """Status-page home for this area (never in web.py)."""
    _ = db_path  # pure section: no DB read needed
    return ("<h3 id='status-b9-inputaudit'>Input-validation audit "
            "<small>(feature)</small></h3>"
            "<p>Type-51 exercises show one function; list the inputs that "
            "reach eval/exec/open/subprocess/SQL sinks without validation. "
            "AST-graded checklist with per-item partial credit, no sandbox. "
            "<code>groundwork/inputaudit.py</code>.</p>")


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "input-validation-audit", "kind": "feature",
            "title": "Input-validation audit",
            "blurb": "Spot the inputs that reach dangerous sinks without validation.",
            "path": "/status", "anchor": "status-b9-inputaudit"}
