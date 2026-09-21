"""Desirable-difficulty dial: learner-tunable challenge level (F-55).

One knob, levels 1..5 ("gentle".."spicy"), mapping onto the
sched.py stability vocabulary: ``retrievability_floor`` is the
minimum sched R a review card must hold to stay in the queue, and
``new_cards`` caps how many never-attempted cards join the mix.
Level 1 keeps R high and new cards to one (recall/explain only);
level 5 drops the floor and adds new cards (analyse..create enter).
The parent applies it without new storage: filter the due list with
``sched.elapsed_retrievability``/``retrievability`` against the floor,
then cap new cards (minisession ``_is_new`` sense) before calling
``minisession.pick_cards`` for the 5-minute fill. Pure functions,
stdlib only, no groundwork imports, no DB/schema, never raises.
"""
from __future__ import annotations

import html as htmlmod

STATUS_ANCHOR = "status-b12-diffdial"

LEVELS = (1, 2, 3, 4, 5)

DEFAULT_LEVEL = 3

LABELS = {
    1: "gentle",
    2: "steady",
    3: "balanced",
    4: "bold",
    5: "spicy",
}

# Minimum sched retrievability R kept in the queue per level: higher
# levels tolerate more-forgotten (harder) cards. Monotonic decreasing.
FLOORS = {
    1: 0.9,
    2: 0.8,
    3: 0.7,
    4: 0.6,
    5: 0.5,
}

# New-card cap per level feeding the minisession mix. Monotonic
# increasing so harder dials never shrink the intake.
NEW_CARDS = {
    1: 1,
    2: 2,
    3: 3,
    4: 5,
    5: 7,
}

# Bloom tier emphasis per level (bloomchips.py vocabulary, local copy
# — no groundwork imports allowed).
TIER_FOCUS = {
    1: ("recall", "explain"),
    2: ("recall", "explain", "apply"),
    3: ("explain", "apply", "analyse"),
    4: ("apply", "analyse", "modify", "evaluate"),
    5: ("analyse", "modify", "evaluate", "create"),
}


def normalize_level(value) -> int:
    """Clamp a dial setting to 1..5; garbage fails closed to 3."""
    try:
        if isinstance(value, bool):
            return DEFAULT_LEVEL
        num = int(value)
        if num < 1 or num > 5:
            return DEFAULT_LEVEL
        return num
    except (TypeError, ValueError):
        return DEFAULT_LEVEL
    except Exception:  # noqa: BLE001 — coercion must never raise
        return DEFAULT_LEVEL


def dial_params(level) -> dict:
    """Params for one dial level: floor, new-card cap, label.

    Garbage or out-of-range input fails closed to the level 3
    defaults; never raises; returns a fresh dict each call.
    """
    try:
        lv = normalize_level(level)
        return {
            "level": lv,
            "retrievability_floor": float(FLOORS[lv]),
            "new_cards": int(NEW_CARDS[lv]),
            "label": str(LABELS[lv]),
        }
    except Exception:  # noqa: BLE001 — params must never raise
        return {
            "level": DEFAULT_LEVEL,
            "retrievability_floor": float(FLOORS[DEFAULT_LEVEL]),
            "new_cards": int(NEW_CARDS[DEFAULT_LEVEL]),
            "label": str(LABELS[DEFAULT_LEVEL]),
        }


def describe(params) -> str:
    """One-line effect text for a params dict, naming Bloom tiers.

    Unknown or hostile input describes the level 3 defaults; never
    raises.
    """
    try:
        if not isinstance(params, dict):
            params = dial_params(DEFAULT_LEVEL)
            lv = DEFAULT_LEVEL
        else:
            base = dial_params(DEFAULT_LEVEL)
            raw_level = params.get("level", None)
            if (isinstance(raw_level, int) and not isinstance(raw_level, bool)
                    and raw_level in LEVELS):
                lv = raw_level
                base = dial_params(lv)
            else:
                # No trustworthy level: match the triple back to a known
                # level so the tier line stays honest; else level 3.
                lv = DEFAULT_LEVEL
                for cand in LEVELS:
                    known = dial_params(cand)
                    try:
                        if (float(params.get("retrievability_floor", float("nan")))
                                == known["retrievability_floor"]
                                and int(params.get("new_cards", -1))
                                == known["new_cards"]
                                and str(params.get("label", ""))
                                == known["label"]):
                            lv = cand
                            break
                    except (TypeError, ValueError):
                        continue
                base = dial_params(lv)
            try:
                floor = float(params.get("retrievability_floor",
                                         base["retrievability_floor"]))
                if not 0.0 < floor <= 1.0:
                    floor = base["retrievability_floor"]
            except (TypeError, ValueError):
                floor = base["retrievability_floor"]
            try:
                new = int(params.get("new_cards", base["new_cards"]))
                if new < 0:
                    new = base["new_cards"]
            except (TypeError, ValueError):
                new = base["new_cards"]
            label = params.get("label", base["label"])
            if not isinstance(label, str) or not label.strip():
                label = base["label"]
            params = {"retrievability_floor": floor,
                      "new_cards": new, "label": label.strip()}
        tiers = ", ".join(TIER_FOCUS[lv])
        noun = "card" if params["new_cards"] == 1 else "cards"
        return (
            f"{params['label'].capitalize()} (level {lv}): reviews cards "
            f"at R>={params['retrievability_floor']:.2f} with up to "
            f"{params['new_cards']} new {noun} per session "
            f"— leans on {tiers}."
        )
    except Exception:  # noqa: BLE001 — describe must never raise
        tiers = ", ".join(TIER_FOCUS[DEFAULT_LEVEL])
        return (
            "Balanced (level 3): reviews cards at R>=0.70 with up to "
            f"3 new cards per session — leans on {tiers}."
        )


def tour_entry() -> dict:
    """Tour registry entry for the difficulty dial."""
    return {
        "id": "difficulty-dial",
        "kind": "feature",
        "title": "Difficulty dial",
        "blurb": ("Tune challenge 1-5 from gentle to spicy — "
                  "sets how forgotten review cards may be and how many "
                  "new cards join each short session."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        rows = " ".join(
            f"<li><b>{lv} {htmlmod.escape(LABELS[lv])}</b>: "
            f"R>={FLOORS[lv]:.2f}, "
            f"{NEW_CARDS[lv]} new</li>"
            for lv in LEVELS)
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Difficulty dial "
            "<small>(feature)</small></h3>"
            "<p>Turn challenge 1-5 from gentle to spicy: the floor "
            "is the minimum sched retrievability R a review keeps "
            "(lower floors admit harder, more-forgotten cards), and the "
            "cap is how many new cards join the 5-minute mix. "
            f"{htmlmod.escape(describe(dial_params(3)))} "
            "<code>groundwork/diffdial.py</code> provides "
            "<code>dial_params()</code> (clamped, fails closed to level 3, "
            "never raises) and <code>describe()</code> (one-line effect "
            "text in Bloom-tier terms). The parent filters the due list "
            "on the floor and caps new cards before "
            "<code>minisession.pick_cards()</code>.</p>"
            f"<ul>{rows}</ul>"
        )
    except Exception:  # noqa: BLE001 — status must always render
        return f"<h3 id='{STATUS_ANCHOR}'>Difficulty dial</h3>"
