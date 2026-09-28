"""Weekend/light mode: reduced load on chosen days (I-206).

Some days the learner can only do a little; a lighter queue they
finish beats a full queue they abandon. Two URL params drive it —
``?light=sat,sun`` names the light days, ``?lightfrac=0.5`` how much
of the queue survives — so no schema change is needed (Batch-17 dial
precedent: knobs ride the URL, the queue filter stays pure).

Batch-21 cogniload precedent: strained sessions introduce fewer NEW
concepts and never drop due reviews. The reducer partitions the Due
list by newness (``cogniload.is_new`` semantics plus the caller's
``tried`` attempt map) and cuts only the new side: every review
survives, the first N new cards fill the surviving fraction, order
is preserved, and a non-empty queue always yields at least one card.

Fail-closed everywhere: unparseable days, an unparseable fraction,
or a non-light weekday returns the input list object untouched, so
the legacy full queue is the default, not a fallback branch. Pure
functions, stdlib only, no groundwork imports, no I/O. Never raises.
"""
from __future__ import annotations

import html
from datetime import date, datetime, timezone
from math import ceil

STATUS_ANCHOR = "status-b29-lightdays"

SECTION_ANCHOR = "lightdays"

DEFAULT_FRACTION = 0.5

_SHORT = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

DAY_NAMES = {
    "mon": 0, "monday": 0,
    "tue": 1, "tues": 1, "tuesday": 1,
    "wed": 2, "wednesday": 2,
    "thu": 3, "thur": 3, "thurs": 3, "thursday": 3,
    "fri": 4, "friday": 4,
    "sat": 5, "saturday": 5,
    "sun": 6, "sunday": 6,
}

PRESETS = {
    "weekend": frozenset({5, 6}),
    "weekday": frozenset({0, 1, 2, 3, 4}),
    "weekdays": frozenset({0, 1, 2, 3, 4}),
    "everyday": frozenset({0, 1, 2, 3, 4, 5, 6}),
    "daily": frozenset({0, 1, 2, 3, 4, 5, 6}),
}


def _to_int(tok) -> int | None:
    """Strict int coercion; bools and garbage yield None."""
    try:
        if isinstance(tok, bool):
            return None
        return int(str(tok).strip())
    except (TypeError, ValueError):
        return None


def parse_days(value) -> frozenset:
    """Weekday set (Mon=0..Sun=6) from a ``?light=`` value.

    Accepts presets (``weekend``, ``weekday(s)``, ``everyday``,
    ``daily``), comma-separated day names (full or short, any case),
    ints 0-6, ``name-num`` ranges (``sat-sun``, ``1-5``), single ints,
    and lists/sets of any of these. None, ``""``, ``off``/``none``/
    ``never``, and wholly unparseable input yield the empty set —
    light mode off — so bad params fail closed to the full queue.
    Never raises.
    """
    try:
        if value is None or isinstance(value, bool):
            return frozenset()
        if isinstance(value, int):
            return frozenset({value}) if 0 <= value <= 6 else frozenset()
        if isinstance(value, (list, tuple, set, frozenset)):
            out = set()
            for v in value:
                out |= parse_days(v)
            return frozenset(out)
        text = str(value).strip().lower()
        if not text or text in ("none", "off", "never"):
            return frozenset()
        if text in PRESETS:
            return PRESETS[text]
        out = set()
        for tok in text.split(","):
            tok = tok.strip()
            if not tok:
                continue
            if tok in PRESETS:
                out |= PRESETS[tok]
                continue
            if tok in DAY_NAMES:
                out.add(DAY_NAMES[tok])
                continue
            if "-" in tok:
                lo, _, hi = tok.partition("-")
                lo = DAY_NAMES.get(lo.strip(), _to_int(lo))
                hi = DAY_NAMES.get(hi.strip(), _to_int(hi))
                if (lo is not None and hi is not None
                        and 0 <= lo <= hi <= 6):
                    out.update(range(lo, hi + 1))
                continue
            n = _to_int(tok)
            if n is not None and 0 <= n <= 6:
                out.add(n)
            # Unknown tokens are ignored: one bad day never arms or
            # disarms the rest; an all-bad value stays the empty set.
        return frozenset(out)
    except Exception:  # noqa: BLE001 -- parsing never breaks the queue
        return frozenset()


def _clamp_default(default) -> float:
    """Sane default fraction; garbage default yields 0.5."""
    try:
        f = float(default)
        if f != f or f < 0.0:
            return DEFAULT_FRACTION
        return min(f, 1.0)
    except (TypeError, ValueError):
        return DEFAULT_FRACTION


def parse_fraction(value, default=DEFAULT_FRACTION):
    """Surviving queue share from a ``?lightfrac=`` value.

    None/``""`` yields ``default`` (0.5); ``"50%"``-style percents
    are honored; 0.0 means reviews-only; >= 1.0 clamps to keep-all.
    Negative, NaN, boolean, and unparseable input yield None, which
    the reducer reads as light-mode-off (fail closed to full queue).
    Never raises.
    """
    try:
        if value is None:
            return _clamp_default(default)
        if isinstance(value, bool):
            return None
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return _clamp_default(default)
            if text.endswith("%"):
                try:
                    f = float(text[:-1].strip()) / 100.0
                except (TypeError, ValueError):
                    return None
                return f if 0.0 <= f <= 1.0 else None
            value = text
        f = float(value)
        if f != f or f < 0.0:
            return None
        return min(f, 1.0)
    except (TypeError, ValueError):
        return None
    except Exception:  # noqa: BLE001 -- parsing never breaks the queue
        return None


def weekday_of(today=None):
    """Monday=0..Sunday=6 for ``today``; None means now (UTC).

    Accepts weekday ints, dates, datetimes, ISO strings, and digit
    strings. Anything unreadable yields None (never a guess, so the
    reducer fails closed). Never raises.
    """
    try:
        if today is None:
            return datetime.now(timezone.utc).weekday()
        if isinstance(today, bool):
            return None
        if isinstance(today, int):
            return today if 0 <= today <= 6 else None
        if isinstance(today, (datetime, date)):
            return today.weekday()
        if isinstance(today, str):
            text = today.strip()
            if not text:
                return None
            n = _to_int(text)
            if n is not None and 0 <= n <= 6 and text == str(n):
                return n
            return date.fromisoformat(text[:10]).weekday()
        return None
    except (TypeError, ValueError):
        return None
    except Exception:  # noqa: BLE001 -- parsing never breaks the queue
        return None


def is_light_day(days=None, today=None) -> bool:
    """True when ``today`` falls in the parsed ``?light=`` day set."""
    try:
        dayset = parse_days(days)
        if not dayset:
            return False
        w = weekday_of(today)
        return w is not None and w in dayset
    except Exception:  # noqa: BLE001 -- doubt means a full day
        return False


def _is_new(card, tried=None) -> bool:
    """Newness in the ``cogniload.is_new`` sense.

    Never-attempted cards (no tries, no review flag, no last-review
    stamp) are new; anything with attempt history is a review that
    must survive. The caller's ``tried`` id->count map overrides the
    card's own fields. Non-dict cards are never new (fail closed).
    """
    try:
        if not isinstance(card, dict):
            return False
        if isinstance(tried, dict):
            try:
                if card.get("id") in tried:
                    try:
                        return int(tried[card.get("id")] or 0) <= 0
                    except (TypeError, ValueError):
                        return True
            except TypeError:
                pass
        if card.get("is_new") is True:
            return True
        n = card.get("attempts", card.get("reviews", card.get("n", 0)))
        try:
            if int(n or 0) > 0:
                return False
        except (TypeError, ValueError):
            pass
        if card.get("last_review"):
            return False
        return True
    except Exception:  # noqa: BLE001 -- doubt keeps the card a review
        return False


def apply_light_days(due, days=None, fraction=None, today=None,
                     tried=None) -> list:
    """Reduce the Due queue on light days; reviews always survive.

    Active only when ``days`` parses non-empty, ``fraction`` parses,
    and ``today`` falls in the set — otherwise ``due`` returns
    untouched (identical object). When active: every review card is
    kept, new cards fill up to ``ceil(fraction * len(queue))`` total,
    order is preserved (filter only), the input is never mutated, and
    a non-empty queue always yields at least one card. ``tried``
    (id->attempt count) settles newness disputes. Never raises.
    """
    try:
        if not isinstance(due, list):
            return due
        if not parse_days(days):
            return due
        frac = parse_fraction(fraction)
        if frac is None:
            return due
        w = weekday_of(today)
        if w is None or w not in parse_days(days):
            return due
        rows = [c for c in due if isinstance(c, dict)]
        if not rows:
            return due
        tried_map = tried if isinstance(tried, dict) else {}
        reviews = [c for c in rows if not _is_new(c, tried_map)]
        fresh = [c for c in rows if _is_new(c, tried_map)]
        keep_new = max(0, ceil(frac * len(rows)) - len(reviews))
        drop = set(map(id, fresh[keep_new:]))
        kept = [c for c in rows if id(c) not in drop]
        return kept or [rows[0]]
    except Exception:  # noqa: BLE001 -- light mode never breaks Due
        return due


def describe(dayset=None, fraction=None) -> str:
    """One-line account of the light schedule. Never raises."""
    try:
        days = parse_days(dayset)
        frac = parse_fraction(fraction)
        if not days or frac is None:
            return "full queue every day"
        if days == PRESETS["weekend"]:
            label = "weekends"
        elif days == PRESETS["weekday"]:
            label = "weekdays"
        else:
            label = ", ".join(_SHORT[d] for d in sorted(days))
        return (f"light {label} - about {int(round(frac * 100))}% of "
                "the queue; due reviews always stay")
    except Exception:  # noqa: BLE001 -- control copy never raises
        return "full queue every day"


def light_box_html(days=None, fraction=None, mode="") -> str:
    """Due-page control: light-day presets plus the active schedule.

    Links carry ``?light=`` (session mode preserved); the line below
    describes the active schedule via describe(). Always renders so
    the ``lightdays`` anchor never moves. Never raises.
    """
    try:
        active = parse_days(days)
        frac = parse_fraction(fraction)
        suffix = f"mode={mode}&" if mode in ("one", "cold") else ""
        presets = (("off", ""), ("weekend", "weekend"),
                   ("sat", "sat"), ("sun", "sun"))
        links = " · ".join(
            f"<a href='/due?{suffix}light={slug}'>{label}</a>"
            + (" <b>(light)</b>" if parse_days(slug) == active else "")
            for label, slug in presets)
        return (f"<p id='{SECTION_ANCHOR}'><small>Light days: {links}<br>"
                f"{html.escape(describe(active, frac))}</small></p>")
    except Exception:  # noqa: BLE001 -- control never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Weekend light mode "
        "<small>(improvement)</small></h3>"
        "<p>Chosen days run a lighter Due queue — <code>?light=</code> "
        "names the days, <code>?lightfrac=</code> the surviving share — "
        "so a busy day still ends finished. <code>groundwork/lightdays.py</code> "
        "provides <code>parse_days()</code>/<code>parse_fraction()</code> "
        "(fail closed to the full queue) and "
        "<code>apply_light_days()</code> (order-preserving reducer: every "
        "due review survives, only never-attempted cards are trimmed).</p>"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "light-days",
        "kind": "improvement",
        "title": "Weekend light mode",
        "blurb": "Chosen days run a lighter Due queue — new cards "
                 "trimmed, due reviews untouched.",
        "path": "/due",
        "anchor": SECTION_ANCHOR,
    }
