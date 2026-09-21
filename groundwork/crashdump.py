"""Core-dump-lite triage: read a traceback, name the frame + the fix.

F-38, type 61, bloom ``analyse`` — the learner dissects a failure into its
crashing frame and fix category, like spot-bug (13) and fuzz-triage (34).

Complements ``groundwork/diagnose.py``: diagnose pastes a REAL traceback and
links every named function to its lesson (where to study); this card shows a
short SYNTHETIC traceback (deterministic from ``ex_id``) and grades
identification (what broke): the crashing frame's function AND the fix
category from a fixed set.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only (``hashlib``/``html``/``re``), no
groundwork imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); pipeline needs no skip guard — the
traceback is always synthesizable, so generate always returns a card.

``generate`` never raises and never returns None: a synthetic traceback is
always plantable, so the pipeline splice never skips this type.

Grading is exact after documented normalization (case-insensitive, stray
quotes/backticks stripped, fix ``_``/space read as ``-``): the crashing
frame must appear as an ISOLATED field (whole line, comma field, or a
``frame=`` value) and the fix category must match. A pasted traceback dump
never passes — the frame name buried in a ``File ... in <frame>`` line is
not isolated (fuzztriage/secretscan isolated-only precedent). Both halves
must match; grading fails closed and never raises. No network, no
subprocess.
"""
from __future__ import annotations

import hashlib
import html
import re

TYPE_NUM = 61
TYPE_NAME = "crash-triage"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b10-crashdump"

FIXES = ("guard-missing-key", "zero-check", "none-check",
         "type-check", "bounds-check")

_SCENARIOS = (
    {"error": "KeyError: 'email'", "fix": "guard-missing-key",
     "frames": (("run_report", "report = aggregate(rows)"),
                ("aggregate", "user = lookup_user(uid)"),
                ("lookup_user", 'email = user["email"]')),
     "why": "the 'email' key is absent — test membership or use .get()."},
    {"error": "ZeroDivisionError: division by zero", "fix": "zero-check",
     "frames": (("handle_request", "summary = summarize(counts)"),
                ("summarize", "rate = ratio(done, total)"),
                ("ratio", "return done / total")),
     "why": "total is 0 — guard before dividing."},
    {"error": "AttributeError: 'NoneType' object has no attribute 'name'",
     "fix": "none-check",
     "frames": (("main", "html = render(session)"),
                ("render", "label = format_name(user)"),
                ("format_name", "return user.name.strip()")),
     "why": "user is None — check for None before touching attributes."},
    {"error": "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
     "fix": "type-check",
     "frames": (("process", "lines = combine(items)"),
                ("combine", "total = subtotal(cart)"),
                ("subtotal", "total = add_tax(amount, label)"),
                ("add_tax", "return amount + label")),
     "why": "a number met a string — coerce or validate types first."},
    {"error": "IndexError: list index out of range", "fix": "bounds-check",
     "frames": (("serve", "page = paginate(items, n)"),
                ("paginate", "chunk = fetch_page(items, n)"),
                ("fetch_page", "entry = get_item(items, n)"),
                ("get_item", "return items[n]")),
     "why": "n runs past the end — check the length first."},
)

_LINE_STEPS = (0, 5, 11, 16, 22)

_FRAME_KEYS = {"frame", "function", "func", "name"}
_FIX_KEYS = {"fix", "category", "fix_category"}


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _pick(ex_id: str) -> tuple[dict, int]:
    digest = hashlib.sha256(str(ex_id).encode()).hexdigest()
    return _SCENARIOS[int(digest[:8], 16) % len(_SCENARIOS)], int(digest[8:16], 16)


def _traceback(fname: str, scenario: dict, salt: int) -> tuple[str, list]:
    base = 10 + (salt % 25)
    lines = ["Traceback (most recent call last):"]
    frames = []
    for i, (func, code) in enumerate(scenario["frames"]):
        lineno = base + _LINE_STEPS[i]
        lines.append(f'  File "{fname}", line {lineno}, in {func}')
        lines.append(f"    {code}")
        frames.append([func, code, lineno])
    lines.append(scenario["error"])
    return "\n".join(lines), frames


def _hints(fname: str, nframes: int) -> list[str]:
    return [
        "Read bottom-up: the last frame before the error line is where it crashed.",
        f"The traceback names {nframes} functions in {fname}, but only the innermost one raised.",
        "Worked step: reply with the crashing function on one line and the fix category on the next.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a crash-triage card; always returns a card, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        name = _concept_field(concept, "name", "") or "service"
        raw_file = _concept_field(concept, "file", "") or "app.py"
        fname = raw_file.split("/")[-1] or "app.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        scenario, salt = _pick(ex_id if ex_id is not None else "ex061")
        tb, frames = _traceback(fname, scenario, salt)
        crash = frames[-1][0]
        front = (
            "Read this traceback. Reply with the CRASHING function "
            "(innermost frame) and the fix category — one per line "
            "(or as `frame=<name>` / `fix=<category>`).\n"
            f"Fix categories: {', '.join(FIXES)}.\n"
            f"```pytb\n{tb}\n```"
        )
        back = (f"Crash in `{crash}` ({scenario['error']}) — "
                f"fix: `{scenario['fix']}` ({scenario['why']})")
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": raw_file, "line": line,
            "commit": commit,
            "hints": _hints(fname, len(frames)),
            "front": front, "back": back,
            "payload": {"traceback": tb, "frames": frames,
                        "crash_frame": crash, "error": scenario["error"],
                        "fix": scenario["fix"], "fixes": list(FIXES),
                        "grounded": True},
        }
    except Exception:
        # Never raise and never None: fall back to scenario 0.
        scenario = _SCENARIOS[0]
        tb, frames = _traceback("app.py", scenario, 0)
        crash = frames[-1][0]
        return {
            "id": str(ex_id), "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "fallback",
            "concept": "service", "file": "app.py", "line": 0,
            "commit": "", "hints": _hints("app.py", len(frames)),
            "front": ("Name the crashing function and the fix category.\n"
                      f"```pytb\n{tb}\n```"),
            "back": f"Crash in `{crash}` — fix: `{scenario['fix']}`.",
            "payload": {"traceback": tb, "frames": frames,
                        "crash_frame": crash, "error": scenario["error"],
                        "fix": scenario["fix"], "fixes": list(FIXES),
                        "grounded": True},
        }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _norm_frame(text: str) -> str:
    t = str(text or "").strip().strip("'\"`").strip()
    return t.lower()


def _norm_fix(text: str) -> str:
    t = str(text or "").strip().strip("'\"`").strip().lower()
    return re.sub(r"[\s_]+", "-", t)


def _fields(text: str) -> list[str]:
    """Isolated answer fields: whole lines, comma fields, key=value values.

    A frame name buried in a pasted ``File ... in <frame>`` line is never
    isolated — only a bare field counts (fuzztriage/secretscan precedent).
    Never raises.
    """
    try:
        out: list[str] = []
        for line in str(text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            if "=" in line:
                key, _, val = line.partition("=")
                if key.strip().lower() in _FRAME_KEYS | _FIX_KEYS:
                    if val.strip():
                        out.append(val.strip())
                    continue
            if ":" in line:
                key, _, val = line.partition(":")
                if key.strip().lower() in _FRAME_KEYS | _FIX_KEYS:
                    if val.strip():
                        out.append(val.strip())
                    continue
            out.extend(re.split(r"[,;]", line))
        return [f.strip() for f in out if f.strip()]
    except Exception:
        return []


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Pass only when the isolated frame AND the fix category both match."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        frame = str(payload.get("crash_frame", "") or "")
        fix = str(payload.get("fix", "") or "")
        if not frame or not fix:
            return _fail("Exercise payload is missing the crash frame.")
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Submit the crashing function and the fix category, "
                         "one per line.")
        fields = _fields(text)
        frame_ok = _norm_frame(frame) in [_norm_frame(f) for f in fields]
        fix_ok = _norm_fix(fix) in [_norm_fix(f) for f in fields]
        if frame_ok and fix_ok:
            return {"pass": True, "score": 1.0,
                    "feedback": f"Crash in `{frame}` — fix: `{fix}`."}
        if not frame_ok and not fix_ok:
            return _fail("Neither matches — read bottom-up: the last frame "
                         "before the error line crashed. Name it plus a fix "
                         f"category from: {', '.join(FIXES)}.")
        if not frame_ok:
            return _fail("Wrong frame — name the innermost (crashing) "
                         "function alone on one line, not its callers.")
        return _fail("Wrong fix category — choose exactly one from: "
                     f"{', '.join(FIXES)}.")
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit the "
                     "crashing function and the fix category.")


def render(exercise: dict) -> str:
    """Exercise widget: traceback plus frame/fix answer box."""
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
        f"<p><small>Both halves must match exactly (case-insensitive): the "
        f"crashing function as an isolated answer plus the fix category. "
        f"Pasting the traceback never counts.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='3' cols='60' "
        f"placeholder='frame: <function>\nfix: <category>'></textarea><br>"
        f"<button>Name frame + fix</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Crash triage <small>(feature)</small></h3>"
        "<p>Read a short synthetic traceback — name the crashing frame's "
        "function and the fix category. Graded by exact isolated match; "
        "pasting the traceback never counts. Complements the diagnose page, "
        "which links real pasted tracebacks to lessons. "
        "<code>groundwork/crashdump.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "crash-triage", "kind": "feature",
            "title": "Crash triage",
            "blurb": "Read a mini traceback — name the crashing function and the fix category.",
            "path": "/status", "anchor": "status-b10-crashdump"}
