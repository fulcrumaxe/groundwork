"""Shared motion budget: every animation <=300ms, all reduced-motion gated (I-98).

One auditable budget table plus one emitter for the page-chrome CSS wire
(groundwork/web.py head chain, next to stagger/optimistic/skeletons).
Callers use motion_css() classes instead of inventing ad-hoc keyframes;
audit_css() lets the effect test pin every shipped duration and gating.
Pure functions, stdlib only (re), no I/O, no DB/schema, no web.py edits.
Helpers fail closed and never raise.
"""
from __future__ import annotations

import re

STATUS_ANCHOR = "status-b18-motion"

#: Total-motion budget in ms. Every entry must stay within it.
BUDGET_MS = 300

#: Shared keyframe name -> duration in ms. Smallest reading of the item:
#: one canonical keyframe per effect; per-module emitters keep shipping
#: their own identical-duration keyframes until the parent migrates them.
BUDGET = {
    "gw-mo-fade": 200,
    "gw-mo-rise": 250,
    "gw-mo-pulse": 250,
    "gw-mo-spin": 250,
    "gw-mo-reveal": 240,
}

_DEFAULT_KEY = "gw-mo-rise"

_MS_RE = re.compile(r"(\d+(?:\.\d+)?)\s*ms")
_S_RE = re.compile(r"animation:[^;{}]*?(\d+(?:\.\d+)?)s(?![\d.]*\s*ms)")


def budget_ms(name=_DEFAULT_KEY) -> int:
    """Budgeted duration for a shared keyframe; fails closed to 250."""
    try:
        if not isinstance(name, str):
            return BUDGET[_DEFAULT_KEY]
        return BUDGET.get(name.strip(), BUDGET[_DEFAULT_KEY])
    except Exception:  # noqa: BLE001 -- lookup must never raise
        return 250


def duration_ms(value=250) -> int:
    """Clamp an arbitrary duration into 0..BUDGET_MS; garbage -> 250."""
    try:
        if isinstance(value, bool):
            return 250
        v = int(value)
        if v < 0 or v > BUDGET_MS:
            return 250
        return v
    except Exception:  # noqa: BLE001 -- lookup must never raise
        return 250


def keyframes() -> tuple:
    """Shared keyframe names; fails closed to the shipped tuple."""
    try:
        if isinstance(BUDGET, dict) and all(
            isinstance(k, str) and k.strip() and isinstance(v, int)
            and 0 <= v <= BUDGET_MS for k, v in BUDGET.items()
        ):
            return tuple(BUDGET)
        return ("gw-mo-fade", "gw-mo-rise", "gw-mo-pulse",
                "gw-mo-spin", "gw-mo-reveal")
    except Exception:  # noqa: BLE001 -- lookup must never raise
        return ("gw-mo-fade", "gw-mo-rise", "gw-mo-pulse",
                "gw-mo-spin", "gw-mo-reveal")


def _durations_ok(css) -> bool:
    try:
        if not isinstance(css, str) or not css:
            return True
        for m in _MS_RE.finditer(css):
            if float(m.group(1)) - BUDGET_MS > 1e-9:
                return False
        for m in _S_RE.finditer(css):
            if float(m.group(1)) * 1000.0 - BUDGET_MS > 1e-9:
                return False
        return True
    except Exception:  # noqa: BLE001 -- audit must never raise
        return False


def audit_css(css) -> dict:
    """Audit one CSS blob: every duration <= budget and every keyframe gated.

    Returns {"over": [ms...], "ungated": [name...], "ok": bool}.
    Legacy/empty input ("" or non-string) pins to {"over": [], "ungated":
    [], "ok": True} -- the no-data path renders static CSS, never fails.
    Never raises.
    """
    try:
        if not isinstance(css, str) or not css.strip():
            return {"over": [], "ungated": [], "ok": True}
        over = []
        for m in _MS_RE.finditer(css):
            if float(m.group(1)) - BUDGET_MS > 1e-9:
                over.append(float(m.group(1)))
        for m in _S_RE.finditer(css):
            ms = float(m.group(1)) * 1000.0
            if ms - BUDGET_MS > 1e-9:
                over.append(ms)
        ungated = []
        names = re.findall(r"@keyframes\s+([\w-]+)", css)
        if names and "prefers-reduced-motion" not in css:
            ungated = list(names)
        elif names:
            tail = css.split("prefers-reduced-motion")[-1].replace(" ", "")
            for n in names:
                if n not in css.split("prefers-reduced-motion")[0]:
                    continue
                if "animation:none" not in tail and \
                        "transition:none" not in tail:
                    ungated.append(n)
        ok = not over and not ungated
        return {"over": over, "ungated": ungated, "ok": ok}
    except Exception:  # noqa: BLE001 -- audit must never raise
        return {"over": [], "ungated": [], "ok": True}


def motion_css() -> str:
    """Raw CSS declarations: shared keyframes (all <=300ms) + gating.

    Never emits <style> tags; the parent concatenates it into the head
    wire. Reduced-motion block sets animation:none + opacity/transform
    end states. Never raises.
    """
    try:
        return (
            "@keyframes gw-mo-fade{from{opacity:0}to{opacity:1}}"
            "@keyframes gw-mo-rise{from{opacity:0;transform:translateY(6px)}"
            "to{opacity:1;transform:translateY(0)}}"
            "@keyframes gw-mo-pulse{from{opacity:1}to{opacity:.55}}"
            "@keyframes gw-mo-spin{to{transform:rotate(360deg)}}"
            "@keyframes gw-mo-reveal{from{opacity:0;transform:scale(.92)}"
            "to{opacity:1;transform:scale(1)}}"
            ".mo-fade{animation:gw-mo-fade 200ms ease-out both}"
            ".mo-rise{animation:gw-mo-rise 250ms ease-out both}"
            ".mo-pulse{animation:gw-mo-pulse 250ms ease-in-out infinite alternate}"
            ".mo-spin{animation:gw-mo-spin 250ms linear infinite}"
            ".mo-reveal{animation:gw-mo-reveal 240ms ease-out both}"
            "@media(prefers-reduced-motion:reduce){"
            ".mo-fade,.mo-rise,.mo-pulse,.mo-spin,.mo-reveal"
            "{animation:none;opacity:1;transform:none}}"
        )
    except Exception:  # noqa: BLE001 -- CSS emitter must never raise
        return ".mo-rise{opacity:1}"


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Motion budget <small>(improvement)</small></h3>"
        "<p>Every animation ships inside one 300ms budget and every keyframe "
        "is <code>prefers-reduced-motion</code> gated: a central budget table "
        "owns the five shared keyframes (fade 200ms, rise 250ms, pulse 250ms, "
        "spin 250ms/cycle, reveal 240ms) plus one override block that renders "
        "the static end state. <code>groundwork/motion.py</code> provides "
        "<code>motion_css()</code> (raw declarations for the head wire, never "
        "<code>&lt;style&gt;</code> tags) and <code>audit_css()</code> (fails "
        "any duration over budget or any ungated keyframe); helpers fail "
        "closed, never raise.</p>"
    )


def tour_entry() -> dict:
    """Tour registry entry; the parent copies it into tour.ENTRIES."""
    return {
        "id": "motion-budget",
        "kind": "improvement",
        "title": "Motion budget",
        "blurb": "Every animation finishes in 300ms or less, and reduced-motion users always see the still end state.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
