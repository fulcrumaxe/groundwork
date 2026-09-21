"""Delayed-retest engine: 7/30-day probe cards measuring true retention (F-51).

Same-day fluency never counts: probes resurface owned/stable cards once
their last review sits 7 or 30 days in the past, with no intervening
probe since that review. Probe outcomes feed the north-star delayed
accuracy on mature cards (see groundwork/northstar.py, mature 21+ days);
this module only selects and builds the probes — it never grades and
never duplicates that metric. Pure functions of passed-in dicts,
stdlib only, no groundwork imports, no DB/schema. Fail-closed:
never raises.
"""
from __future__ import annotations

from datetime import datetime, timezone

STATUS_ANCHOR = "status-b12-retest"

PROBE_DAYS: tuple = (7, 30)

# A card counts as stable once it would survive to the first probe
# window. Probes at 7/30 days graduate cards toward the north-star
# maturity threshold (21+ days); the threshold itself lives in
# northstar.py and is referenced here, not redefined as a metric.
STABLE_DAYS = 7.0

_FORMATS = ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d")


def _parse(value) -> datetime | None:
    """Parse an ISO date/datetime string; None on anything unparseable."""
    try:
        if not isinstance(value, str) or not value.strip():
            return None
        text = value.strip()
        if text.endswith("Z"):
            try:
                return datetime.strptime(text, _FORMATS[0]).replace(
                    tzinfo=timezone.utc)
            except ValueError:
                pass
        for fmt in _FORMATS:
            try:
                parsed = datetime.strptime(text, fmt)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)
            except ValueError:
                continue
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            return None
    except Exception:  # noqa: BLE001 — date parsing must never raise
        return None


def _utcnow() -> datetime:
    try:
        return datetime.now(timezone.utc)
    except Exception:  # noqa: BLE001 — clock must never raise
        return datetime(2000, 1, 1, tzinfo=timezone.utc)


def _as_now(now) -> datetime:
    """Coerce now (datetime | ISO str | None) to aware datetime."""
    try:
        if now is None:
            return _utcnow()
        if isinstance(now, datetime):
            if now.tzinfo is None:
                return now.replace(tzinfo=timezone.utc)
            return now.astimezone(timezone.utc)
        parsed = _parse(now)
        return parsed if parsed is not None else _utcnow()
    except Exception:  # noqa: BLE001 — now coercion must never raise
        return _utcnow()


def _owned(card: dict) -> bool:
    try:
        if not isinstance(card, dict):
            return False
        return bool(card.get("owned"))
    except Exception:  # noqa: BLE001 — ownership check must never raise
        return False


def _stability(card: dict) -> float | None:
    """Card stability in days; None when missing/non-numeric/unstable."""
    try:
        raw = card.get("stability", card.get("prev_stability"))
        value = float(raw)
        if value != value or value == float("inf") or value == float("-inf"):
            return None
        if value < STABLE_DAYS:
            return None
        return value
    except (TypeError, ValueError, AttributeError):
        return None
    except Exception:  # noqa: BLE001 — stability check must never raise
        return None


def _window_for(elapsed_days: int) -> int | None:
    try:
        if elapsed_days >= PROBE_DAYS[1]:
            return PROBE_DAYS[1]
        if elapsed_days >= PROBE_DAYS[0]:
            return PROBE_DAYS[0]
        return None
    except Exception:  # noqa: BLE001 — window lookup must never raise
        return None


def probes_due(cards: list[dict], now=None) -> list[dict]:
    """Probe cards due: owned/stable, last review past a 7/30-day window.

    Each item is {"card_id", "window": 7|30, "overdue_days"}. A card
    with a ``last_probe`` at or after its ``last_review`` was already
    probed for this cycle and is skipped. Malformed dates, missing
    keys, and non-dict rows are skipped fail-closed; never raises.
    """
    try:
        if not isinstance(cards, list):
            return []
        moment = _as_now(now)
        out: list[dict] = []
        for card in cards:
            try:
                if not isinstance(card, dict):
                    continue
                if not _owned(card):
                    continue
                if _stability(card) is None:
                    continue
                reviewed = _parse(card.get("last_review",
                                           card.get("last_review_at",
                                                    card.get("reviewed_at"))))
                if reviewed is None:
                    continue
                elapsed = (moment - reviewed).total_seconds() / 86400.0
                if elapsed < PROBE_DAYS[0]:
                    continue
                probed = _parse(card.get("last_probe",
                                         card.get("probed_at")))
                if probed is not None and probed >= reviewed:
                    # A probe already covers this review cycle; unless
                    # the card explicitly lists uncovered windows, skip.
                    try:
                        uncovered = card.get("unprobed_windows")
                        if not isinstance(uncovered, (list, tuple)):
                            continue
                    except Exception:  # noqa: BLE001 — skip fail-closed
                        continue
                window = _window_for(int(elapsed // 1))
                if window is None:
                    continue
                if probed is not None and probed >= reviewed:
                    try:
                        if window not in set(uncovered):
                            continue
                    except Exception:  # noqa: BLE001 — skip fail-closed
                        continue
                cid = card.get("card_id", card.get("id"))
                try:
                    cid = int(cid)
                except (TypeError, ValueError):
                    try:
                        cid = str(cid) if cid is not None else None
                    except Exception:  # noqa: BLE001 — id must never raise
                        cid = None
                if cid is None:
                    continue
                overdue = max(0, int(elapsed // 1) - window)
                out.append({"card_id": cid, "window": window,
                            "overdue_days": overdue})
            except Exception:  # noqa: BLE001 — one bad row skips, never raises
                continue
        out.sort(key=lambda r: (-r["window"], -r["overdue_days"]))
        return out
    except Exception:  # noqa: BLE001 — selector must never raise
        return []


def probe_card(card: dict) -> dict:
    """Build a probe card naming the original concept; never raises.

    Returns {"front", "back", "window"}. ``window`` mirrors
    _window_for on elapsed-since-review (30 when past 30 days, else
    7); an explicit valid ``window`` key on the card is honored.
    Unknown concept/front/back fall back to generic labels.
    """
    try:
        if not isinstance(card, dict):
            return {"front": "Retest (7d): an earlier concept",
                    "back": "", "window": 7}
        try:
            explicit = int(card.get("window", 0))
            window = explicit if explicit in PROBE_DAYS else None
        except (TypeError, ValueError):
            window = None
        if window is None:
            try:
                reviewed = _parse(card.get("last_review",
                                           card.get("last_review_at",
                                                    card.get("reviewed_at"))))
                if reviewed is None:
                    window = PROBE_DAYS[0]
                else:
                    elapsed = (_utcnow() - reviewed).total_seconds() / 86400.0
                    window = _window_for(int(elapsed // 1)) or PROBE_DAYS[0]
            except Exception:  # noqa: BLE001 — window defaults to 7
                window = PROBE_DAYS[0]
        try:
            concept = card.get("concept") or card.get("concept_id") or "earlier concept"
            concept = str(concept).strip() or "earlier concept"
        except Exception:  # noqa: BLE001 — concept label must never raise
            concept = "earlier concept"
        try:
            front_src = card.get("front") or card.get("question") or ""
            front_src = str(front_src).strip()
        except Exception:  # noqa: BLE001 — front must never raise
            front_src = ""
        try:
            back_src = card.get("back") or card.get("answer") or ""
            back_src = str(back_src).strip()
        except Exception:  # noqa: BLE001 — back must never raise
            back_src = ""
        front = f"Retest ({window}d): {concept}"
        if front_src:
            front += f" — {front_src}"
        return {"front": front, "back": back_src, "window": window}
    except Exception:  # noqa: BLE001 — builder must never raise
        return {"front": "Retest (7d): an earlier concept",
                "back": "", "window": 7}


def tour_entry() -> dict:
    """Tour registry entry for the delayed-retest feature; never raises."""
    try:
        return {"id": "delayed-retest", "kind": "feature",
                "title": "Delayed retest",
                "blurb": "7- and 30-day probe cards resurface owned concepts so recalls measure true retention.",
                "path": "/status", "anchor": STATUS_ANCHOR}
    except Exception:  # noqa: BLE001 — tour entry must never raise
        return {"id": "delayed-retest", "kind": "feature",
                "title": "Delayed retest",
                "blurb": "7- and 30-day probe cards resurface owned concepts.",
                "path": "/status", "anchor": "status-b12-retest"}


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        days = f"{PROBE_DAYS[0]}/{PROBE_DAYS[1]}"
    except Exception:  # noqa: BLE001 — status must never raise
        days = "7/30"
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Delayed retest <small>(feature)</small></h3>"
        f"<p>Owned, stable cards resurface as {days}-day probe cards once "
        "their last review sits past a window with no intervening probe. "
        "Probes name the original concept and feed the north-star delayed "
        "accuracy on mature cards (same-day fluency never counts). "
        "<code>groundwork/retest.py</code> provides pure "
        "<code>probes_due()</code>/<code>probe_card()</code> helpers with "
        "fail-closed ISO parsing — never raise, no DB, no schema.</p>"
    )
