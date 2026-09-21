"""SQL-authoring exercise (type 55, F-32, bloom: apply).

The learner writes a SQL SELECT from a spec + tiny fixture schema;
graded by running it against a fresh in-memory sqlite3 fixture and
comparing result sets. The card is self-contained: schema, seed rows,
reference query, and expected result set all live in the payload
(grounded=True always, so the pipeline needs no skip guard).
Stdlib only (``sqlite3``/``re``/``html``), import-safe standalone:
no groundwork imports; the app DB is untouched (fixture is :memory:).

Read-only grading posture: only a single SELECT- or WITH-headed
statement runs, on a fresh :memory: DB with PRAGMA query_only=ON;
everything else (empty, multi-statement, non-SELECT, SQL errors,
hostile input) fails closed with feedback and never raises.

Order rule: result sets compare as multisets (order-insensitive)
unless the spec says ORDER BY, when row order must match exactly.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES).
"""
from __future__ import annotations

import hashlib
import html
import re
import sqlite3
from collections import Counter

TYPE_NUM = 55
TYPE_NAME = "sql-authoring"
BLOOM = "apply"
STATUS_ANCHOR = "status-b9-sqlex"

TABLE = "items"
SCHEMA = ("CREATE TABLE items (id INTEGER PRIMARY KEY, "
          "name TEXT, qty INTEGER)")
MAX_SUBMIT = 5000

_HEAD = re.compile(r"^(SELECT|WITH)\b", re.IGNORECASE)
_LINE_COMMENT = re.compile(r"^--[^\n]*\n?")
_BLOCK_COMMENT = re.compile(r"^/\*.*?\*/", re.DOTALL)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _seed(ex_id, cname: str) -> int:
    h = hashlib.sha256(f"{ex_id}|{cname}".encode()).hexdigest()
    return int(h[:8], 16)


def _clean_word(text) -> str:
    w = re.sub(r"[^A-Za-z0-9 ]+", "", str(text or "")).strip().split()
    return (" ".join(w)[:24].strip() or "item")


def _rows(seed: int, label: str) -> list[list]:
    base = _clean_word(label)
    out = []
    for i, sfx in enumerate(("alpha", "beta", "gamma", "delta")):
        out.append([i + 1, f"{base}-{sfx}", (seed // (6 ** i)) % 6 + 1])
    return out


def _spec(seed: int, cname: str, rows: list[list]) -> tuple[str, str, bool]:
    qtys = sorted(r[2] for r in rows)
    v = seed % 3
    if v == 0:
        k = qtys[1]
        while k > 0 and not [r for r in rows if r[2] > k]:
            k -= 1
        return (f"List the `name` and `qty` of rows with `qty` > {k} "
                "(two columns; row order does not matter).",
                f"SELECT name, qty FROM {TABLE} WHERE qty > {k}", False)
    if v == 1:
        k = qtys[1]
        return (f"List the `name` of rows with `qty` >= {k}, ordered by "
                "`name` A-Z (one column; row order matters).",
                f"SELECT name FROM {TABLE} WHERE qty >= {k} "
                "ORDER BY name", True)
    k = qtys[1]
    return (f"Return a single row: the count of rows with `qty` < {k}.",
            f"SELECT COUNT(*) AS n FROM {TABLE} WHERE qty < {k}", False)


def _run(rows: list, query: str) -> list[list]:
    con = sqlite3.connect(":memory:")
    try:
        con.execute(SCHEMA)
        con.executemany(
            f"INSERT INTO {TABLE} (id, name, qty) VALUES (?,?,?)",
            [tuple(r) for r in rows])
        return [list(r) for r in con.execute(query).fetchall()]
    finally:
        con.close()


def _fmt_row(row) -> str:
    return "(" + ", ".join(repr(c) for c in row) + ")"


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a SQL-authoring card; never raises on the generic suite ctx."""
    try:
        ctx = ctx or {}
        cname = _concept_field(concept, "name", "record") or "record"
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        seed = _seed(str(ex_id), cname)
        rows = _rows(seed, cname)
        task, ref, ordered = _spec(seed, cname, rows)
        expected = _run(rows, ref)
        shown = "\n".join(_fmt_row(r) for r in rows)
        front = (
            f"Write a SQL SELECT for `{cname}` rows.\n"
            f"Fixture schema:\n```sql\n{SCHEMA};\n```\n"
            f"Fixture rows (id, name, qty):\n```\n{shown}\n```\n"
            f"Task: {task}\n"
            "Reply with a single SELECT query (a WITH ... SELECT is fine).")
        back = ref + ";\n-- expected result set:\n" + "\n".join(
            _fmt_row(r) for r in expected)
        hints = [
            "SELECT only the asked columns — extra columns change the set.",
            ("Match row order exactly (ORDER BY name A-Z)."
             if ordered else
             "Row order is ignored — the WHERE filter is what counts."),
            "Filter on `qty` with WHERE; quote text values, not numbers.",
        ]
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", cname),
            "concept": cname, "file": file, "line": line,
            "commit": commit, "hints": hints, "front": front, "back": back,
            "payload": {"table": TABLE, "schema": SCHEMA, "rows": rows,
                        "task": task, "reference": ref,
                        "expected": expected, "ordered": ordered,
                        "grounded": True},
        }
    except Exception:  # never raise on suite ctx; minimal fallback card
        rows = [[1, "item-alpha", 3]]
        ref = f"SELECT name, qty FROM {TABLE} WHERE qty > 1"
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM, "concept_id": "fallback", "concept": "record",
            "file": "", "line": 0, "commit": "",
            "hints": ["Filter with WHERE.", "Two columns.",
                      "Reply with one SELECT."],
            "front": "Write a SELECT for one fixture row "
                     f"(`{TABLE}`: id, name, qty).",
            "back": ref + ";",
            "payload": {"table": TABLE, "schema": SCHEMA, "rows": rows,
                        "task": "fallback", "reference": ref,
                        "expected": [["item-alpha", 3]], "ordered": False,
                        "grounded": True},
        }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _strip_leading_comments(q: str) -> str:
    while True:
        q = q.lstrip()
        m = _LINE_COMMENT.match(q) or _BLOCK_COMMENT.match(q)
        if not m:
            return q
        q = q[m.end():]


def _clean_query(text) -> tuple[str | None, str]:
    q = str(text if text is not None else "").strip()
    if not q:
        return None, "Submit a single SELECT query for the spec."
    if len(q) > MAX_SUBMIT:
        return None, "Submission too large — submit just the query."
    if q.endswith(";"):
        q = q[:-1]  # one trailing semicolon tolerated, not stacked queries
    if ";" in q:  # note: also rejects ';' inside string literals (rare)
        return None, "Submit a single statement — no stacked queries."
    q = _strip_leading_comments(q).strip()
    if not q:
        return None, "Submit a single SELECT query for the spec."
    if not _HEAD.match(q):
        return None, ("Only SELECT (or WITH ... SELECT) queries run — "
                      "no writes, no DDL.")
    return q, ""


def _cell(v):
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def _norm(rows) -> list[list] | None:
    try:
        return [[_cell(c) for c in r] for r in rows]
    except TypeError:
        return None


def _key(row) -> str:
    return repr(tuple(row))


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Run the query on a fresh :memory: fixture; compare sets. Never raises."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        rows = payload.get("rows")
        expected = payload.get("expected")
        ordered = bool(payload.get("ordered", False))
        if (not isinstance(rows, list) or not rows
                or not isinstance(expected, list) or not expected
                or any(not isinstance(r, (list, tuple)) for r in
                       list(rows) + list(expected))):
            return _fail("Card has no fixture — nothing to grade.")
        q, msg = _clean_query(submission)
        if q is None:
            return _fail(msg)
        try:
            con = sqlite3.connect(":memory:")
            try:
                con.execute(str(payload.get("schema") or SCHEMA))
                con.executemany(
                    f"INSERT INTO {payload.get('table') or TABLE} "
                    "(id, name, qty) VALUES (?,?,?)",
                    [tuple(r) for r in rows])
                con.execute("PRAGMA query_only=ON")  # engine read-only
                got = [list(r) for r in con.execute(q).fetchall()]
            finally:
                con.close()
        except Exception:
            return _fail("Query did not run on the fixture — check "
                         "table/column names and syntax. Nothing graded.")
        want = _norm(expected)
        got_n = _norm(got)
        if want is None or got_n is None:
            return _fail("Could not read the result rows — retry.")
        n_cols = len(want[0])
        if any(len(r) != n_cols for r in got_n):
            return _fail(f"Column count wrong: got {len(got_n[0]) if got_n else 0}, "
                         f"want {n_cols} — SELECT only the asked columns.")
        if ordered:
            if got_n == want:
                return {"pass": True, "score": 1.0,
                        "feedback": f"Correct result set "
                                    f"({len(want)} rows in order)."}
            hits = sum(1 for a, b in zip(got_n, want) if a == b)
            score = hits / max(len(want), len(got_n), 1)
            return {"pass": False, "score": score,
                    "feedback": f"Row order/content wrong ({hits}/"
                                f"{len(want)} positions right) — the spec "
                                f"says ORDER BY, so order is graded exactly."}
        cw, cg = Counter(map(_key, want)), Counter(map(_key, got_n))
        if cw == cg:
            return {"pass": True, "score": 1.0,
                    "feedback": f"Correct result set ({len(want)} row(s))."}
        hits = sum((cw & cg).values())
        score = hits / max(len(want), len(got_n), 1)
        missing = list((cw - cg).elements())
        extra = list((cg - cw).elements())
        detail = ""
        if missing:
            detail += f" missing {missing[0]};"
        if extra:
            detail += f" unexpected {extra[0]};"
        return {"pass": False, "score": score,
                "feedback": f"{hits}/{len(want)} rows right "
                            f"(got {len(got_n)}).{detail} Check the WHERE "
                            f"filter and selected columns (order ignored)."}
    except Exception:  # noqa: BLE001 — grading never raises
        return _fail("Grader could not read the submission — submit one SELECT.")


def render(exercise: dict) -> str:
    """Card widget: spec + fixture plus a SQL answer box."""
    payload = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    note = ("Row order matters (spec says ORDER BY)."
            if payload.get("ordered") else "Row order does not matter.")
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Your query runs on a fresh in-memory fixture; "
        f"the result set must match. {html.escape(note)} "
        f"Only a single SELECT/WITH statement runs.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='8' "
        f"cols='70' placeholder='SELECT ...'></textarea><br>"
        f"<button>Run query</button></form>"
        f"{hints}<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>SQL authoring <small>(feature)</small></h3>"
        "<p>Write a SQL SELECT from a spec — graded by running it on a "
        "fresh in-memory fixture and comparing result sets (multisets, "
        "order-sensitive only under ORDER BY). "
        "<code>groundwork/sqlex.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "sql-authoring", "kind": "feature",
            "title": "SQL authoring",
            "blurb": "Write a SELECT from a spec — graded on the rows it returns.",
            "path": "/status", "anchor": "status-b9-sqlex"}
