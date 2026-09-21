"""CLI UX review exercise (type 57, F-34, bloom: evaluate).

The learner reads a realistic ``--help`` output containing exactly ONE
planted usability flaw (from a fixed 5-category taxonomy) and must name
the flaw category. Grading is exact match after documented
normalization: case, spaces, underscores, hyphens, slashes, colons and
one layer of surrounding quotes are ignored — a wrong category, a
two-category dump, or an empty/garbage answer never passes.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only (``hashlib``/``html``), no
groundwork imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); pipeline needs no skip guard (a card
is always plantable from (ex_id, concept), like secretscan).

``generate`` never raises: when the snippet is empty AND the concept
has no usable name it returns ``None`` instead of a card, and the
parent pipeline splice must skip ``None``.
"""
from __future__ import annotations

import hashlib
import html

TYPE_NUM = 57
TYPE_NAME = "cli-ux-review"
BLOOM = "evaluate"
STATUS_ANCHOR = "status-b10-cliux"

_HELP_INCONSISTENT = """usage: deploy [--dry-run | --dryrun] [--force] [--output DIR]

options:
  --dry-run     preview changes without applying them
  --dryrun      preview changes (legacy spelling)
  --force       apply changes without prompting
  --output DIR  write the report to DIR (default: ./out)

required: none. all options are optional.

examples:
  deploy --dry-run
  deploy --force --output ./reports"""

_HELP_REQUIRED = """usage: deploy --target HOST [--force] [--output DIR]

options:
  --target HOST  which host to deploy to
  --force        apply changes without prompting
  --output DIR   write the report to DIR (default: ./out)

examples:
  deploy --target prod-1"""

_HELP_DESTRUCTIVE = """usage: deploy [--mode MODE] [--confirm] [--output DIR]

options:
  --mode MODE   what to do: deploy or wipe (default: wipe)
  --confirm     ask before applying changes
  --output DIR  write the report to DIR (default: ./out)

required: none. all options are optional.

examples:
  deploy --mode deploy
  deploy --mode wipe --confirm"""

_HELP_CRYPTIC = """usage: deploy --target HOST [--force]

options:
  --target HOST  which host to deploy to (required)
  --force        apply changes without prompting

examples:
  deploy --target prod-1

error:
  $ deploy
  E42"""

_HELP_NOEXAMPLES = """usage: deploy --target HOST [--force] [--output DIR]

options:
  --target HOST  which host to deploy to (required)
  --force        apply changes without prompting
  --output DIR   write the report to DIR (default: ./out)"""

# flaw id -> (label, aliases, why, help text). Every help text but the
# named flaw is clean on the other four dimensions, so exactly ONE
# category fits each card.
FLAWS = (
    ("inconsistent-flag-naming", "Inconsistent flag naming",
     ("inconsistent flags", "flag naming", "mixed flag spelling"),
     "Two spellings of the same flag (--dry-run vs --dryrun) force "
     "users to guess which one works.",
     _HELP_INCONSISTENT),
    ("missing-required-marking", "Missing required-argument marking",
     ("missing required", "required marking", "unmarked required"),
     "--target is required but nothing marks it required, so users "
     "learn that by trial and error.",
     _HELP_REQUIRED),
    ("destructive-default", "Destructive default without confirmation",
     ("dangerous default", "wipe by default"),
     "The default mode wipes and confirmation is opt-in, so a bare "
     "run destroys data.",
     _HELP_DESTRUCTIVE),
    ("cryptic-error", "Cryptic error message",
     ("cryptic error", "bad error message", "error code only"),
     "Running with no arguments prints a bare code (E42) with no hint "
     "about what is missing.",
     _HELP_CRYPTIC),
    ("no-examples", "No examples section",
     ("missing examples", "no examples"),
     "The help lists usage and options but shows zero examples, so "
     "users must guess a working invocation.",
     _HELP_NOEXAMPLES),
)

_FLAW_IDS = [f[0] for f in FLAWS]

# Snippet keyword signals that ground the flaw choice (first hit wins);
# otherwise the flaw is picked deterministically from (ex_id, concept).
_SIGNALS = (
    (("delete", "remove", "destroy", "wipe", "rm ", "drop"),
     "destructive-default"),
    (("required", "add_argument", "missing"), "missing-required-marking"),
    (("raise", "except", "traceback", "error"), "cryptic-error"),
    (("--", "argparse", "click", "optparse", "usage", "flag"),
     "inconsistent-flag-naming"),
)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _pick_flaw(ex_id: str, name: str, snippet_text: str) -> tuple[str, str]:
    low = str(snippet_text or "").lower()
    for keys, fid in _SIGNALS:
        if any(k in low for k in keys):
            return fid, "found"
    i = int(hashlib.sha256(f"{ex_id}:{name}".encode()).hexdigest(), 16)
    return _FLAW_IDS[i % len(_FLAW_IDS)], "planted"


def _by_id(fid: str) -> tuple:
    for f in FLAWS:
        if f[0] == fid:
            return f
    return FLAWS[0]


def _hints(file: str, line: int) -> list[str]:
    where = f"{file}:{line}" if file and line else (file or "the linked file")
    cats = "; ".join(f"{fid} ({label})" for fid, label, _, _, _ in FLAWS)
    return [
        "Check five things: flag spelling, required marking, defaults, "
        "error text, examples — four are clean, one is not.",
        f"Look at {where}: the flaw is one category judgment, not a typo hunt.",
        f"Worked step: the five categories are {cats}. Reply with the ONE that fits.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a CLI-UX-review card, or None when nothing is plantable.

    Found mode: a snippet keyword signal selects the flaw category.
    Planted mode: the flaw is picked deterministically from
    ``(ex_id, concept)``. Returns None only when the snippet is empty
    AND the concept has no usable name.
    """
    try:
        ctx = ctx or {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "") or "service"
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        lines = [str(l) for l in snippet if str(l).strip()]
        if not lines and not _concept_field(concept, "name", ""):
            return None  # no plantable surface: nothing to ground on
        fid, mode = _pick_flaw(str(ex_id), name, "\n".join(lines))
        _, label, _, why, help_text = _by_id(fid)
        cats = "\n".join(f"- {i} ({lab})" for i, lab, _, _, _ in FLAWS)
        front = (
            "Study this --help output. It contains exactly ONE usability "
            "flaw. Reply with the flaw category (id or label).\n"
            f"Categories:\n{cats}\n"
            f"```text\n{help_text[:800]}\n```"
        )
        back = f"Flaw: {label} ({fid}). {why}"
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": _hints(file, line),
            "front": front, "back": back,
            "payload": {"help": help_text[:800], "flaw": fid,
                        "label": label, "mode": mode,
                        "grounded": True},
        }
    except Exception:
        return None  # grading-grade safety: generate never raises


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def normalize_flaw(text: str) -> str:
    """Lowercase; ignore quotes, spacing and separator style."""
    t = str(text if text is not None else "").strip().lower()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in ("'", '"'):
        t = t[1:-1].strip()
    t = "".join("-" if ch in ("_", " ", "/", ":") else ch for ch in t)
    while "--" in t:
        t = t.replace("--", "-")
    return t.strip("-")


def _accepted(fid: str) -> set[str]:
    _, label, aliases, _, _ = _by_id(fid)
    return {normalize_flaw(s) for s in (fid, label, *aliases)}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact flaw-category match after separator/case normalization."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        fid = str(payload.get("flaw", "") or "")
        if fid not in _FLAW_IDS:
            return _fail("Exercise payload is missing the flaw category.")
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Name the ONE flaw category (id or label).")
        if normalize_flaw(text) in _accepted(fid):
            _, label, _, _, _ = _by_id(fid)
            return {"pass": True, "score": 1.0,
                    "feedback": f"Correct: {label}."}
        return _fail("Not the planted flaw — re-check the five categories "
                     "and name exactly one.")
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — name one category.")


def render(exercise: dict) -> str:
    """Exercise widget: --help output plus a flaw-category answer box."""
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
        f"<p><small>Exact flaw category after normalization: case, spaces, "
        f"underscores, hyphens and surrounding quotes are ignored. Accepted "
        f"forms are the flaw id (e.g. inconsistent-flag-naming), its label, "
        f"or a listed alias. A wrong category, two categories, or an empty "
        f"answer fails.</small></p></details>"
        f"<form method='post'><input name='answer' size='50' "
        f"placeholder='name the flaw category'>"
        f"<button>Name the flaw</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>CLI UX review <small>(feature)</small></h3>"
        "<p>Spot the single usability flaw in a --help output — name its "
        "category (flag naming, required marking, destructive default, "
        "cryptic error, no examples). Graded by exact category match after "
        "case/separator normalization. "
        "<code>groundwork/cliux.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "cli-ux-review", "kind": "feature",
            "title": "CLI UX review",
            "blurb": "Spot the one usability flaw in a --help screen — name its category.",
            "path": "/status", "anchor": "status-b10-cliux"}
