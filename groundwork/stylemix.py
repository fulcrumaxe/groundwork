"""Learning-style tuning (F-98): visual-vs-textual mix from performance.

Infers whether a learner retains more from visual or textual study
from graded review history — never from a self-report quiz. The
lesson rendering path (``Handler.module_html``) computes one affinity
for the page via :func:`records_for` and calls :func:`order_sections`
per lesson, so diagram-first vs text-first ordering follows evidence;
with no usable history the affinity is 0.0 and the legacy text-first
order is byte-identical.

Pure functions, stdlib only (``html``), no I/O, no DB changes, never
raises. Thin delegation only: web.py gains one import, one affinity
line, and the lesson loop emits visual blocks before the explainer
when the order says so; grading, sched, and History are untouched.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b21-stylemix"

VISUAL = "visual"
TEXTUAL = "textual"
MIXED = "mixed"

PASS_GRADE = 4
MIN_ATTEMPTS = 3
MAX_SHIFT = 25


def _words(value) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        return len(value.split())
    if isinstance(value, (list, tuple)):
        return sum(_words(v) for v in value)
    if isinstance(value, dict):
        return sum(_words(v) for v in value.values())
    return len(str(value).split())


def _visual_hits(lesson) -> int:
    """Count of visual evidence slots present on a lesson dict."""
    try:
        if not isinstance(lesson, dict):
            return 0
        hits = 0
        dual = lesson.get("dualcode")
        if isinstance(dual, dict):
            steps = dual.get("steps")
            if isinstance(steps, list) and any(
                    isinstance(s, str) and s.strip() for s in steps):
                hits += 1
        worked = lesson.get("worked")
        if isinstance(worked, dict):
            trace = worked.get("trace")
            if isinstance(trace, dict):
                steps = trace.get("steps")
                if isinstance(steps, list) and len(steps) > 0:
                    hits += 1
        if lesson.get("figure"):
            hits += 1
        return hits
    except Exception:  # noqa: BLE001 -- classification never raises
        return 0


def classify_card(card) -> str:
    """Kind of one card/lesson: visual, textual, or mixed.

    A dict with visual evidence (diagram steps, worked trace, or
    figure) and little study text is visual; one with study text and
    no visuals is textual; everything else (both, neither, hostile
    input) is mixed and excluded from the affinity signal.
    """
    try:
        if not isinstance(card, dict):
            return MIXED
        visual = _visual_hits(card)
        words = sum(_words(card.get(k)) for k in
                    ("summary", "docstring", "how", "key_lines", "source"))
        if visual > 0 and words < 30:
            return VISUAL
        if visual == 0 and words >= 30:
            return TEXTUAL
        return MIXED
    except Exception:  # noqa: BLE001
        return MIXED


def _pass_rate(records) -> tuple[float, int]:
    """(pass fraction, n) over grade/correct records; (0.0, 0) if none."""
    try:
        hits = 0
        total = 0
        for rec in records or []:
            if isinstance(rec, dict):
                grade = rec.get("grade", rec.get("correct"))
            elif isinstance(rec, (list, tuple)) and len(rec) >= 2:
                grade = rec[1]
            else:
                grade = rec
            if grade is None:
                continue
            if isinstance(grade, str):
                text = grade.strip().lower()
                if text in ("", "none", "null", "error"):
                    continue
                passed = text not in ("0", "false", "no", "fail", "wrong")
            elif isinstance(grade, bool):
                passed = grade
            else:
                try:
                    passed = float(grade) >= PASS_GRADE
                except (TypeError, ValueError):
                    continue
            total += 1
            hits += 1 if passed else 0
        if not total:
            return (0.0, 0)
        return (hits / total, total)
    except Exception:  # noqa: BLE001
        return (0.0, 0)


def _kind_of(rec) -> str:
    try:
        if isinstance(rec, dict):
            kind = rec.get("kind", "")
            if kind in (VISUAL, TEXTUAL):
                return kind
            return classify_card(rec.get("card", rec))
        if isinstance(rec, (list, tuple)) and len(rec) >= 1:
            first = rec[0]
            if first in (VISUAL, TEXTUAL):
                return first
            return classify_card(first)
        return MIXED
    except Exception:  # noqa: BLE001
        return MIXED


def affinity(records) -> float:
    """Visual affinity in [-1.0, +1.0] from graded history.

    ``records`` is an iterable of (kind, grade) pairs or dicts with
    ``kind`` plus ``grade``/``correct``. Positive means visual material
    is retained better, negative means textual. Mixed-kind and
    unparsable records are ignored. Fewer than MIN_ATTEMPTS usable
    attempts on either side (or none at all — the legacy no-data
    case) yields 0.0, an even mix.
    """
    try:
        visual = [r for r in (records or [])
                  if _kind_of(r) == VISUAL]
        textual = [r for r in (records or [])
                   if _kind_of(r) == TEXTUAL]
        v_rate, v_n = _pass_rate(visual)
        t_rate, t_n = _pass_rate(textual)
        if v_n < MIN_ATTEMPTS or t_n < MIN_ATTEMPTS:
            return 0.0
        return max(-1.0, min(1.0, v_rate - t_rate))
    except Exception:  # noqa: BLE001 -- tuning never raises
        return 0.0


def _field(row, key, default=None):
    """Mapping-style field read that also works on sqlite3.Row."""
    try:
        if isinstance(row, dict):
            return row.get(key, default)
        return row[key]
    except (KeyError, IndexError, TypeError):
        return default


def records_for(history, cards_by_concept, lesson_map) -> list:
    """(kind, grade) affinity records from a module page's data.

    ``history`` maps card id to review rows (mappings with ``grade``,
    newest-first); ``cards_by_concept`` maps concept id to card rows
    (plain dicts or sqlite3.Row); ``lesson_map`` maps lesson node to
    lesson dict. Each reviewed card contributes its grades paired with
    its concept lesson's visual/textual kind; mixed-kind lessons and
    gradeless rows are skipped. Order-free; hostile input yields ``[]``;
    never raises.
    """
    try:
        if not isinstance(history, dict) or not isinstance(cards_by_concept,
                                                           dict):
            return []
        lessons = lesson_map if isinstance(lesson_map, dict) else {}
        out = []
        for cid, cards in cards_by_concept.items():
            try:
                node = (str(cid).split(":", 1)[1] if ":" in str(cid)
                        else str(cid))
                kind = classify_card(lessons.get(node))
                if kind not in (VISUAL, TEXTUAL):
                    continue
                if not isinstance(cards, (list, tuple)):
                    continue
                for card in cards:
                    try:
                        rows = history.get(_field(card, "id"), [])
                        for row in (rows or []):
                            try:
                                grade = _field(row, "grade", row)
                                if grade is None:
                                    continue
                                out.append((kind, grade))
                            except (AttributeError, TypeError):
                                continue
                    except (AttributeError, TypeError):
                        continue
            except (AttributeError, TypeError):
                continue
        return out
    except Exception:  # noqa: BLE001 -- tuning never raises
        return []


def mix_for(value) -> dict:
    """{"visual", "textual"} percentages for an affinity.

    0.0 is an even 50/50; full +/-1.0 shifts MAX_SHIFT points toward
    the stronger side. Garbage fails closed to 50/50; the two shares
    always sum to 100.
    """
    try:
        amount = max(-1.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        amount = 0.0
    shift = round(amount * MAX_SHIFT)
    return {"visual": 50 + shift, "textual": 50 - shift}


def order_sections(lesson, value=0.0) -> list:
    """Section order for one lesson: text-first unless visual affinity.

    Positive affinity renders the diagram/visual block before the
    study-text block; zero or negative (including the legacy no-data
    0.0) keeps the historical text-first order, so pages without
    history render byte-identically.
    """
    try:
        sections = ["text", "visual", "practice"]
        try:
            amount = float(value)
        except (TypeError, ValueError):
            amount = 0.0
        if amount > 0 and isinstance(lesson, dict) and _visual_hits(lesson):
            sections = ["visual", "text", "practice"]
        return sections
    except Exception:  # noqa: BLE001
        return ["text", "visual", "practice"]


def recommend_line(value) -> str:
    """One-line mix summary, e.g. 'visual 60 / textual 40'."""
    try:
        mix = mix_for(value)
        return f"visual {mix['visual']} / textual {mix['textual']}"
    except Exception:  # noqa: BLE001 -- display never raises
        return "visual 50 / textual 50"


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    try:
        sample = html.escape(recommend_line(0.4))
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Learning-style tuning <small>(feature)</small></h3>"
            "<p>Visual-vs-textual mix follows graded performance, not a quiz. "
            "<code>groundwork/stylemix.py</code> computes "
            "<code>affinity()</code> from review history "
            "(visual pass rate minus textual pass rate, 3+ attempts a side) "
            "and <code>order_sections()</code> puts the stronger modality "
            "first on the lesson rendering path "
            "(<code>Handler.module_html</code>); no history keeps the legacy "
            "text-first order. A live sample renders below.</p>"
            f"<p>Even mix reads <code>{sample}</code>.</p>"
        )
    except Exception:  # noqa: BLE001 -- status must never raise
        return (f"<h3 id='{STATUS_ANCHOR}'>Learning-style tuning</h3>"
                "<p>Style-mix help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "stylemix-tuning",
        "kind": "feature",
        "title": "Learning-style tuning",
        "blurb": "Visual-vs-textual mix follows performance, not a quiz.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
