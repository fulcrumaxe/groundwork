"""Friendly wagers (F-128): bet coffee on delayed-test outcomes.

Bets arrive as query data (``?wager=probe:<card>:<window>`` or the
place form fields) and settle at render against MEASURED outcomes
the caller supplies (latest card grades, northstar delayed accuracy)
— never recomputed here, no DB/schema change. Stakes are coffee only:
no network, no real money. Pure functions, stdlib ``html`` only,
no groundwork imports, no I/O. Fail-closed: never raises.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-wagers"

STATUS_PAGE_ANCHOR = "status-b24-wagers"

STAKE = "coffee"

WINDOWS: tuple = (7, 30)

PASS_GRADE = 4

DEFAULT_TARGET = 0.8


def _str(value, default: str = "") -> str:
    """Coerce to stripped text; default on anything unusable."""
    try:
        if value is None:
            return default
        text = str(value).strip()
        return text if text else default
    except Exception:  # noqa: BLE001 — text coercion must never raise
        return default


def _blank() -> dict:
    """Fresh open probe wager."""
    return {"kind": "probe", "card_id": None, "window": WINDOWS[0],
            "target": None, "bettor": "you", "rival": "a friend",
            "stake": STAKE, "status": "open", "placed_at": ""}


def _copy(wager) -> dict:
    """Shallow-copy a wager dict; garbage becomes a fresh open probe."""
    try:
        if isinstance(wager, dict):
            return dict(wager)
    except Exception:  # noqa: BLE001 — copy must never raise
        pass
    return _blank()


def _window(value) -> int:
    """7/30-day window; anything else falls back to 7."""
    try:
        return int(value) if int(value) in WINDOWS else WINDOWS[0]
    except (TypeError, ValueError):
        return WINDOWS[0]


def _card_id(value):
    """int when numeric, stripped text, else None; never raises."""
    try:
        return int(value)
    except (TypeError, ValueError):
        try:
            return str(value).strip() or None
        except Exception:  # noqa: BLE001
            return None


def place_probe_wager(card_id, window: int = 7, bettor: str = "you",
                      rival: str = "a friend", placed_at: str = "") -> dict:
    """Log a coffee bet that one probe review (7- or 30-day) will pass.

    Returns a fresh ``status="open"`` wager dict. Unknown windows fall
    back to 7; unusable card ids become None (still loggable, settled
    by explicit grade later). Never raises.
    """
    try:
        window = _window(window)
        cid: object = _card_id(card_id)
        return {"kind": "probe", "card_id": cid, "window": window,
                "target": None, "bettor": _str(bettor, "you"),
                "rival": _str(rival, "a friend"), "stake": STAKE,
                "status": "open", "placed_at": _str(placed_at)}
    except Exception:  # noqa: BLE001 — placement must never raise
        return _blank()


def _goal(value) -> float:
    """0–1 target; garbage and NaN fall back to the default."""
    try:
        goal = float(value)
        if goal != goal:
            return DEFAULT_TARGET
        return round(min(1.0, max(0.0, goal)), 2)
    except (TypeError, ValueError):
        return DEFAULT_TARGET


def place_accuracy_wager(target: float = DEFAULT_TARGET, bettor: str = "you",
                         rival: str = "a friend",
                         placed_at: str = "") -> dict:
    """Log a coffee bet that mature delayed accuracy holds ``target``.

    ``target`` is clamped to 0–1 (garbage → 0.8). Settles later via
    ``settle()`` against a northstar-style snapshot dict. Never raises.
    """
    try:
        goal = _goal(target)
        return {"kind": "accuracy", "card_id": None, "window": None,
                "target": goal, "bettor": _str(bettor, "you"),
                "rival": _str(rival, "a friend"), "stake": STAKE,
                "status": "open", "placed_at": _str(placed_at)}
    except Exception:  # noqa: BLE001 — placement must never raise
        out = _blank()
        out.update({"kind": "accuracy", "window": None,
                    "target": DEFAULT_TARGET})
        return out


def _probe_spec(bits: list):
    """(card_id, window) from probe spec parts; window splits from right."""
    if len(bits) > 2:
        try:
            return ":".join(bits[1:-1]), int(bits[-1])
        except (TypeError, ValueError):
            return ":".join(bits[1:]), 7
    return bits[1], 7


def wagers_from_query(query) -> list:
    """Wager dicts from ``?wager=probe:<card>:<window>`` / ``?wager=acc:<target>`` specs.

    The place form submits the same single-spec shape. Never raises.
    """
    out = []
    try:
        if not isinstance(query, dict):
            return []
        for spec in query.get("wager", []) or []:
            try:
                bits = str(spec).split(":")
                if bits[0] == "probe" and len(bits) >= 2:
                    cid, window = _probe_spec(bits)
                    out.append(place_probe_wager(cid, window))
                elif bits[0] == "acc":
                    out.append(place_accuracy_wager(
                        bits[1] if len(bits) > 1 else DEFAULT_TARGET))
            except Exception:  # noqa: BLE001 -- one bad spec never breaks
                continue
    except Exception:  # noqa: BLE001 -- placement must never raise
        pass
    return out


def settle(wager: dict, outcome: dict) -> dict:
    """Settle one open wager against a caller-measured outcome.

    Probe wagers read ``outcome["grade"]`` (a probe review grade:
    >= 4 wins). Accuracy wagers read ``outcome["delayed_acc"]`` (a
    northstar snapshot value: ``None`` means no mature recalls yet,
    so the wager stays open). Non-open, malformed, or unmeasurable
    inputs return the wager still open — missing data never loses a
    bet. Never raises.
    """
    try:
        mine = _copy(wager)
        if mine.get("status") != "open":
            return mine
        if not isinstance(outcome, dict):
            return mine
        if mine.get("kind") == "accuracy":
            raw = outcome.get("delayed_acc", outcome.get("accuracy"))
            try:
                acc = float(raw)
            except (TypeError, ValueError):
                return mine
            if acc != acc or raw is None:  # NaN/missing is not a measurement
                return mine
            goal = _goal(mine.get("target", DEFAULT_TARGET))
            mine["status"] = "won" if acc >= goal else "lost"
            return mine
        try:
            grade = float(outcome.get("grade"))
        except (TypeError, ValueError):
            return mine
        mine["status"] = "won" if grade >= PASS_GRADE else "lost"
        return mine
    except Exception:  # noqa: BLE001 — settling must never raise
        return _copy(wager)


def settle_all(wagers, grades_by_card=None, delayed_acc=None) -> list:
    """Settle every wager against live outcomes; never raises.

    ``grades_by_card`` maps card id (str and int forms both tried) to
    its latest recorded grade; ``delayed_acc`` is the northstar mature
    delayed accuracy (None keeps accuracy wagers open).
    """
    try:
        table = {}
        for key, val in (grades_by_card or {}).items():
            try:
                table[str(key)] = val
                table[int(key)] = val
            except (TypeError, ValueError):
                table[str(key)] = val
    except Exception:  # noqa: BLE001
        table = {}
    out = []
    for wager in (wagers or []):
        try:
            mine = _copy(wager)
            if mine.get("status") != "open":
                out.append(mine)
                continue
            if mine.get("kind") == "accuracy":
                out.append(settle(mine, {"delayed_acc": delayed_acc}))
                continue
            cid = mine.get("card_id")
            grade = table.get(cid, table.get(str(cid)))
            if grade is None:
                out.append(mine)
            else:
                out.append(settle(mine, {"grade": grade}))
        except Exception:  # noqa: BLE001 -- one bad wager never breaks
            continue
    return out


def ledger_summary(wagers) -> dict:
    """Count an in-memory wager ledger; garbage ledgers read as empty.

    ``coffees_won`` (rival owes the bettor) and ``coffees_owed``
    (bettor owes the rival) count one coffee per settled wager.
    Never raises.
    """
    try:
        rows = list(wagers) if isinstance(wagers, (list, tuple)) else []
    except Exception:  # noqa: BLE001 — summary must never raise
        rows = []
    total = won = lost = 0
    try:
        for row in rows:
            try:
                status = row.get("status") if isinstance(row, dict) else None
            except Exception:  # noqa: BLE001 — one bad row never breaks
                continue
            total += 1
            if status == "won":
                won += 1
            elif status == "lost":
                lost += 1
    except Exception:  # noqa: BLE001 — summary must never raise
        return {"n": 0, "open": 0, "won": 0, "lost": 0,
                "coffees_won": 0, "coffees_owed": 0}
    return {"n": total, "open": total - won - lost, "won": won,
            "lost": lost, "coffees_won": won, "coffees_owed": lost}


def _row_html(wager: dict) -> str:
    """One ledger line; never raises."""
    try:
        mine = _copy(wager)
        who = html.escape(mine.get("bettor", "you"))
        rival = html.escape(mine.get("rival", "a friend"))
        status = mine.get("status")
        if mine.get("kind") == "accuracy":
            what = f"delayed accuracy holds {mine.get('target', DEFAULT_TARGET):.0%}"
        else:
            what = (f"probe {mine.get('window', 7)}d on card "
                    f"{html.escape(str(mine.get('card_id')))}")
        if status == "won":
            tail = f" — won, {rival} owes {who} a coffee."
        elif status == "lost":
            tail = f" — lost, {who} owes {rival} a coffee."
        else:
            tail = " — open, a coffee riding on it."
        return f"<p class='wager-{status}'>{who} vs {rival}: {what}{tail}</p>"
    except Exception:  # noqa: BLE001 — rendering must never raise
        return "<p class='wager-open'>An open coffee wager.</p>"


def place_form() -> str:
    """One-line bet placer (GET ?wager=…); always safe to render."""
    return (
        "<form class='wager-place' method='get' action='/reviews'>"
        "<label>Bet a coffee "
        "<input name='wager' size='28' "
        "placeholder='probe:CARD:7 or acc:0.8'></label> "
        "<button type='submit'>Bet coffee</button></form>")


def section_html(wagers=None) -> str:
    """Anchored History subsection: the coffee ledger, always rendered."""
    try:
        rows = list(wagers) if isinstance(wagers, (list, tuple)) else []
        rows = [r for r in rows if isinstance(r, dict)]
    except Exception:  # noqa: BLE001 — section must never raise
        rows = []
    head = (f"<h3 id='{STATUS_ANCHOR}'>Friendly wagers "
            f"<small>(feature)</small></h3>")
    if not rows:
        return (head + "<p>No wagers yet — bet a coffee on your next "
                "delayed retest. Probe passes (grade 4+) win; "
                "same-day fluency never counts.</p>" + place_form())
    try:
        summ = ledger_summary(rows)
        tally = (f"<p>{summ['won']} coffees won · {summ['lost']} owed "
                 f"· {summ['open']} open.</p>")
    except Exception:  # noqa: BLE001 — tally must never break the page
        tally = ""
    try:
        lines = "".join(_row_html(r) for r in rows)
    except Exception:  # noqa: BLE001 — rows must never break the page
        lines = ""
    return head + tally + lines + place_form()


def status_section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch24.py."""
    return (
        f"<h3 id='{STATUS_PAGE_ANCHOR}'>Friendly wagers "
        "<small>(feature)</small></h3>"
        "<p>Bet a coffee on delayed recalls — "
        "<code>groundwork/wagers.py</code> settles probe bets against "
        "recorded grades and accuracy bets against the north-star "
        "snapshot, all on the History page; no network, no real money.</p>")


def tour_entry() -> dict:
    """Tour registry entry for friendly wagers."""
    return {"id": "friendly-wagers", "kind": "feature",
            "title": "Friendly wagers",
            "blurb": "Bet a coffee on your next delayed retest — probe passes win, and the History ledger keeps score.",
            "path": "/reviews", "anchor": STATUS_ANCHOR}
