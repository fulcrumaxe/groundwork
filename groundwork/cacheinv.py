"""Cache-invalidation reasoning exercise (type 69, F-46, bloom: analyse).

The learner studies a cached function plus four lettered mutation
paths and names every path that must bust the cache — and nothing
else. One missed bust ships stale reads, one hot-path bust wastes a
hot cache: the gate is an exact set match with no partial credit.
Static and deterministic, stdlib only.

``generate`` never returns None and never raises: thin input yields
an ungrounded fallback card (synthetic ``get_profile`` scenario) the
pipeline skips.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only, no groundwork imports.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES, grade/render branches) and
``groundwork/pipeline.py`` (BLOOM_DEFAULT_TYPES); status section and
tour entry live below.
"""

from __future__ import annotations

import hashlib
import html
import re

TYPE_NUM = 69
TYPE_NAME = "cache-invalidation"
BLOOM = "analyse"
STATUS_ANCHOR = "status-b11-cacheinv"

_LETTERS = ("A", "B", "C", "D")


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _clean_word(name: str) -> str:
    cleaned = re.sub(r"\W", "_", str(name or "")).strip("_") or "lookup"
    if cleaned[0].isdigit():
        cleaned = "lookup_" + cleaned
    return cleaned


def _rotation(ex_id) -> int:
    try:
        digest = hashlib.sha256(str(ex_id).encode()).hexdigest()
        return int(digest[:2], 16) % len(_LETTERS)
    except Exception:  # noqa: BLE001 — seeding must never raise
        return 0


def _roles(func: str, thing: str) -> list:
    """(role, description): two writers bust, the hot read must not."""
    return [
        ("hot", f"Read {thing} via {func}() — hot read path, served from cache."),
        ("write", f"Update {thing} via save_{thing}() — changes the cached value."),
        ("write", f"Delete {thing} via drop_{thing}() — removes the cached value."),
        ("other", f"Append an audit row via log_event() — never touches {thing}."),
    ]


def _scenario(func: str, thing: str, rot: int) -> tuple:
    roles = _roles(func, thing)
    order = [(i + rot) % len(roles) for i in range(len(roles))]
    paths = [{"id": _LETTERS[pos], "desc": roles[i][1]}
             for pos, i in enumerate(order)]
    answer = sorted(_LETTERS[pos] for pos, i in enumerate(order)
                    if roles[i][0] == "write")
    hot = sorted(_LETTERS[pos] for pos, i in enumerate(order)
                 if roles[i][0] == "hot")
    return paths, answer, hot


def _hints() -> list[str]:
    return [
        "A bust is needed exactly where the cached value can change.",
        "Reads never bust; unrelated writers never bust.",
        "Worked step: name the paths that rewrite or remove the value — nothing else.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a cache-invalidation card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        file = _concept_field(concept, "file", "") or "cache.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        if name or any(str(l).strip() for l in snippet):
            func = _clean_word(name or "lookup")
            grounded = True
        else:
            func = "get_profile"
            grounded = False
        thing = func.replace("get_", "").replace("fetch_", "") or "record"
        paths, answer, hot = _scenario(func, thing, _rotation(ex_id))
        listed = "\n".join(f"{p['id']}. {p['desc']}" for p in paths)
        front = (
            f"`{func}()` results are cached under key `{thing}:{{id}}`. "
            "Name EVERY mutation path that must bust the cache — "
            "and bust nothing else.\n"
            f"{listed}"
        )
        back = (f"Bust {', '.join(answer)}: the writers change or remove "
                f"the cached value. Keep {', '.join(hot)} cached "
                "(hot read path) and ignore the audit writer.")
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", func),
            "concept": name or func, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(),
            "front": front, "back": back,
            "payload": {"func": func, "cache_key": f"{thing}:{{id}}",
                        "paths": paths, "answer": answer, "hot": hot,
                        "grounded": grounded},
        }
    except Exception:
        return {  # generate never raises and never returns None
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "get_profile",
            "concept": "get_profile", "file": "cache.py", "line": 0,
            "commit": "", "hints": _hints(),
            "front": "Name every mutation path that must bust the cache.",
            "back": "Bust the writers; keep the hot read cached.",
            "payload": {"func": "get_profile", "cache_key": "profile:{id}",
                        "paths": [], "answer": [], "hot": [],
                        "grounded": False},
        }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _norm_ids(submission) -> set:
    try:
        return {c.upper() for c in re.findall(r"[a-dA-D]", str(submission))}
    except Exception:  # noqa: BLE001 — normalization never raises
        return set()


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact-set gate: every bust named, no hot path busted."""
    _ = runner
    try:
        p = (exercise or {}).get("payload", {}) or {}
        answer = p.get("answer")
        hot = p.get("hot", [])
        if not isinstance(answer, list) or not answer:
            return _fail("Card has no invalidation set.")
        want = set(answer)
        given = _norm_ids(submission)
        if not given:
            return _fail("Name the paths to bust (letters A–D).")
        missing = sorted(want - given)
        hot_hit = sorted(given & set(hot))
        extra = sorted(given - want - set(hot))
        if not missing and not hot_hit and not extra:
            return {"pass": True, "score": 1.0,
                    "feedback": "Exact bust set: writers busted, hot path kept."}
        parts = []
        if missing:
            parts.append(f"missed bust: {', '.join(missing)}")
        if hot_hit:
            parts.append(f"hot path must stay cached: {', '.join(hot_hit)}")
        if extra:
            parts.append(f"must not bust: {', '.join(extra)}")
        return _fail("Wrong bust set — " + "; ".join(parts) + ".")
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — name letters A–D.")


def render(exercise: dict) -> str:
    """Exercise widget: scenario plus one checkbox per mutation path."""
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    paths = (exercise.get("payload", {}) or {}).get("paths", [])
    boxes = "".join(
        f"<label><input type='checkbox' name='bust' value='{p['id']}'> "
        f"<b>{p['id']}</b> {html.escape(p['desc'])}</label><br>"
        for p in paths if isinstance(p, dict))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Every invalidation point must be named and no hot "
        f"path busted — exact set match; no partial credit.</small></p>"
        f"</details>"
        f"<form method='post'>{boxes}<button>Bust the cache</button></form>"
        f"{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Cache invalidation <small>(feature)</small></h3>"
        "<p>Name every mutation path that busts a cached value — exact "
        "set, no hot-path busts, no partial credit. "
        "<code>groundwork/cacheinv.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "cache-invalidation", "kind": "feature",
            "title": "Cache invalidation",
            "blurb": "Name every mutation path that busts a cached value — exact set, no hot-path busts.",
            "path": "/status", "anchor": "status-b11-cacheinv"}
