"""Module pipeline: ingest -> select -> author -> verify -> schedule.

The caller (the agent that made the change) authors every lesson and
exercise in its own words. Expected outputs for execution exercises are
*measured* by running reference code in the sandbox, never invented.
Anything that doesn't reproduce is discarded by the verification gate.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from . import diff as diffmod
from . import exercises as ex
from . import graph as graphmod
from . import modules as modmod
from . import sandbox as sbmod
from . import select as selectmod
from . import whyit as whyitmod

MUTATIONS = [("+", "-"), ("-", "+"), ("*", "+"), ("==", "!="),
             ("!=", "=="), ("True", "False"), ("<", "<="), (">", ">=")]


def func_source(repo: str, file: str, line: int) -> str:
    """Full source of the def enclosing `line` (Python), else line block."""
    p = Path(repo) / file
    if not p.is_file() and Path(file).is_file():
        p = Path(file)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return ""
    if p.suffix == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return ""
        best = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.lineno <= line and (best is None or node.lineno > best.lineno):
                    best = node
        if best is not None:
            seg = ast.get_source_segment(text, best)
            if seg:
                return seg
    lines = text.splitlines()
    start = max(0, line - 6)
    return "\n".join(lines[start:line + 10])


def _call_harness(src: str) -> tuple[str, str] | None:
    """Return (runnable_src, call_expr) for no-arg/all-default functions."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None
    fn = next((n for n in tree.body
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))), None)
    if fn is None or fn.args.kwonlyargs or fn.args.vararg or fn.args.kwarg:
        return None
    args = []
    defaults = [None] * (len(fn.args.args) - len(fn.args.defaults)) + list(fn.args.defaults)
    for a, d in zip(fn.args.args, defaults):
        if d is None:
            return None  # required arg we cannot invent
        try:
            v = ast.literal_eval(d)
            args.append(repr(v))
        except (ValueError, SyntaxError):
            return None
    call = f"{fn.name}({', '.join(args)})"
    return src, call


def _mutate(src: str) -> tuple[str, int] | None:
    lines = src.splitlines()
    for i, l in enumerate(lines):
        if i == 0 or l.strip().startswith(("#", '"', "'")):
            continue
        for old, new in MUTATIONS:
            if old in l:
                lines[i] = l.replace(old, new, 1)
                return "\n".join(lines), i + 1
    return None


def build_ctx(repo: str, concept, snippet: list[str], hunks,
              decisions: list[dict], graph) -> dict:
    src = func_source(repo, concept.file, concept.line)
    ctx: dict = {
        "commit": "", "graph": graph, "decisions": decisions,
        "diff_lines": [l for h in hunks if h.file == concept.file for l in h.lines][:30],
    }
    if src:
        ctx["code_block"] = src  # full def: parses, orders well as Parsons
    harness = _call_harness(src) if src else None
    runner = sbmod.SandboxRunner()
    if harness:
        runnable, call = harness
        res = runner.run(f"{runnable}\nprint(repr({call}))")
        if res.ok and res.stdout.strip():
            ctx["runnable"] = runnable
            ctx["call"] = call
            ctx["expected_output"] = res.stdout.strip()
            # Assert-only harness: no defs, so it cannot override submissions.
            ctx["tests"] = (
                f"_out = repr({call})\n"
                f"assert _out == {res.stdout.strip()!r}, f'FAIL: {{_out}}'\nprint('OK')")
            var = _first_var(src)
            tr = runner.trace(f"{runnable}\nprint(repr({call}))", var)
            if tr.ok and tr.data:
                ctx["trace_var"] = var
                ctx["trace_expected"] = tr.data
    mut = _mutate(src) if src else None
    if mut and ctx.get("tests"):
        buggy, bug_line = mut
        # The injected bug must actually break the measured tests.
        bad = runner.run(buggy + "\n" + ctx["tests"])
        good = runner.run(runnable + "\n" + ctx["tests"])
        if (not bad.ok or "FAIL" in bad.stdout) and good.ok:
            ctx["buggy"] = buggy
            ctx["bug_line"] = bug_line
            ctx["fixed"] = runnable
    return ctx


def docstring_for(repo: str, file: str, line: int) -> str:
    """Extract docstring (Python) or leading comment (TS/JS) for the def at line."""
    p = Path(repo) / file
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return ""
    if p.suffix == ".py":
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return ""
        best = None
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.lineno <= line and (best is None or node.lineno > best.lineno):
                    best = node
        if best is not None:
            return ast.get_docstring(best) or ""
        return ""
    lines = text.splitlines()
    doc: list[str] = []
    for l in lines[max(0, line - 8):line - 1][::-1]:
        s = l.strip()
        if s.startswith(("//", "*", "/*", "*/")):
            doc.append(s.strip("/ *"))
        elif not s:
            continue
        else:
            break
    return " ".join(reversed([d for d in doc if d]))


def lesson_for(repo: str, concept, graph) -> dict:
    """Teaching content for a concept: summary, docs, relations, key lines.

    This is the 'study' half of the loop — everything the old MVP only
    asked about, the lesson now also explains.
    """
    doc = docstring_for(repo, concept.file, concept.line)
    callers = sorted({s for s, d, k in graph.edges
                      if d in (concept.node_id, concept.name) and s != concept.node_id})
    callees = sorted({d for s, d, k in graph.edges
                      if s == concept.node_id and d != concept.node_id})
    node = graph.nodes.get(concept.node_id)
    calls = list(getattr(node, "calls", []) or [])[:8]
    snippet = "\n".join(
        _snippet_lines(repo, concept.file, concept.line, before=2, after=8))
    first_line = doc.splitlines()[0] if doc else ""
    summary = first_line or (
        f"`{concept.name}` is a {concept.kind} defined in "
        f"{concept.file}:{concept.line or '?ague'}."
        .replace(":?ague", ""))
    if not first_line:
        if callees or calls:
            uses = ", ".join(f"`{c}`" for c in (callees or calls)[:4])
            summary += f" It works with {uses}."
        if callers:
            used_by = ", ".join(f"`{c}`" for c in callers[:4])
            summary += f" It is used by {used_by}."
    source = func_source(repo, concept.file, concept.line)
    node = graph.nodes.get(concept.node_id)
    how = walkthrough(source)
    return {"concept_id": concept.node_id, "name": concept.name,
            "kind": concept.kind, "file": concept.file, "line": concept.line,
            "summary": summary, "docstring": doc,
            "callers": callers[:8], "callees": (callees or calls)[:8],
            "key_lines": snippet, "source": source,
            "complexity": getattr(node, "complexity", 0) or 0,
            "how": how, "worked": None,
            "dualcode": {"steps": list(how), "states": []}}


def _snippet_lines(repo: str, file: str, line: int, before: int = 2,
                   after: int = 8) -> list[str]:
    try:
        lines = (Path(repo) / file).read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    return lines[max(0, line - 1 - before):line - 1 + after]


def _expr_summary(node: ast.AST) -> str:
    try:
        return ast.unparse(node).strip()[:60]
    except (ValueError, SyntaxError):
        return "..."


def walkthrough(src: str, limit: int = 8) -> list[str]:
    """Plain-words step-by-step of a function's body (AST-based).

    The 'very good basic explanation': what each step does, in order.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    fn = next((n for n in tree.body
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))), None)
    if fn is None:
        return []
    steps: list[str] = []
    body = [s for s in fn.body
            if not (isinstance(s, ast.Expr)
                    and isinstance(s.value, ast.Constant)
                    and isinstance(s.value.value, str))]
    for stmt in body[:limit]:
        if isinstance(stmt, ast.Assign):
            targets = ", ".join(f"`{t.id}`" for t in stmt.targets
                                if isinstance(t, ast.Name)) or "a value"
            steps.append(f"Sets {targets} to `{_expr_summary(stmt.value)}`.")
        elif isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            steps.append(f"Sets `{stmt.target.id}` to "
                         f"`{_expr_summary(stmt.value) if stmt.value else '…'}`.")
        elif isinstance(stmt, ast.Return):
            steps.append(f"Hands back `{_expr_summary(stmt.value) if stmt.value else 'nothing'}`.")
        elif isinstance(stmt, ast.If):
            steps.append(f"If `{_expr_summary(stmt.test)}`, runs the next "
                         f"{len(stmt.body)} step(s)"
                         + ("; otherwise the other branch." if stmt.orelse else "."))
        elif isinstance(stmt, (ast.For, ast.AsyncFor)):
            steps.append(f"Repeats for each `{_expr_summary(stmt.target)}` in "
                         f"`{_expr_summary(stmt.iter)}`.")
        elif isinstance(stmt, ast.While):
            steps.append(f"Keeps going while `{_expr_summary(stmt.test)}`.")
        elif isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            f = stmt.value.func
            name = f.id if isinstance(f, ast.Name) else getattr(f, "attr", "…")
            steps.append(f"Calls `{name}(…)` and ignores the result.")
        elif isinstance(stmt, ast.Expr):
            steps.append(f"Evaluates `{_expr_summary(stmt.value)}`.")
        elif isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            steps.append(f"Defines a helper, `{stmt.name}(…)`.")
        else:
            steps.append(f"`{type(stmt).__name__}` step.")
    return steps


def _first_var(src: str) -> str:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return "x"
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and node.targets:
            t = node.targets[0]
            if isinstance(t, ast.Name):
                return t.id
    return "x"


# Exercise-type registry by Bloom tier (grading/chips map through it).
# It is NOT an emission list: the pipeline deals no types on its own;
# every card below is caller-authored.
BLOOM_DEFAULT_TYPES = {
    "recall": [1, 2, 4, 3],
    "explain": [5, 6, 7, 25, 1],
    "apply": [8, 10, 11, 12, 9, 31, 32, 33, 44, 54, 55, 68, 72, 74, 81],
    "analyse": [13, 14, 16, 18, 9, 15, 17, 26, 28, 29, 34, 36, 37, 45,
                49, 50, 51, 52, 53, 58, 59, 60, 61, 69, 76, 82],
    "modify": [12, 14, 19, 20, 27, 35, 38, 39, 46, 47, 56, 62, 66, 67, 70],
    "evaluate": [21, 22, 48, 57, 63, 71, 73, 77, 78],
    "create": [24, 23, 40, 41, 42, 43, 64, 65, 75],
    "understand": [79, 1, 80],
}


def _concept_index(concepts) -> dict:
    by_key = {}
    for c in concepts:
        by_key[c.node_id] = c
        by_key.setdefault(c.name, c)
    return by_key


def apply_agent_lessons(lessons: list, concepts, agent_lessons: list) -> list:
    """Override templated lesson fields with the caller's own words.

    Each item needs `concept` (selected node id or name) and a non-empty
    `summary`; optional `how`, `key_lines`, `docstring`, `source`,
    `callers`, `callees` replace the generated values. Measured fields
    (`worked`) always stay. Returns per-item error strings.
    """
    errors = []
    by_concept = {L["concept_id"]: L for L in lessons}
    idx = _concept_index(concepts)
    for i, item in enumerate(agent_lessons):
        tag = f"lessons[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{tag}: must be an object")
            continue
        key = item.get("concept") or item.get("name")
        c = idx.get(str(key)) if key else None
        if c is None or c.node_id not in by_concept:
            errors.append(f"{tag}: unknown concept {key!r}")
            continue
        summary = str(item.get("summary") or "").strip()
        if not summary:
            errors.append(f"{tag}: missing summary")
            continue
        L = by_concept[c.node_id]
        L["summary"] = summary[:2000]
        for f in ("how", "key_lines", "docstring", "source",
                  "callers", "callees", "before", "after"):
            if item.get(f) is not None:
                L[f] = item[f]
        L["agent"] = True
    return errors


def build_agent_exercises(agent_exercises: list, concepts, start_n: int,
                          commit: str, purpose: str, note_for) -> tuple:
    """Caller-authored cards in generated-exercise shape.

    Each item needs `concept` (selected node id or name) plus non-empty
    `front`/`back`; `type` must be a known exercise id (default 1).
    Returns (items, errors, next_n).
    """
    items, errors = [], []
    idx = _concept_index(concepts)
    n = start_n
    for i, item in enumerate(agent_exercises):
        tag = f"exercises[{i}]"
        if not isinstance(item, dict):
            errors.append(f"{tag}: must be an object")
            continue
        key = item.get("concept")
        c = idx.get(str(key)) if key else None
        if c is None:
            errors.append(f"{tag}: unknown concept {key!r}")
            continue
        front = str(item.get("front") or "").strip()
        back = str(item.get("back") or "").strip()
        if not front or not back:
            errors.append(f"{tag}: front and back are both required")
            continue
        t = item.get("type", 1)
        if t not in ex.TYPES:
            errors.append(f"{tag}: unknown type {t!r}")
            continue
        n += 1
        payload = item.get("payload") or {}
        if not isinstance(payload, dict):
            errors.append(f"{tag}: payload must be an object")
            continue
        hints = item.get("hints") or []
        items.append({
            "id": f"ex{n:03d}", "type": t,
            "type_name": ex.TYPES[t][0], "bloom": ex.TYPES[t][1],
            "concept_id": c.node_id, "concept": c.name,
            "file": c.file, "line": c.line, "commit": commit,
            "front": front[:2000], "back": back[:2000],
            "payload": payload, "hints": list(hints)[:8],
            "why": why_for(note_for(c), purpose)})
    return items, errors, n


def create_module(con, repo: str, commit_range: str = "", task_summary: str = "",
                  touched_symbols: list[str] | None = None,
                  learner_level: str = "intermediate",
                  provider=None, runner=None, purpose: str = "",
                  concept_notes: dict | None = None,
                  agent_lessons: list | None = None,
                  agent_exercises: list | None = None,
                  agent_exercises_only: bool = False) -> dict:
    # The agent that made the change writes every lesson and exercise in
    # its own words. The pipeline never invents teaching content: no
    # generated lessons, no generated cards, no LLM drafts, no template
    # fallback. Only measurement may add to what the caller wrote
    # (sandbox-measured worked examples, card verification). A module
    # lands if and only if every selected concept carries an
    # agent-authored lesson and at least one agent-authored exercise;
    # otherwise the call fails with the coverage gap named and nothing
    # is stored. `provider` is accepted for compatibility and ignored:
    # no outside model is consulted. `agent_exercises_only` is likewise
    # legacy: every card is caller-authored, so there is nothing to
    # replace.
    if agent_lessons is not None and not isinstance(agent_lessons, list):
        return {"error": "lessons must be a list"}
    if agent_exercises is not None and not isinstance(agent_exercises, list):
        return {"error": "exercises must be a list"}
    # Absolute repo: concept file anchors must resolve regardless of cwd.
    repo = str(Path(repo).resolve())
    repo_p = Path(repo)
    graph = graphmod.build_repo_graph(repo_p)
    d = diffmod.read_diff(repo_p, commit_range)
    touched = list(touched_symbols or []) or diffmod.touched_symbols(d, graph)
    # Mastery per node from past reviews (pass rate of its cards).
    mastery: dict[str, float] = {}
    for row in con.execute(
            "SELECT concepts.id AS cid, concepts.name, AVG(reviews.grade) AS g,"
            " COUNT(reviews.id) AS n FROM concepts"
            " LEFT JOIN cards ON cards.concept_id = concepts.id"
            " LEFT JOIN reviews ON reviews.card_id = cards.id"
            " GROUP BY concepts.id"):
        if row["n"]:
            mastery[row["cid"]] = (row["g"] or 0) / 5.0
            mastery[row["name"]] = (row["g"] or 0) / 5.0
    concepts = selectmod.select_concepts(graph, touched, mastery)
    if not concepts:
        return {"error": "no concepts selected; nothing to teach"}
    decisions = [dict(r) for r in con.execute(
        "SELECT * FROM decisions WHERE repo=? ORDER BY id DESC LIMIT 20", (repo,))]
    runner = runner or sbmod.SandboxRunner()
    notes = concept_notes or {}

    def _note_for(c) -> str:
        for key in (c.node_id, c.name):
            if key in notes:
                return str(notes[key])
        return ""

    lessons = [lesson_for(repo, c, graph) for c in concepts]
    lesson_by_concept = {L["concept_id"]: L for L in lessons}
    # The caller's own words land on the extracted lesson frames. Frames
    # without an agent summary are not lessons yet — they are the gap.
    agent_errors = apply_agent_lessons(lessons, concepts, agent_lessons or [])
    # I-109: stamp each lesson with the agent's concept note so the
    # lesson path can say why it matters. Absent note = absent key.
    for c in concepts:
        note = whyitmod.clean_note(_note_for(c))
        if note:
            lesson_by_concept[c.node_id]["why_note"] = note
    missing_lessons = sorted(
        {L["concept_id"] for L in lessons if not L.get("agent")})
    for c in concepts:
        snippet = ex.get_snippet(repo, c.file, c.line)
        hunks = [h for h in d.hunks if h.file == c.file]
        ctx = build_ctx(repo, c, snippet, hunks, decisions, graph)
        lesson = lesson_by_concept[c.node_id]
        # Measured worked example: the exact call and output the study
        # shows. Measurement, not authorship: the caller cannot invent
        # outputs, so the sandbox supplies them.
        if "runnable" in ctx:
            worked = {"call": ctx.get("call", ""), "output": ctx["expected_output"]}
            if "trace_expected" in ctx:
                worked["trace"] = {"var": ctx["trace_var"],
                                   "steps": ctx["trace_expected"]}
                # Dual-code states: measured values behind the diagram steps.
                dc = lesson.get("dualcode")
                if isinstance(dc, dict):
                    dc["states"] = [str(v) for v in ctx["trace_expected"]][:8]
            lesson["worked"] = worked
    # The caller's cards are the ONLY cards. They face the same sandbox
    # verifier as before — equal treatment, no free pass — but nothing
    # generated joins them.
    n = 0
    ax, ax_errors, n = build_agent_exercises(
        agent_exercises or [], concepts, n, ",".join(d.commits[:2]),
        purpose, _note_for)
    agent_errors += ax_errors
    covered = {e["concept_id"] for e in ax}
    missing_exercises = [c.node_id for c in concepts if c.node_id not in covered]
    if missing_lessons or missing_exercises:
        return {
            "error": ("every selected concept needs an agent-authored "
                      "lesson and at least one agent-authored exercise; "
                      f"missing lessons: {missing_lessons or 'none'}; "
                      f"missing exercises: {missing_exercises or 'none'}"),
            "agent_errors": agent_errors}
    exercises = ax
    for e in exercises:
        if e["type"] in (1, 5, 6, 24):
            # Teaching backs: the caller's explanation, not rubric keywords.
            e["back"] = _teaching_back(
                lesson_by_concept[e["concept_id"]], e["back"])
    # Open learning holes become complete-the-function exercises (PRD
    # "learning mode"): the agent left a TODO, the learner writes it.
    holes = [dict(r) for r in con.execute(
        "SELECT * FROM holes WHERE repo=? AND status='open'", (repo,))]
    for h in holes:
        src = func_source(repo, h["file"], h["line"] or 1)
        if not src.strip():
            continue
        n += 1
        eid = f"ex{n:03d}"
        hc = selectmod.ScoredConcept(f"hole:{h['id']}",
                                     h["file"].split("/")[-1].rsplit(".", 1)[0],
                                     "function", h["file"], h["line"] or 1,
                                     1.0, 1.0, 1.0, 1.0)
        concepts.append(hc)
        hole_lesson = lesson_for(repo, hc, graph)
        lessons.append(hole_lesson)
        stub = (src.splitlines()[0]
                + f"\n    # TODO (you): {h['spec']}\n    pass")
        exercises.append({
            "id": eid, "type": 12, "type_name": "complete-function",
            "bloom": "apply", "concept_id": hc.node_id, "concept": hc.name,
            "file": hc.file, "line": hc.line, "commit": "",
            "front": (f"Fill the learning hole: {h['spec']}\n"
                      f"```python\n{stub}\n```"),
            "back": src,
            "why": why_for(h["spec"], purpose),
            "payload": {"stub": stub, "tests": "", "reference": src},
            "hints": [f"Re-read {hc.file} around line {hc.line}.",
                      "Write the smallest code that satisfies the spec.",
                      f"Worked step: the current code is ```\n{src[:400]}\n```"],
        })
        con.execute("UPDATE holes SET status='used' WHERE id=?", (h["id"],))
    report = sbmod.verify_module(exercises, runner)
    kept = report["kept"]
    if not kept:
        return {"error": ("no exercises survived sandbox verification; "
                          "fix the card payloads and resubmit"),
                "agent_errors": agent_errors,
                "dropped": len(report["dropped"]),
                "pass_rate": report["pass_rate"]}
    mid = modmod.new_id()
    modmod.save_module(con, mid, repo, commit_range, task_summary,
                       learner_level, kept, concepts, lessons, purpose)
    return {"module_id": mid, "concepts": [c.node_id for c in concepts],
            "lessons": lessons, "exercises": kept,
            "purpose": purpose,
            "dropped": len(report["dropped"]),
            "pass_rate": report["pass_rate"],
            "agent_errors": agent_errors}


UNSTATED_WHY = ("No reason given — the agent didn't say why this matters. "
                "Ask it to pass a purpose next time.")


def why_for(agent_note: str = "", purpose: str = "") -> str:
    """Per-card reason, from MCP entry time — never templated, never repeated.

    The module purpose is shown once as the Mission header, so repeating it
    on every card just recreates the same-text problem. A card shows its
    concept's own note; with no note and no purpose it says so honestly.
    """
    if agent_note:
        return agent_note
    if purpose:
        return ""
    return UNSTATED_WHY


def _teaching_back(lesson: dict, fallback: str) -> str:
    parts = [lesson["summary"]]
    if lesson.get("docstring") and lesson["docstring"] not in lesson["summary"]:
        parts.append(lesson["docstring"])
    if lesson.get("key_lines"):
        parts.append("Key code:\n" + lesson["key_lines"][:600])
    if lesson.get("callers"):
        parts.append("Used by: " + ", ".join(f"`{c}`" for c in lesson["callers"][:4]))
    text = "\n\n".join(parts).strip()
    return text or fallback

