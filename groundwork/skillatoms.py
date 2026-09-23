"""Skill-atom decomposition (F-99).

Splits a failing concept into small ordered sub-skills ("atoms") from
recent graded attempts, so reteach can target the failing part instead
of replaying the whole concept. Pure functions, stdlib only, no I/O.

Caller: MCPServer.submit_review post-grade path (groundwork/mcp.py):
when a card fails twice in a row, the queue calls decompose() over the
card's recent reviews and renders section_html() on the result page
(groundwork/web.py) beside the relief banner. Legacy no-data fallback:
fallback_plan() returns the whole concept as a single atom so old
callers with no attempt history keep working.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b21-skillatoms"

MAX_ATOMS = 4

_ATOM_ORDER = ("recall", "discriminate", "procedure", "transfer")

_ATOM_LABELS = {
    "recall": "Recall the definition",
    "discriminate": "Tell it apart from lookalikes",
    "procedure": "Apply the steps in order",
    "transfer": "Use it in a new case",
}

# Stems have no trailing \b on purpose: it must match "confused",
# "steps", "defined" — the words miss notes actually contain.
_PATTERNS: tuple[tuple[str, str], ...] = (
    ("recall", r"\b(what is|define|definition|mean by|forgot|blank)"),
    ("discriminate", r"\b(vs\.?|versus|instead of|confus|mistook|rather than|difference)"),
    ("procedure", r"\b(order|sequence|step|first.*then|missed.*arg|syntax|signature|import|call)"),
    ("transfer", r"\b(new case|different|edge|adapt|generaliz|real code)"),
)


def _norm(text) -> str:
    if not isinstance(text, str):
        return ""
    return text.strip().lower()


def classify_miss(error: str) -> str:
    """Map one miss note to an atom kind; unknown text -> procedure."""
    t = _norm(error)
    if not t:
        return "procedure"
    for kind, pat in _PATTERNS:
        if re.search(pat, t):
            return kind
    return "procedure"


def decompose(concept: str, attempts: list[dict] | None,
              max_atoms: int = MAX_ATOMS) -> list[dict]:
    """Split a failing concept into <= max_atoms ordered sub-skills.

    attempts: recent graded dicts with keys ok (bool), error/note (str),
    etype (exercise type, optional). Only misses (ok falsy) vote.
    Returns atoms: [{atom, label, misses, probe}]. No misses or no
    history -> [fallback atom]. Pure; never raises on bad input.
    """
    name = concept.strip() if isinstance(concept, str) and concept.strip() else "concept"
    try:
        limit = int(max_atoms)
    except (TypeError, ValueError):
        limit = MAX_ATOMS
    limit = max(1, min(limit, MAX_ATOMS))
    votes: dict[str, int] = {}
    if isinstance(attempts, (list, tuple)):
        for a in attempts:
            if not isinstance(a, dict):
                continue
            if a.get("ok"):
                continue
            err = a.get("error", a.get("note", a.get("back", "")))
            votes[classify_miss(err)] = votes.get(classify_miss(err), 0) + 1
    if not votes:
        return [fallback_atom(name)]
    ranked = sorted(votes, key=lambda k: (-votes[k], _ATOM_ORDER.index(k)))
    atoms = []
    for kind in ranked[:limit]:
        atoms.append({
            "atom": f"{name}::{kind}",
            "label": _ATOM_LABELS[kind],
            "misses": votes[kind],
            "probe": f"One-question probe: {_ATOM_LABELS[kind].lower()} for '{name}'.",
        })
    atoms.sort(key=lambda d: _ATOM_ORDER.index(d["atom"].split("::")[-1]))
    return atoms


def fallback_atom(concept: str) -> dict:
    """Legacy single-atom plan when no attempt history exists."""
    return fallback_plan(concept)[0]


def fallback_plan(concept: str) -> list[dict]:
    """Whole-concept single atom; keeps callers with no data working."""
    name = concept.strip() if isinstance(concept, str) and concept.strip() else "concept"
    return [{"atom": f"{name}::all", "label": f"Review '{name}' as a whole",
             "misses": 0, "probe": f"One-question probe: recall '{name}'."}]


def needs_split(attempts: list[dict] | None, fails: int = 2) -> bool:
    """True when consecutive trailing misses reach `fails` (default 2)."""
    if not isinstance(attempts, (list, tuple)) or not attempts:
        return False
    try:
        bar = int(fails)
    except (TypeError, ValueError):
        bar = 2
    run = 0
    for a in reversed(attempts):
        if isinstance(a, dict) and not a.get("ok"):
            run += 1
        else:
            break
    return run >= max(1, bar)


def section_html(concept: str, atoms: list[dict] | None) -> str:
    """Atoms as an HTML list; empty input renders as empty string."""
    if not atoms:
        return ""
    name = html.escape(concept.strip() if isinstance(concept, str) and concept.strip() else "concept")
    items = []
    for a in atoms:
        if not isinstance(a, dict):
            continue
        items.append(f"<li><strong>{html.escape(str(a.get('label', 'atom')))}</strong>"
                     f" — {html.escape(str(a.get('probe', '')))}"
                     f" ({int(a.get('misses', 0))} miss(es))</li>")
    if not items:
        return ""
    return (f"<section class='skill-atoms' id='skill-atoms'>"
            f"<p><strong>Sub-skills for {name}</strong></p>"
            f"<ol>{''.join(items)}</ol></section>")


def status_section() -> str:
    """Anchored status subsection with a live atoms sample; db-free.

    Named status_section (not section_html) because section_html here
    renders a concept's atoms for the result page, not a status block.
    """
    try:
        sample = section_html(
            "retrieval practice",
            decompose("retrieval practice",
                      [{"ok": False, "error": "forgot the definition"},
                       {"ok": False, "error": "wrong order of steps"}]))
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Skill atoms "
            "<small>(feature)</small></h3>"
            "<p>When a card fails twice in a row, the concept splits "
            "into ordered sub-skills so reteach targets the failing "
            "part instead of replaying the whole card. A live sample "
            "renders below.</p>"
            f"{sample}"
        )
    except Exception:  # noqa: BLE001 -- status must always render
        return f"<h3 id='{STATUS_ANCHOR}'>Skill atoms</h3>"


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {"id": "skill-atoms", "kind": "feature",
            "title": "Split the miss into sub-skills",
            "blurb": ("Two fails in a row split the concept into small "
                     "ordered sub-skills so reteach hits the failing part."),
            "path": "/status", "anchor": STATUS_ANCHOR}
