"""Automatic remediation paths (F-100).

When a learner fails concept X, the Due queue pulls up to three of
X's unmastered prerequisites ahead of X so the retry is scaffolded
instead of repeated cold. Pure functions of passed-in dicts, stdlib
only, no groundwork imports, no DB/schema. Fail-closed: never raises;
empty or malformed input yields empty paths and the caller's due list
unchanged.

Caller: ``MCPServer.tool_list_due_reviews`` in groundwork/mcp.py (the
Due queue, rendered at /due): after a grade < 3 review for concept X
it lifts X's prerequisite cards -- resolved from the module lessons'
``needs`` via lessondeps -- ahead of X with :func:`queue_remediation`
and a make_card that re-queues the real due cards flagged remedial.
Prerequisites with no real card are left out so the renderer never
sees a synthetic card without an id.
"""
from __future__ import annotations

STATUS_ANCHOR = "status-b21-remedpath"

MAX_PREREQS = 3

# Grades >= 3 count as a pass (matches sched.review_card); anything
# below means the concept still needs work.
MASTERED_GRADE = 3.0


def _concepts(value) -> list:
    """Coerce a prereq-list-ish value to a clean list of names."""
    try:
        if value is None:
            return []
        if isinstance(value, str):
            return [value.strip()] if value.strip() else []
        if isinstance(value, dict):
            return _concepts(list(value))
        return [str(v).strip() for v in list(value)
                if str(v).strip()]
    except Exception:  # noqa: BLE001 — coercion must never raise
        return []


def prereqs_for(concept, prereq_map) -> list:
    """Up to MAX_PREREQS prerequisite names for concept, in map order."""
    try:
        if not isinstance(prereq_map, dict):
            return []
        key = str(concept).strip() if concept is not None else ""
        if not key:
            return []
        return _concepts(prereq_map.get(key))[:MAX_PREREQS]
    except Exception:  # noqa: BLE001 — lookup must never raise
        return []


def is_mastered(concept, mastery, threshold: float = MASTERED_GRADE) -> bool:
    """True when concept's average grade reaches threshold. Missing data: False."""
    try:
        if not isinstance(mastery, dict):
            return False
        key = str(concept).strip() if concept is not None else ""
        if not key or key not in mastery:
            return False
        grade = float(mastery[key])
        if grade != grade:  # NaN is never mastered
            return False
        limit = float(threshold)
        return grade >= limit
    except (TypeError, ValueError, AttributeError):
        return False
    except Exception:  # noqa: BLE001 — mastery check must never raise
        return False


def remediation_path(failed, prereq_map, mastery=None,
                     threshold: float = MASTERED_GRADE) -> list:
    """Ordered queue for a failure: unmastered prereqs first, failed last.

    Mastered prereqs are skipped; the failed concept itself is never
    listed as its own prereq. Empty list when nothing is known (legacy
    no-data fallback) or the input is malformed.
    """
    try:
        key = str(failed).strip() if failed is not None else ""
        if not key:
            return []
        seen = {key}
        path = []
        for pre in prereqs_for(key, prereq_map):
            if pre in seen:
                continue
            seen.add(pre)
            if not is_mastered(pre, mastery, threshold):
                path.append(pre)
        path.append(key)
        return path
    except Exception:  # noqa: BLE001 — path building must never raise
        try:
            key = str(failed).strip()
            return [key] if key else []
        except Exception:  # noqa: BLE001 — last-resort fallback
            return []


def _due_concepts(due) -> set:
    try:
        concepts = set()
        for card in due or []:
            if isinstance(card, dict):
                name = card.get("concept")
                if name is not None and str(name).strip():
                    concepts.add(str(name).strip())
        return concepts
    except Exception:  # noqa: BLE001 — scan must never raise
        return set()


def _failures(failures) -> list:
    """Coerce failures (names or card dicts) to a clean name list."""
    try:
        if failures is None:
            return []
        if isinstance(failures, str):
            return [failures.strip()] if failures.strip() else []
        names = []
        for item in list(failures):
            if isinstance(item, dict):
                name = item.get("concept", item.get("concept_id"))
            else:
                name = item
            if name is not None and str(name).strip():
                names.append(str(name).strip())
        return names
    except Exception:  # noqa: BLE001 — coercion must never raise
        return []


def _default_card(concept: str, failed: str) -> dict:
    return {"concept": concept, "remedial": True,
            "remediation_for": failed,
            "front": "Remediation for %s: recall %s first."
                     % (failed, concept),
            "back": "Revisit %s, then retry %s." % (concept, failed)}


def queue_remediation(due, failures, prereq_map, mastery=None,
                      make_card=None, threshold: float = MASTERED_GRADE) -> list:
    """New due list with remediation cards prepended ahead of failures.

    Concepts already present in due are not duplicated; mastered
    prereqs are skipped via :func:`remediation_path`. ``make_card`` is
    an optional callable ``(concept, failed) -> dict``; otherwise a
    minimal remedial card dict is built. Fail-closed: any malformed
    input returns ``list(due)`` (or [] for malformed due).
    """
    try:
        cards = list(due) if due is not None else []
    except Exception:  # noqa: BLE001 — due coercion must never raise
        return []
    try:
        if not isinstance(prereq_map, dict) or not prereq_map:
            return cards
        names = _failures(failures)
        if not names:
            return cards
        build = make_card if callable(make_card) else _default_card
        present = _due_concepts(cards)
        prepended: list = []
        queued: set = set()
        for failed in names:
            for concept in remediation_path(failed, prereq_map,
                                            mastery, threshold):
                if concept == failed or concept in present or concept in queued:
                    continue
                queued.add(concept)
                try:
                    card = build(concept, failed)
                    prepended.append(card if isinstance(card, dict)
                                     else _default_card(concept, failed))
                except Exception:  # noqa: BLE001 — bad factory falls back
                    prepended.append(_default_card(concept, failed))
        return prepended + cards
    except Exception:  # noqa: BLE001 — remediation must never raise
        return cards


def describe_path(path, failed=None) -> str:
    """One-line human summary of a remediation path."""
    try:
        items = _concepts(path)
        if not items:
            return "No remediation path: no prerequisite data."
        if failed is not None and str(failed).strip():
            tail = str(failed).strip()
            head = [c for c in items if c != tail]
            return ("To retry %s, first revisit %s."
                    % (tail, ", ".join(head)) if head
                    else "Retry %s directly: all prerequisites mastered." % tail)
        if len(items) == 1:
            return "Retry %s directly." % items[0]
        return "First revisit %s, then retry %s." % (
            ", ".join(items[:-1]), items[-1])
    except Exception:  # noqa: BLE001 — description must never raise
        return "No remediation path available."


def section_html(path, failed=None) -> str:
    """Remediation path as an HTML note; empty path renders as empty."""
    import html
    try:
        items = _concepts(path)
        if not items:
            return ""
        return ("<p class='remediation'>%s</p>"
                % html.escape(describe_path(items, failed)))
    except Exception:  # noqa: BLE001 — note must never raise
        return ""


def tour_entry() -> dict:
    """Status-tour entry for the remediation path feature."""
    return {
        "id": "remediation-path", "kind": "feature",
        "title": "Fail forward: prerequisites first",
        "blurb": ("Failing a card pulls its shaky prerequisites ahead of "
                 "the retry instead of repeating the card cold."),
        "path": "/due", "anchor": STATUS_ANCHOR}
