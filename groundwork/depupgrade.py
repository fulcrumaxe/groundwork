"""Dependency-upgrade exercise (type 62, F-39, bloom: modify).

The learner reads a pinned-requirement bump plus a breaking-change note
and rewrites the shown caller lines from the old API shape to the new
one. The "upgrade" is entirely static: a small fixed catalog of
fictional ``storelib`` 1.x -> 2.0.0 breaking changes (renamed kwarg,
removed function, changed return shape, new required arg), dealt
deterministically from ``ex_id`` so every card reproduces. No network,
no pip, no real packages — grading is a static shape check in the
spirit of migration.py: the submission must contain the new-API shape
(per-entry regexes, spacing/quote tolerant) and must NOT contain the
old-API shape. The sandbox runner is accepted and ignored.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only (``hashlib``/``html``/``re``), no
groundwork imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); pipeline needs no skip guard (the
catalog card is always plantable and grounded, like types 47/56).

``generate`` never raises: it returns ``None`` only when the snippet is
empty AND the concept has no usable name (no surface to ground the
card on); on the generic suite ctx it always deals a real card.
"""
from __future__ import annotations

import hashlib
import html
import re

TYPE_NUM = 62
TYPE_NAME = "dep-upgrade"
BLOOM = "modify"
STATUS_ANCHOR = "status-b10-depupgrade"
DISCLOSURE = (
    "Pass needs the new-API call shape (spacing/quotes ignored) with "
    "no leftover old-API shape; graded statically, no sandbox.")
_MAX_CHARS = 20000

_BREAKING = [
    {
        "key": "renamed-kwarg",
        "lib": "storelib",
        "old_pin": "storelib==1.4.2",
        "new_pin": "storelib==2.0.0",
        "change": "2.0.0 renamed the `timeout_ms` keyword (milliseconds) "
                  "to `timeout` (seconds).",
        "old_caller": "page = client.fetch(key, timeout_ms=5000)",
        "fixed": "page = client.fetch(key, timeout=5)",
        "new": [r"client\.fetch\s*\(\s*key\s*,\s*timeout\s*=\s*5(?:\.0)?\s*\)"],
        "old": [r"timeout_ms\s*="],
    },
    {
        "key": "removed-function",
        "lib": "storelib",
        "old_pin": "storelib==1.4.2",
        "new_pin": "storelib==2.0.0",
        "change": "2.0.0 removed `utils.flatten`; call `utils.flat_rows` "
                  "instead (same argument).",
        "old_caller": "rows = utils.flatten(table)",
        "fixed": "rows = utils.flat_rows(table)",
        "new": [r"utils\.flat_rows\s*\(\s*table\s*\)"],
        "old": [r"utils\.flatten\s*\("],
    },
    {
        "key": "return-shape",
        "lib": "storelib",
        "old_pin": "storelib==1.4.2",
        "new_pin": "storelib==2.0.0",
        "change": "2.0.0 `db.get_user` returns an `(id, name)` tuple "
                  "instead of a dict; unpack it, do not subscript it.",
        "old_caller": "user = db.get_user(uid)\nname = user[\"name\"]",
        "fixed": "_, name = db.get_user(uid)",
        "new": [r"_\s*,\s*name\s*=\s*db\.get_user\s*\(\s*uid\s*\)"],
        "old": [r"user\s*\[\s*[\"']name[\"']\s*\]"],
    },
    {
        "key": "required-arg",
        "lib": "storelib",
        "old_pin": "storelib==1.4.2",
        "new_pin": "storelib==2.0.0",
        "change": "2.0.0 `render` requires a `format` keyword; "
                  "pass `format=\"pdf\"`.",
        "old_caller": "report = render(report_data)",
        "fixed": "report = render(report_data, format=\"pdf\")",
        "new": [r"render\s*\(\s*report_data\s*,\s*format\s*=\s*[\"']pdf[\"']\s*\)"],
        "old": [],
    },
]


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _pick(ex_id: str) -> dict:
    digest = hashlib.sha256(str(ex_id).encode()).hexdigest()
    return _BREAKING[int(digest, 16) % len(_BREAKING)]


def _hints(entry: dict, file: str, line: int) -> list[str]:
    where = f"{file}:{line}" if file and line else (file or "the linked file")
    return [
        f"Read the breaking-change note first: {entry['change']}",
        f"Look at {where}: rewrite the caller so only the "
        f"{entry['new_pin']} shape remains.",
        f"Worked step: the migrated caller is `{entry['fixed']}` — "
        "submit those lines.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Deal one dep-upgrade card, or None when nothing grounds it.

    The catalog is self-contained, so any real suite ctx deals a card;
    None happens only when the snippet is empty AND the concept has no
    usable name. Never raises.
    """
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        lines = [str(l) for l in snippet if str(l).strip()]
        if not lines and not name:
            return None  # no plantable surface: nothing to ground on
        name = name or "caller"
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        entry = _pick(ex_id)
        front = (
            f"Upgrade `{entry['lib']}` `{entry['old_pin']}` -> "
            f"`{entry['new_pin']}` for `{name}`.\n"
            f"Breaking change: {entry['change']}\n"
            "Rewrite the caller lines below to the new API and submit them.\n"
            f"```python\n{entry['old_caller']}\n```"
        )
        back = f"Migrated caller:\n```python\n{entry['fixed']}\n```"
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": _hints(entry, file, line),
            "front": front, "back": back,
            "payload": {"lib": entry["lib"], "old_pin": entry["old_pin"],
                        "new_pin": entry["new_pin"], "change": entry["change"],
                        "key": entry["key"], "old_caller": entry["old_caller"],
                        "fixed": entry["fixed"], "new": list(entry["new"]),
                        "old": list(entry["old"]), "grounded": True},
        }
    except Exception:
        return None  # grading-grade safety: generate never raises


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _search(pat: str, text: str) -> bool:
    try:
        return re.search(pat, text) is not None
    except re.error:
        return False


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Pass = every new-API pattern matches AND no old-API pattern does.

    Pure-static (migration.py spirit): the runner is accepted and
    ignored, so grading never depends on the network or packages.
    Fail closed on empty/garbage/broken payloads. Never raises.
    """
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        new = list(payload.get("new", []) or [])
        old = list(payload.get("old", []) or [])
        fixed = str(payload.get("fixed", "") or "")
        if not new:
            return _fail("Exercise payload is missing the new-API shape.")
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Submit the rewritten caller lines using the new API.")
        if len(text) > _MAX_CHARS:
            return _fail("Submission too large — submit just the caller lines.")
        for pat in old:
            if _search(str(pat), text):
                return {"pass": False, "score": 0.0,
                        "feedback": f"Still uses the old API (`{pat}`) — "
                                    "a migration moves the call, never copies it. "
                                    "Drop the old shape and retry."}
        hits = sum(1 for pat in new if _search(str(pat), text))
        if hits == len(new):
            return {"pass": True, "score": 1.0,
                    "feedback": f"Caller migrated ({hits}/{len(new)} new-API "
                                "shapes, no old API left)."}
        expect = f" Expected: `{fixed}`." if fixed else ""
        return {"pass": False, "score": hits / len(new),
                "feedback": f"Missing the new-API shape ({hits}/{len(new)}).{expect}"}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit the caller lines.")


def render(exercise: dict) -> str:
    """Exercise widget: pin bump + change note + old caller + textarea."""
    payload = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    old_caller = html.escape(str(payload.get("old_caller", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<pre>{old_caller}</pre>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>{html.escape(DISCLOSURE)}</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='6' "
        f"cols='70'>{old_caller}</textarea>"
        f"<br><button>Migrate caller</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Dependency upgrade <small>(feature)</small></h3>"
        "<p>Rewrite a caller from a removed/renamed 1.x API to the 2.0.0 "
        "shape after a pin bump — graded statically (new-API shape present, "
        "old-API shape absent; spacing/quotes ignored), no network, no "
        "packages. "
        "<code>groundwork/depupgrade.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "dep-upgrade", "kind": "feature",
            "title": "Dependency upgrade",
            "blurb": "Migrate a caller across a breaking pin bump — new-API shape in, old shape out.",
            "path": "/status", "anchor": "status-b10-depupgrade"}
