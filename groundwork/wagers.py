"""Friendly wagers (F-128): bet coffee on delayed-test outcomes, logged.

A local, single-learner dare ledger: bet a coffee that a probe review
will pass, or that mature delayed accuracy will hold a target. Stakes
are coffee only — no network, no real money.

Bets are placed with plain query data (``?wager=probe:<card>:<window>``
or the place form's ``wager_kind``/``wager_card``/``wager_window`` /
``wager_target`` fields) and settle at render time against MEASURED
outcomes owned elsewhere, never recomputed here: probe windows read
the latest recorded grade for the card (pass = grade >= 4, mirroring
groundwork/retest.py) and long-horizon wagers settle on the
groundwork/northstar.py snapshot (mature 21+ day delayed accuracy).
The caller (``history.history_html``) supplies those outcomes as plain
dicts, so this module duplicates no selector, metric, or threshold
logic and needs no DB/schema change.

Pure functions of passed-in dicts/lists, stdlib only (``html``),
no groundwork imports, no DB/schema, no I/O. Fail-closed:
never raises.
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


def _copy(wager) -> dict:
    """Shallow-copy a wager dict; garbage becomes a fresh open probe."""
    try:
        if isinstance(wager, dict):
            return dict(wager)
    except Exception:  # noqa: BLE001 — copy must never raise
        pass
    return {"kind": "probe", "card_id": None, "window": WINDOWS[0],
            "target": None, "bettor": "you", "rival": "a friend",
            "stake": STAKE, "status": "open", "placed_at": ""}


def place_probe_wager(card_id, window: int = 7, bettor: str = "you",
                      rival: str = "a friend", placed_at: str = "") -> dict:
    """Log a coffee bet that one probe review (7- or 30-day) will pass.

    Returns a fresh ``status="open"`` wager dict. Unknown windows fall
    back to 7; unusable card ids become None (still loggable, settled
    by explicit grade later). Never raises.
    """
    try:
        try:
            window = int(window)
        except (TypeError, ValueError):
            window = WINDOWS[0]
        if window not in WINDOWS:
            window = WINDOWS[0]
        try:
            cid: object = int(card_id)
        except (TypeError, ValueError):
            try:
                cid = str(card_id).strip() or None
            except Exception:  # noqa: BLE001 — id must never raise
                cid = None
        return {"kind": "probe", "card_id": cid, "window": window,
                "target": None, "bettor": _str(bettor, "you"),
                "rival": _str(rival, "a friend"), "stake": STAKE,
                "status": "open", "placed_at": _str(placed_at)}
    except Exception:  # noqa: BLE001 — placement must never raise
        return {"kind": "probe", "card_id": None, "window": WINDOWS[0],
                "target": None, "bettor": "you", "rival": "a friend",
                "stake": STAKE, "status": "open", "placed_at": ""}


def place_accuracy_wager(target: float = DEFAULT_TARGET, bettor: str = "you",
                         rival: str = "a friend",
                         placed_at: str = "") -> dict:
    """Log a coffee bet that mature delayed accuracy holds ``target``.

    ``target`` is clamped to 0–1 (garbage → 0.8). Settles later via
    ``settle()`` against a northstar-style snapshot dict. Never raises.
    """
    try:
        try:
            goal = float(target)
            if goal != goal:  # NaN fails closed to the default
                goal = DEFAULT_TARGET
        except (TypeError, ValueError):
            goal = DEFAULT_TARGET
        goal = min(1.0, max(0.0, goal))
        return {"kind": "accuracy", "card_id": None, "window": None,
                "target": round(goal, 2), "bettor": _str(bettor, "you"),
                "rival": _str(rival, "a friend"), "stake": STAKE,
                "status": "open", "placed_at": _str(placed_at)}
    except Exception:  # noqa: BLE001 — placement must never raise
        return {"kind": "accuracy", "card_id": None, "window": None,
                "target": DEFAULT_TARGET, "bettor": "you",
                "rival": "a friend", "stake": STAKE,
                "status": "open", "placed_at": ""}


def wagers_from_query(query) -> list:
    """Wager dicts from /reviews query data; [] when nothing placed.

    Accepts ``?wager=probe:<card>:<window>`` / ``?wager=acc:<target>``
    specs plus the place form's discrete ``wager_kind`` /
    ``wager_card`` / ``wager_window`` / ``wager_target`` fields.
    Never raises.
    """
    out = []
    try:
        if not isinstance(query, dict):
            return []
        for spec in query.get("wager", []) or []:
            try:
                bits = str(spec).split(":")
                if bits[0] == "probe" and len(bits) >= 2:
                    # Card ids may contain colons: the window is the
                    # trailing int, everything between is the card id.
                    if len(bits) > 2:
                        try:
                            window = int(bits[-1])
                            cid = ":".join(bits[1:-1])
                        except (TypeError, ValueError):
                            window, cid = 7, ":".join(bits[1:])
                    else:
                        window, cid = 7, bits[1]
                    out.append(place_probe_wager(cid, window))
                elif bits[0] == "acc":
                    out.append(place_accuracy_wager(
                        bits[1] if len(bits) > 1 else DEFAULT_TARGET))
            except Exception:  # noqa: BLE001 -- one bad spec never breaks
                continue
        kind = (query.get("wager_kind", [""])[0]
                if isinstance(query.get("wager_kind"), list)
                else query.get("wager_kind", ""))
        if str(kind or "").strip():
            if str(kind).strip() == "accuracy":
                out.append(place_accuracy_wager(
                    (query.get("wager_target", [""])[0]
                     if isinstance(query.get("wager_target"), list)
                     else query.get("wager_target", "")) or DEFAULT_TARGET))
            else:
                card = (query.get("wager_card", [""])[0]
                        if isinstance(query.get("wager_card"), list)
                        else query.get("wager_card", ""))
                window = (query.get("wager_window", [""])[0]
                          if isinstance(query.get("wager_window"), list)
                          else query.get("wager_window", ""))
                out.append(place_probe_wager(card, window or 7))
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
            if raw is None:
                return mine
            try:
                acc = float(raw)
            except (TypeError, ValueError):
                return mine
            if acc != acc:  # NaN is not a measurement
                return mine
            try:
                goal = float(mine.get("target", DEFAULT_TARGET))
            except (TypeError, ValueError):
                goal = DEFAULT_TARGET
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
    """Compact bet placer (GET ?wager=…); always safe to render."""
    try:
        return (
            "<form class='wager-place' method='get' action='/reviews'>"
            "<label>Bet a coffee "
            "<select name='wager_kind'>"
            "<option value='probe'>probe passes</option>"
            "<option value='accuracy'>delayed accuracy holds</option>"
            "</select></label> "
            "<label>Card <input name='wager_card' size='6' "
            "placeholder='card id'></label> "
            "<label>Window <select name='wager_window'>"
            "<option value='7'>7-day</option>"
            "<option value='30'>30-day</option>"
            "</select></label> "
            "<label>Target <input name='wager_target' size='4' "
            "placeholder='0.8'></label> "
            "<button type='submit'>Bet coffee</button></form>")
    except Exception:  # noqa: BLE001 -- form must never raise
        return ""


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
    """Tour registry entry for friendly wagers; never raises."""
    try:
        return {"id": "friendly-wagers", "kind": "feature",
                "title": "Friendly wagers",
                "blurb": "Bet a coffee on your next delayed retest — probe passes win, and the History ledger keeps score.",
                "path": "/reviews", "anchor": STATUS_ANCHOR}
    except Exception:  # noqa: BLE001 — tour entry must never raise
        return {"id": "friendly-wagers", "kind": "feature",
                "title": "Friendly wagers",
                "blurb": "Bet a coffee on delayed recalls.",
                "path": "/reviews", "anchor": STATUS_ANCHOR}
