"""Type completeness contract (F-50).

Every new exercise type ships with six parts: generator, grader,
widget (render branch), disclosure (grading.py table), emission
(pipeline BLOOM_DEFAULT_TYPES), and an e2e answer fixture. This
module is a pure audit library over plain data — the parent passes
exercises.TYPES / GENERATORS / BLOOM plus the pipeline map and the
grading table as simple collections; this module NEVER imports
groundwork, touches the DB, or defines a new exercise type number.
Precedent: highlight.py ships as a tested library + live status demo.

Registry shape (plain data, db-free)::

    {
        "generator":  {72, ...},  # GENERATORS keys
        "grader":     {72, ...},  # grade-branch types
        "widget":     {72, ...},  # render-branch types
        "disclosure": {72, ...},  # grading-table keys
        "emission":   {72, ...},  # union of BLOOM_DEFAULT_TYPES values
        "e2e":        {72, ...},  # types with an e2e answer fixture
    }

Each value may be a set, list, tuple, or dict (dict reads as its
keys). Anything else fails closed to "missing" for that part.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b12-typecontract"

_PARTS = ("generator", "grader", "widget", "disclosure", "emission", "e2e")


def required_parts() -> tuple:
    """The six parts every exercise type must ship; fails closed."""
    try:
        if tuple(_PARTS) == ("generator", "grader", "widget",
                             "disclosure", "emission", "e2e"):
            return _PARTS
        return ("generator", "grader", "widget",
                "disclosure", "emission", "e2e")
    except Exception:  # noqa: BLE001 — part list must never raise
        return ("generator", "grader", "widget",
                "disclosure", "emission", "e2e")


def _as_set(value) -> set:
    """Collection of type numbers as a set of ints; never raises."""
    try:
        if isinstance(value, dict):
            items = list(value.keys())
        elif isinstance(value, (set, frozenset, list, tuple)):
            items = list(value)
        else:
            return set()
        out = set()
        for v in items:
            try:
                out.add(int(v))
            except (TypeError, ValueError):
                continue
        return out
    except Exception:  # noqa: BLE001 — normalization must never raise
        return set()


def audit_type(type_num, registry: dict) -> dict:
    """Audit one type against a passed-in registry dict.

    Returns {"type": n, "ok": bool, "missing": [...]}. Unknown or
    malformed input fails closed (ok=False, all parts missing);
    never raises.
    """
    try:
        parts = required_parts()
        try:
            n = int(type_num)
        except (TypeError, ValueError):
            return {"type": type_num, "ok": False, "missing": list(parts)}
        if not isinstance(registry, dict):
            return {"type": n, "ok": False, "missing": list(parts)}
        missing = [p for p in parts if n not in _as_set(registry.get(p))]
        return {"type": n, "ok": not missing, "missing": missing}
    except Exception:  # noqa: BLE001 — audit must never raise
        try:
            return {"type": type_num, "ok": False,
                    "missing": list(required_parts())}
        except Exception:  # noqa: BLE001 — last resort
            return {"type": 0, "ok": False,
                    "missing": ["generator", "grader", "widget",
                                "disclosure", "emission", "e2e"]}


def completeness(report) -> dict:
    """Summarize a list of audit_type() dicts; never raises.

    Returns {"total","complete","incomplete","rate","missing_types"}.
    """
    try:
        rows = list(report) if report else []
    except Exception:  # noqa: BLE001 — summary must never raise
        return {"total": 0, "complete": 0, "incomplete": 0,
                "rate": 0.0, "missing_types": []}
    try:
        total = len(rows)
        missing_types = [r.get("type") for r in rows
                         if not isinstance(r, dict) or not r.get("ok")]
        complete = total - len(missing_types)
        rate = (complete / total) if total else 0.0
        return {"total": total, "complete": complete,
                "incomplete": len(missing_types), "rate": rate,
                "missing_types": missing_types}
    except Exception:  # noqa: BLE001 — summary must never raise
        return {"total": 0, "complete": 0, "incomplete": 0,
                "rate": 0.0, "missing_types": []}


def _cell(ok: bool) -> str:
    return "yes" if ok else "<b>no</b>"


def section_html(report=None) -> str:
    """Anchored status subsection with a demo table sketch.

    Zero-arg renders a static sketch (one complete row, one
    incomplete row). The parent may pass a live report list from
    audit_type() for a live table. Db-free; wired into the status
    page by the parent (batch12.py). Never raises.
    """
    try:
        parts = required_parts()
        head = "".join(f"<th>{html.escape(p)}</th>" for p in parts)
        if isinstance(report, list) and report:
            rows = ""
            for r in report[:12]:
                try:
                    n = int(r.get("type")) if isinstance(r, dict) else 0
                    miss = set(r.get("missing", [])) if isinstance(r, dict) else set(parts)
                    ok = bool(r.get("ok")) if isinstance(r, dict) else False
                except Exception:  # noqa: BLE001 — one bad row skips
                    continue
                tds = "".join(f"<td>{_cell(p not in miss)}</td>" for p in parts)
                rows += (f"<tr><td>{n}</td>{tds}"
                         f"<td>{'ok' if ok else 'gap'}</td></tr>")
        else:
            tds_ok = "".join("<td>yes</td>" for _ in parts)
            tds_gap = "".join("<td>yes</td>" if p in
                              ("generator", "widget", "disclosure", "emission")
                              else "<td><b>no</b></td>"
                              for p in parts)
            rows = (f"<tr><td>72</td>{tds_ok}<td>ok</td></tr>"
                    f"<tr><td>99</td>{tds_gap}<td>gap</td></tr>")
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Type completeness contract "
            "<small>(feature)</small></h3>"
            "<p>Every new exercise type ships with six parts — "
            "<code>generator</code>, <code>grader</code>, "
            "<code>widget</code>, <code>disclosure</code>, "
            "<code>emission</code>, <code>e2e</code> — or it does not "
            "ship. <code>groundwork/typecontract.py</code> audits a "
            "passed-in registry dict (db-free, stdlib only, never "
            "raises); the sketch below shows a complete type and one "
            "missing its grader and e2e answer.</p>"
            f"<table class='log'><tr><th>Type</th>{head}<th>Verdict</th></tr>"
            f"{rows}</table>"
        )
    except Exception:  # noqa: BLE001 — status must never raise
        return (f"<h3 id='{STATUS_ANCHOR}'>Type completeness contract "
                "<small>(feature)</small></h3>"
                "<p>Type audit unavailable; the contract still holds.</p>")


def tour_entry() -> dict:
    """Tour registry entry for this feature; never raises."""
    try:
        anchor = STATUS_ANCHOR
    except Exception:  # noqa: BLE001 — entry must never raise
        anchor = "status-b12-typecontract"
    return {"id": "type-contract", "kind": "feature",
            "title": "Type completeness contract",
            "blurb": "Every exercise type proves six parts — generator, "
                     "grader, widget, disclosure, emission, e2e answer — "
                     "audited live below.",
            "path": "/status", "anchor": anchor}
