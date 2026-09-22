"""Transfer test exercise (type 74, F-70, bloom: apply).

The learner meets a known concept in UNFAMILIAR code: the front shows a
novel snippet (identifiers systematically renamed, structure kept) with
NO lesson links — no file:line, no lesson title, no "see lesson" pointer.
The task is predict-output on the novel snippet, graded by sandbox vectors
(reference behavior, not text match), so lesson-text recall cannot pass.

``generate`` never returns None and never raises: thin input (no runnable
code) yields an ungrounded card the pipeline skips via the generic
``grounded is False`` filter. ``gen_transfer`` is the card-type generator
``gen_<name>(ex_id, concept, snippet, ctx) -> dict`` carrying
front/back/check; ``generate`` aliases it for the GENERATORS registry.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches),
``groundwork/grading.py`` (disclosure 74),
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES) and ``groundwork/__main__``
(cmd_e2e fixture answer); status section and tour entry below join the
``groundwork/batch18.py`` home module (anchor ``status-b18-transfer``).
"""

from __future__ import annotations

import ast
import hashlib
import html

TYPE_NUM = 74
TYPE_NAME = "transfer-test"
BLOOM = "apply"
STATUS_ANCHOR = "status-b18-transfer"

# Novel-identifier pool: ordinary names, nothing lesson-flavoured.
_WORDS = ("bex", "koda", "miri", "tavo", "zuna", "plin", "sora", "wex",
          "juno", "krel", "dax", "pim", "rova", "tink", "zel", "quim")

# Names never renamed: builtins, keywords-by-construction, dunders.
_KEEP = {"self", "cls", "True", "False", "None", "__name__",
         "print", "len", "range", "str", "int", "bool", "list", "dict",
         "set", "tuple", "sum", "min", "max", "abs", "repr", "enumerate"}


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _seed(ex_id) -> int:
    try:
        return int(hashlib.sha256(str(ex_id).encode()).hexdigest()[:8], 16)
    except Exception:  # noqa: BLE001 — seeding must never raise
        return 0


def _novel_variant(code: str, ex_id) -> str:
    """Rename user identifiers deterministically; structure untouched.

    Returns "" when the code does not parse (caller marks ungrounded).
    """
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return ""
    names = sorted({n.id for n in ast.walk(tree)
                    if isinstance(n, ast.Name) and n.id not in _KEEP
                    and not n.id.startswith("__")}
                   | {n.name for n in ast.walk(tree)
                      if isinstance(n, ast.FunctionDef)
                      and n.name not in _KEEP
                      and not n.name.startswith("__")})
    if not names:
        return ""
    seed = _seed(ex_id)
    pool = list(_WORDS)
    mapping = {n: pool[(seed + i) % len(pool)] + f"_{i}"
               for i, n in enumerate(names)}
    # Avoid collisions with names already in the code.
    taken = set(names) | set(pool)
    for n, new in list(mapping.items()):
        if new in taken:
            mapping[n] = f"{new}x"

    class _Renamer(ast.NodeTransformer):
        def visit_Name(self, node):  # noqa: N802
            if node.id in mapping:
                node.id = mapping[node.id]
            return node

        def visit_FunctionDef(self, node):  # noqa: N802
            if node.name not in _KEEP:
                node.name = mapping.get(node.name, node.name)
            self.generic_visit(node)
            return node

        def visit_arg(self, node):  # noqa: N802
            if node.arg in mapping:
                node.arg = mapping[node.arg]
            return node

    try:
        return ast.unparse(_Renamer().visit(tree))
    except Exception:  # noqa: BLE001 — unparse must never raise
        return ""


def _front_text(concept_name: str, novel: str) -> str:
    # No anchor: no file, no line, no lesson link anywhere on the front.
    return (
        f"You know `{concept_name}` — now prove it somewhere new. "
        "This snippet restates the same idea in code you have not seen "
        "(names changed, idea kept). There are no links back to the lesson.\n"
        f"What does it print/return?\n```python\n{novel[:600]}\n```"
    )


def _hints() -> list[str]:
    # Generic scaffolding only — never a pointer into lesson text.
    return [
        "Ignore the unfamiliar names; track what each value becomes.",
        "Run it in your head line by line, then answer the output.",
        "Worked step: rename one name back to the one you know, re-check.",
    ]


def gen_transfer(ex_id, concept, snippet, ctx) -> dict:
    """Build a transfer card with front/back/check; never None, never raises."""
    try:
        return _gen(ex_id, concept, snippet, ctx)
    except Exception:  # noqa: BLE001 — generate never raises
        return _gen(None, None, None, None)


def _gen(ex_id, concept, snippet, ctx) -> dict:
    ctx = ctx if isinstance(ctx, dict) else {}
    name = _concept_field(concept, "name", "") or "concept"
    node_id = _concept_field(concept, "node_id", "transfer")
    try:
        line = int(getattr(concept, "line", 0) or 0)
    except (TypeError, ValueError):
        line = 0
    commit = str(ctx.get("commit", "") or "")
    code = str(ctx.get("runnable", "") or "")
    expected = str(ctx.get("expected_output", ""))
    novel = _novel_variant(code, ex_id) if code else ""
    grounded = bool(novel and expected)
    front = _front_text(name, novel) if grounded else (
        f"Apply `{name}` in unfamiliar code (no runnable reference "
        "recorded for this card).")
    back = expected if grounded else code.strip() or name
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
        "bloom": BLOOM, "concept_id": node_id, "concept": name,
        "file": _concept_field(concept, "file", "") or "",
        "line": line,
        "commit": commit, "hints": _hints(),
        "front": front, "back": back,
        "payload": {"novel": novel, "expected": expected,
                    "reference": code,
                    "check": {"expected": expected},
                    "grounded": grounded},
    }


generate = gen_transfer


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Sandbox-measured output match on the novel snippet (type-8 bar)."""
    try:
        return _grade(exercise, submission, runner)
    except Exception as exc:  # noqa: BLE001 — grading never raises
        return _fail(f"Grader hiccup ({exc}) — resubmit.")


def _grade(exercise: dict, submission: str, runner) -> dict:
    p = (exercise or {}).get("payload", {}) or {}
    check = p.get("check", {}) or {}
    expected = str(check.get("expected", p.get("expected", ""))).strip()
    novel = p.get("novel", "")
    text = str(submission if submission is not None else "").strip()
    if not text:
        return _fail("Answer the output of the unfamiliar snippet.")
    if not novel or not expected:
        return _fail("No reference output recorded on this card.")
    if runner is None:
        return {"pass": False, "score": 0.0,
                "feedback": "No sandbox available for grading."}
    try:
        res = runner.run(novel)
    except Exception:  # noqa: BLE001 — runner faults fail closed
        return _fail("Sandbox unavailable — resubmit.")
    ref_ok = res.ok and res.stdout.strip() == expected
    if not ref_ok:
        return _fail("Reference no longer reproduces; flagged stale.")
    ok = text == expected
    return {"pass": ok, "score": 1.0 if ok else 0.0,
            "feedback": "Transfer holds — same idea, new code." if ok else
            f"Actual output: {res.stdout.strip()[:200]!r}."}


def render(exercise: dict) -> str:
    """Widget: novel snippet prompt plus answer box (generic shape)."""
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
        f"<p><small>Your answer on the unfamiliar snippet must equal "
        f"the sandbox-measured output, run live — no lesson text "
        f"to lean on.</small></p></details>"
        f"<form method='post'><label>It prints/returns: "
        f"<input name='answer' size='30'></label> "
        f"<button>Check transfer</button></form>{hints}</article>")


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch18.py."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Transfer test <small>(feature)</small></h3>"
        "<p>Same concept in a novel snippet with no lesson links on the "
        "front — predict the output of renamed code; the sandbox grades "
        "behavior, not recall. "
        "<code>groundwork/transfer.py</code> (type 74).</p>"
    )


def tour_entry() -> dict:
    """Tour registry entry; the parent copies it into tour.ENTRIES."""
    return {
        "id": "transfer-test",
        "kind": "feature",
        "title": "Transfer test",
        "blurb": "Same idea in code you have never seen — no lesson links on the front; the sandbox checks the behavior.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
