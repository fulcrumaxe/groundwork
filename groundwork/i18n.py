"""i18n-extraction exercise (type 53, F-30, bloom: analyse).

The learner reads a small function and lists the hardcoded user-facing
strings that should be extracted for translation. The reference set is
derived from the AST of the shown code, and grading is an EXACT set
match after whitespace folding (order-insensitive): a missing string
OR one extra string fails, score 0.0 — no partial credit, in the same
spirit as fuzztriage's line-match strictness (a wrong answer that merely
contains a required string as a substring still fails).

Collection rule (deterministic, documented here):
- every ``str`` constant counts EXCEPT: module/function/class docstrings
  (leading ``Expr(Constant str)``), assignments to dunder names
  (``__all__`` etc.), and import statements (module names are not UI
  text). Comments never count (the AST has no comment nodes).
- f-string STATIC parts count as ONE item with each dynamic hole shown
  as ``{...}`` (e.g. ``f"Hello, {name}!"`` -> ``"Hello, {...}!"``);
  dynamic holes contribute nothing. String constants nested inside a
  hole expression are not collected.
- dict keys, format strings and call arguments all count: whatever the
  AST yields IS the reference, so the rule only needs to be exact, and
  empty/whitespace-only literals are dropped.
- grading normalisation: whitespace fold (``" ".join(s.split())``),
  drop empties, dedupe; case- and punctuation-sensitive otherwise.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``,
``collect_strings``/``reference_set`` helpers, ``section_html``,
``tour_entry``. Import-safe standalone: stdlib only (``ast``/``html``),
no groundwork imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); pipeline needs no harness/mutation
guard (pure static analysis — see EMISSION below). ``generate`` returns
``None`` when the code yields zero strings.
"""
from __future__ import annotations

import ast
import html

TYPE_NUM = 53
TYPE_NAME = "i18n-extract"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b9-i18n"

HOLE = "{...}"

FALLBACK_CODE = (
    "def greet(name):\n"
    '    print("Welcome back")\n'
    '    return f"Hello, {name}!"\n'
)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def normalize(text: str) -> str:
    """Whitespace-fold one candidate string (grading normalisation)."""
    return " ".join(str(text or "").split())


def _is_docstring_expr(stmt) -> bool:
    return (isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str))


def _is_dunder_assign(stmt) -> bool:
    names: list[str] = []
    if isinstance(stmt, ast.Assign):
        for t in stmt.targets:
            if isinstance(t, ast.Name):
                names.append(t.id)
            elif isinstance(t, (ast.Tuple, ast.List)):
                names += [e.id for e in t.elts if isinstance(e, ast.Name)]
    elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
        names.append(stmt.target.id)
    return any(n.startswith("__") and n.endswith("__") for n in names)


def _collect(node: ast.AST, out: list[str]) -> None:
    """Append raw string literals under node (JoinedStr -> one template)."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        for d in node.decorator_list:
            _collect(d, out)
        for d in list(getattr(node.args, "defaults", [])) + list(
                getattr(node.args, "kw_defaults", []) or []):
            if d is not None:
                _collect(d, out)
        _body_strings(node.body, out, docstring_ok=True)
        return
    if isinstance(node, ast.JoinedStr):
        parts = [v.value if isinstance(v, ast.Constant)
                 and isinstance(v.value, str) else HOLE
                 for v in node.values]
        text = "".join(parts)
        if text.replace(HOLE, "").strip():
            out.append(text)
        return  # holes contribute nothing; children already handled
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        if node.value.strip():
            out.append(node.value)
        return
    for child in ast.iter_child_nodes(node):
        _collect(child, out)


def _body_strings(stmts: list, out: list[str], docstring_ok: bool) -> None:
    for i, st in enumerate(stmts):
        if i == 0 and docstring_ok and _is_docstring_expr(st):
            continue
        if isinstance(st, (ast.Import, ast.ImportFrom)):
            continue
        if _is_dunder_assign(st):
            continue
        _collect(st, out)


def collect_strings(source: str) -> list[str]:
    """Raw user-facing literals in source order (never raises)."""
    try:
        tree = ast.parse(source or "")
    except (SyntaxError, ValueError, MemoryError):
        return []
    out: list[str] = []
    try:
        _body_strings(tree.body, out, docstring_ok=True)
    except Exception:  # noqa: BLE001 — collection never raises
        return []
    return out


def reference_set(source: str) -> list[str]:
    """Normalised, deduped, sorted reference set for a code sample."""
    return sorted({normalize(s) for s in collect_strings(source)
                   if normalize(s)})


def _code_for(concept, snippet, ctx) -> tuple[str, bool]:
    ctx = ctx or {}
    code = str(ctx.get("runnable") or "\n".join(snippet or []) or "").strip()
    if code:
        return code, True
    return FALLBACK_CODE, False


def generate(ex_id, concept, snippet, ctx):
    """Build an i18n-extract card; an ungrounded card (never None) when the code has zero strings."""
    try:
        code, grounded = _code_for(concept, snippet, ctx or {})
        strings = reference_set(code)
        name = _concept_field(concept, "name", "function") or "function"
        if not strings:
            return {
                "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
                "bloom": BLOOM,
                "concept_id": _concept_field(concept, "node_id", name),
                "concept": name,
                "file": _concept_field(concept, "file"), "line": 0,
                "commit": str((ctx or {}).get("commit", "") or ""),
                "hints": ["No hardcoded strings: nothing to list.",
                          "Compare with a function that prints messages.",
                          "Recognizing i18n-clean code is the skill."],
                "front": (f"Read `{name}` below. List every hardcoded "
                          f"user-facing string that should be extracted "
                          f"for translation — one string per line, exact "
                          f"text.\n```python\n{code}\n```\n"
                          f"Static analysis found no strings here — this "
                          f"card is skipped in lesson modules."),
                "back": "No hardcoded user-facing strings.",
                "payload": {"code": code, "strings": [], "count": 0,
                            "grounded": False},
            }
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str((ctx or {}).get("commit", "") or "")
        front = (f"Read `{name}` below. List every hardcoded user-facing "
                 f"string that should be extracted for translation "
                 f"({len(strings)} in total) — one string per line, exact "
                 f"text. F-string static text uses `{HOLE}` for each "
                 f"dynamic hole; skip docstrings.\n\n```python\n{code}\n```")
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": [
                "Every literal the user can see on screen counts — labels, "
                "messages, prompts — even inside f-strings.",
                "Docstrings, comments, dunder assignments and import names "
                "are not user-facing: leave them out.",
                f"Static f-string text keeps its shape with `{HOLE}` where "
                "the variable goes, e.g. `Hello, {...}!`.",
            ],
            "front": front, "back": "\n".join(strings),
            "payload": {"code": code, "strings": strings,
                        "count": len(strings), "grounded": grounded},
        }
    except Exception:  # never raise, never None, on the suite ctx
        strings = reference_set(FALLBACK_CODE)
        if not strings:
            return {"id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
                    "bloom": BLOOM, "concept_id": "function",
                    "concept": "function", "file": "", "line": 0,
                    "commit": "",
                    "hints": ["No hardcoded strings: nothing to list."],
                    "front": "List the user-facing strings below.",
                    "back": "No hardcoded user-facing strings.",
                    "payload": {"code": FALLBACK_CODE, "strings": [],
                                "count": 0, "grounded": False}}
        return {"id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
                "bloom": BLOOM, "concept_id": "function",
                "concept": "function", "file": "", "line": 0, "commit": "",
                "hints": ["List each user-facing string, one per line."],
                "front": "List the user-facing strings below, one per line.",
                "back": "\n".join(strings),
                "payload": {"code": FALLBACK_CODE, "strings": strings,
                            "count": len(strings), "grounded": False}}


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact normalised set match. Missing OR extra items fail. Never raises."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        want = [normalize(s) for s in (payload.get("strings") or [])]
        want = sorted({w for w in want if w})
        if not want:
            return _fail("Exercise payload is missing the string set.")
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail(f"List the {len(want)} user-facing strings, one per line.")
        got = sorted({normalize(l) for l in text.splitlines()
                      if normalize(l)})
        if not got:
            return _fail(f"List the {len(want)} user-facing strings, one per line.")
        if got == want:
            return {"pass": True, "score": 1.0,
                    "feedback": f"Complete extraction ({len(want)}/{len(want)} strings)."}
        missing = [s for s in want if s not in got]
        extra = [s for s in got if s not in want]
        bits = []
        if missing:
            bits.append(f"missing {len(missing)}: "
                        + ", ".join(f"`{m[:60]}`" for m in missing[:3]))
        if extra:
            bits.append(f"extra {len(extra)}: "
                        + ", ".join(f"`{e[:60]}`" for e in extra[:3]))
        return _fail("Not the exact set (" + "; ".join(bits)
                     + f"). Every required string, nothing else.")
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — one string per line.")


def render(exercise: dict) -> str:
    """Shown function plus a one-string-per-line answer box."""
    payload = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    from . import codelines as codelinesmod
    code = codelinesmod.numbered_html(str(payload.get("code", "")))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p><pre>{code}</pre>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Exact set match after whitespace folding "
        f"(order-insensitive): every required string present and nothing "
        f"extra. No sandbox.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='8' cols='70' "
        f"placeholder='One string per line…'></textarea><br>"
        f"<button>Check extraction</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>i18n extraction <small>(feature)</small></h3>"
        "<p>List the hardcoded user-facing strings in a function for "
        "translation — graded by exact set match against the AST-derived "
        "string set, no sandbox. "
        "<code>groundwork/i18n.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "i18n-extraction", "kind": "feature",
            "title": "i18n extraction",
            "blurb": "List the hardcoded UI strings to extract for translation — exact set match.",
            "path": "/status", "anchor": "status-b9-i18n"}
