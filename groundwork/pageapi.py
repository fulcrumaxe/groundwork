"""Pagination-retrofit exercise (type 68, F-45, bloom: apply).

The learner retrofits ``?page=``/``?per_page=`` paging onto a given
unpaged list endpoint and submits the three resulting pages as
``page=<json>`` lines. The grader recomputes the expected slices from
the in-payload fixture (23 rows, stable ascending-id order) and
checks: page-1 slice exact, page-2 slice exact (no overlap or gap),
one consistent ``total`` everywhere, stable order, and an empty-items
out-of-range page. A paging contract either holds or it does not —
no partial credit. Static and deterministic, stdlib only.

``generate`` never returns None and never raises: thin input yields
an ungrounded fallback card the pipeline skips.

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
import json
import re

TYPE_NUM = 68
TYPE_NAME = "page-retrofit"
BLOOM = "apply"
STATUS_ANCHOR = "status-b11-pageapi"

_N_ROWS = 23
_PER_PAGE_DEFAULT = 5
_PER_PAGE_MAX = 20


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _clean_resource(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", str(name or "").lower()).strip("-")
    return cleaned or "items"


def _fixture_rows(ex_id, resource: str) -> list:
    try:
        digest = hashlib.sha256(str(ex_id).encode()).hexdigest()
    except Exception:  # noqa: BLE001 — seeding must never raise
        digest = "0" * 64
    tag = digest[:6]
    return [{"id": i + 1, "name": f"{resource}-{tag}-{i + 1:02d}"}
            for i in range(_N_ROWS)]


def _keyed(submission: str) -> dict:
    """Parse `page=<json>` lines into {page: value}; never raises."""
    out: dict = {}
    try:
        for line in str(submission).splitlines():
            if "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip().lower()
            if key in ("page1", "page2", "page99"):
                out[key] = val.strip()
    except Exception:  # noqa: BLE001 — parsing must never raise
        pass
    return out


def _page(rows, num: int, per_page: int) -> dict:
    start = (num - 1) * per_page
    return {"items": rows[start:start + per_page], "page": num,
            "per_page": per_page, "total": len(rows)}


def _front_text(resource: str) -> str:
    handler = (f"def list_{resource}():\n"
               f"    return get_all_{resource}()  # full list, no paging\n")
    return (
        f"Page this endpoint (default `per_page={_PER_PAGE_DEFAULT}`, "
        f"max {_PER_PAGE_MAX}):\n```python\n{handler}```\n"
        f"Contract: `GET /{resource}?page=` (1-based, default 1) and "
        f"`?per_page=` (default {_PER_PAGE_DEFAULT}). Reply with three "
        f"`page=<json>` lines (pages 1, 2, and 99) shaped "
        "`{\"items\": [...], \"page\": p, \"per_page\": n, \"total\": T}` "
        f"using `per_page={_PER_PAGE_DEFAULT}`."
    )


def _hints(resource: str) -> list[str]:
    return [
        f"Slice, don't filter: page p holds rows [(p-1)*{_PER_PAGE_DEFAULT}, p*{_PER_PAGE_DEFAULT}].",
        "`total` is the full row count — identical on every page.",
        "Page 99 is past the end: `items` empty, `total` still full.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a page-retrofit card; never None, never raises."""
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        snippet = list(snippet or [])
        name = _concept_field(concept, "name", "")
        file = _concept_field(concept, "file", "") or "api.py"
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        if name or any(str(l).strip() for l in snippet):
            resource = _clean_resource(name or "items")
            grounded = True
        else:
            resource = "items"
            grounded = False
        rows = _fixture_rows(ex_id, resource)
        back = ("Reference (page 1):\n"
                f"{json.dumps(_page(rows, 1, _PER_PAGE_DEFAULT))}")
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", resource),
            "concept": name or resource, "file": file, "line": line,
            "commit": commit,
            "hints": _hints(resource),
            "front": _front_text(resource), "back": back,
            "payload": {"resource": resource, "rows": rows,
                        "per_page_default": _PER_PAGE_DEFAULT,
                        "per_page_max": _PER_PAGE_MAX,
                        "total": len(rows), "grounded": grounded},
        }
    except Exception:
        return {  # generate never raises and never returns None
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "items", "concept": "items",
            "file": "api.py", "line": 0, "commit": "",
            "hints": _hints("items"),
            "front": _front_text("items"), "back": "see the contract",
            "payload": {"resource": "items", "rows": [],
                        "per_page_default": _PER_PAGE_DEFAULT,
                        "per_page_max": _PER_PAGE_MAX,
                        "total": 0, "grounded": False},
        }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Static slice/total/order gate; no partial credit."""
    _ = runner
    try:
        p = (exercise or {}).get("payload", {}) or {}
        rows = p.get("rows")
        if not isinstance(rows, list) or not rows:
            return _fail("Card has no fixture rows.")
        per_page = _PER_PAGE_DEFAULT
        given = _keyed(submission if submission is not None else "")
        if not given:
            return _fail("Submit three `page=<json>` lines (pages 1, 2, 99).")
        pages = {}
        for key, num in (("page1", 1), ("page2", 2), ("page99", 99)):
            raw = given.get(key)
            if raw is None:
                return _fail(f"Missing `{key}=<json>` line.")
            try:
                pages[num] = json.loads(raw)
            except ValueError:
                return _fail(f"`{key}` is not valid JSON.")
            if not isinstance(pages[num], dict):
                return _fail(f"`{key}` must be a page object.")
        total = len(rows)
        for num in (1, 2, 99):
            pg = pages[num]
            if pg.get("total") != total:
                return _fail(f"`total` must be {total} on every page.")
            if pg.get("page") != num or pg.get("per_page") != per_page:
                return _fail("Each page must echo its `page` and "
                              f"`per_page={per_page}`.")
        if pages[1].get("items") != rows[0:per_page]:
            return _fail("Page-1 slice does not match the fixture.")
        if pages[2].get("items") != rows[per_page:2 * per_page]:
            return _fail("Page-2 slice does not match (no overlap, no gap).")
        combo = list(pages[1].get("items", [])) + list(pages[2].get("items", []))
        if combo != rows[0:2 * per_page]:
            return _fail("Pages 1–2 break stable fixture order.")
        if pages[99].get("items") != []:
            return _fail("Out-of-range pages return empty `items`.")
        return {"pass": True, "score": 1.0,
                "feedback": "Paging contract holds: slices, total, order, tail."}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — submit JSON lines.")


def render(exercise: dict) -> str:
    """Exercise widget: endpoint spec plus three page inputs."""
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    inputs = "".join(
        f"<label>{key} <input name='{key}' size='60' "
        f"placeholder='{key}={{\"items\": [...]}}'></label><br>"
        for key in ("page1", "page2", "page99"))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Every page slice must match the fixture with a "
        f"consistent total and stable order; out-of-range pages return "
        f"empty items — no partial credit.</small></p></details>"
        f"<form method='post'>{inputs}<button>Check paging</button></form>"
        f"{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Page the endpoint <small>(feature)</small></h3>"
        "<p>Retrofit <code>?page=</code>/<code>?per_page=</code> paging onto "
        "an unpaged list endpoint — every page slice must match the fixture "
        "with a consistent <code>total</code> and stable order, and "
        "out-of-range pages return empty items (no partial credit). "
        "<code>groundwork/pageapi.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "page-the-endpoint", "kind": "feature",
            "title": "Page the endpoint",
            "blurb": "Retrofit paging onto a list endpoint — slices, total, and stable order checked.",
            "path": "/status", "anchor": "status-b11-pageapi"}
