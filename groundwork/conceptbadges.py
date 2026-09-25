"""Collectible concept badges, deterministic art per idea (F-113).

Each owned concept earns its own emblem: motif plus hue derived
from sha256(name), so badges are stable across renders and
sessions. No rarity tiers anywhere by design — every badge is
equal, collecting is proof, not pressure. Unowned concepts render
the plain chip markup byte-identical (legacy fallback); hostile
input fails closed to the plain chip. Pure functions, stdlib
html + hashlib only; never raises.
"""
from __future__ import annotations

import hashlib
import html

STATUS_ANCHOR = "status-b23-conceptbadges"

MOTIFS = ("circle", "square", "diamond", "hexagon",
          "triangle", "star", "drop", "bars")
HUES = tuple(range(0, 360, 30))


def badge_for(concept) -> dict:
    """{motif, hue, label} for a concept; fail-closed defaults."""
    try:
        name = str(concept or "concept")
    except Exception:  # noqa: BLE001 -- badges must never raise
        name = "concept"
    try:
        digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
        motif = MOTIFS[int(digest[:8], 16) % len(MOTIFS)]
        hue = HUES[int(digest[8:16], 16) % len(HUES)]
    except Exception:  # noqa: BLE001 -- badges must never raise
        motif, hue = MOTIFS[0], HUES[0]
    return {"motif": motif, "hue": hue, "label": name}


def badge_html(concept, owned: bool = False) -> str:
    """Emblem span when owned, "" otherwise (chip_link owns the chip)."""
    try:
        if not owned:
            return ""
        spec = badge_for(concept)
        label = html.escape(spec["label"])
        return (
            f"<span class='cbadge cbadge-{spec['motif']}' "
            f"style='--cb-hue:{spec['hue']}'>{label}</span>")
    except Exception:  # noqa: BLE001 -- badge must never raise
        return ""


def badge_css() -> str:
    """Raw declarations; parent concats into the head wire."""
    try:
        return (".cbadge{display:inline-block;margin-left:.3em;"
                "padding:.05em .5em;border-radius:999px;"
                "border:1px solid hsl(var(--cb-hue,210),40%,55%);"
                "background:hsl(var(--cb-hue,210),60%,95%);}"
                "@media(prefers-reduced-motion:reduce){.cbadge{border-style:dashed}}")
    except Exception:  # noqa: BLE001 -- CSS emitter must never raise
        return ".cbadge{display:inline-block}"


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = badge_html("loops", True)
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Collectible concept badges "
            "<small>(feature)</small></h3>"
            "<p>Every owned concept earns its emblem — "
            "<code>groundwork/conceptbadges.py</code> derives motif "
            "plus hue from the concept name (deterministic, equal "
            "badges, no rarity): "
            f"{sample}</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Collectible concept badges</h3>"
                "<p>Badge help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "concept-badges",
        "kind": "feature",
        "title": "Collectible concept badges",
        "blurb": ("Each owned concept earns its own deterministic art "
                  "badge — equal badges, no rarity."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
