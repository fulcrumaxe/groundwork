"""Card-facing renderers: answer widgets, meters, hints, forecasts.

Pure HTML builders over card dicts — no HTTP, no page chrome.
The web Handler calls these so card UI never lives in web.py.
"""
from __future__ import annotations

import html
import json

from . import confslider as confslidermod
from . import hinttiers as hinttiersmod
from . import parsons as parsonsmod


def _payload(card) -> dict:
    raw = card.get("payload", "{}") if isinstance(card, dict) else card["payload"]
    try:
        return json.loads(raw or "{}")
    except ValueError:
        return {}


def _confidence(extra: str = "") -> str:
    # Segmented control (I-64): same posted field, tappable segments.
    # Explicit drill odds ride along (Batch 15, F-66): every stated
    # confidence shows its price before the answer is graded.
    return confslidermod.slider_html(3, extra=extra) + " " + confslidermod.odds_html()


PARSONS_JS = """
<script>
if (!window.__parsonsInit) { window.__parsonsInit = true;
function parsonsSync(ol) {
  var ids = Array.prototype.map.call(
    ol.querySelectorAll('li'), function (li) { return li.getAttribute('data-i'); });
  document.getElementById('po-' + ol.id.slice(3)).value = ids.join(' ');
}
document.addEventListener('DOMContentLoaded', function () {
  Array.prototype.forEach.call(document.querySelectorAll('ol.parsons'), function (ol) {
    var dragged = null;
    parsonsSync(ol);
    ol.addEventListener('dragstart', function (e) {
      dragged = e.target.closest('li'); e.dataTransfer.effectAllowed = 'move';
    });
    ol.addEventListener('dragover', function (e) {
      e.preventDefault();
      var li = e.target.closest('li');
      if (li && li !== dragged) {
        var r = li.getBoundingClientRect();
        var after = (e.clientY - r.top) > r.height / 2;
        ol.insertBefore(dragged, after ? li.nextSibling : li);
      }
    });
    ol.addEventListener('drop', function (e) { e.preventDefault(); parsonsSync(ol); });
    ol.addEventListener('click', function (e) {
      var b = e.target.closest('button[data-move]'); if (!b) return;
      var li = b.closest('li'); var d = parseInt(b.getAttribute('data-move'), 10);
      if (d < 0 && li.previousElementSibling) ol.insertBefore(li, li.previousElementSibling);
      if (d > 0 && li.nextElementSibling) ol.insertBefore(li.nextElementSibling, li);
      parsonsSync(ol);
    });
  });
});
}
</script>"""


def hints_html(card, attempts: int = 0) -> str:
    """Progressive hint reveal (adaptive scaffolding): the nudge is always
    visible; each further attempt unlocks the next tier.

    Tiers render visually distinct (I-63) via hinttiers.hints_html,
    which keeps the same 1+attempts prefix semantics.
    """
    hints = _payload(card).get("hints", [])
    return hinttiersmod.hints_html(hints, attempts)


def answer_widget(card, attempts: int = 0, origin: str = "/") -> str:
    """Interaction matched to the exercise type — never just answer+submit.

    `origin` records the page the card was answered from so the result
    screen can link back to it (navigation contract: never strand).
    """
    cid = card["id"]
    etype = str(card["exercise_type"] if isinstance(card, dict)
                else card["exercise_type"])
    p = _payload(card)
    open_form = (f"<form method='post' action='/cards/{cid}/review'>"
                 f"<input type='hidden' name='origin' value='{html.escape(origin, quote=True)}'>")
    if etype == "1":
        opts = "".join(f"<option value='{i}'>{i} — {w}</option>"
                       for i, w in enumerate(
                           ["blank", "wrong", "shaky", "close", "right", "easy"]))
        body = (f"<label>Say it back in your own words first "
                f"(optional, this is the recall):<br>"
                f"<textarea name='recall' rows='3' cols='60'></textarea></label><br>"
                f"<label>Then rate how well you recalled it: "
                f"<select name='answer'>{opts}</select></label> "
                f"{_confidence()}<button>Submit rating</button>")
    elif etype == "2":
        blanks = p.get("blanks") or [{"id": 0, "answers": p.get("answers", [])}]
        fields = " ".join(
            f"<label>___({b['id']}) <input name='b{b['id']}' size='12'></label>"
            for b in blanks)
        body = f"{fields} {_confidence()}<button>Check blanks</button>"
    elif etype in ("4", "7", "16", "18"):
        btns = " ".join(
            f"<button name='answer' value='{html.escape(c)}'>{html.escape(c)}</button>"
            for c in p.get("choices", []))
        body = f"{btns} {_confidence()}"
    elif etype in ("5", "6", "21", "22", "24", "25"):
        hint = ("First line: A or B, then your reasons."
                if etype == "22" else "Explain in your own words…")
        body = (f"<textarea name='answer' rows='5' cols='70' "
                f"placeholder='{hint}'></textarea><br>"
                f"{_confidence()}<button>Submit explanation</button>")
    elif etype == "8":
        if p.get("choices"):
            btns = " ".join(
                f"<button name='answer' value='{html.escape(c)}'>{html.escape(c)}</button>"
                for c in p["choices"])
            body = (f"<p>Pick the output — or type it from memory when these feel easy:</p>"
                    f"{btns}<br>"
                    f"<label>Type it: <input name='answer' size='20'></label> "
                    f"{_confidence()}<button>Check</button>")
        else:
            body = (f"<label>It prints/returns: <input name='answer' size='30'></label> "
                    f"{_confidence()}<button>Check prediction</button>")
    elif etype == "3" and p.get("choices"):
        btns = " ".join(
            f"<button name='answer' value='{html.escape(c)}'>{html.escape(c)}</button>"
            for c in p["choices"])
        body = (f"<p>Pick the signature — or write it from memory when these feel easy:</p>"
                f"{btns}<br>"
                f"<label>Write it: <input name='answer' size='40'></label> "
                f"{_confidence()}<button>Check</button>")
    elif etype == "30":
        left = p.get("left", [])
        right = p.get("right", [])
        letters = " ".join(f"<b>{chr(ord('A') + i)}</b> {html.escape(b)}"
                           for i, b in enumerate(right))
        rows = "".join(
            f"<tr><td><b>{i}</b> {html.escape(a)}</td>"
            f"<td><input name='m{i}' size='3' placeholder='letter'></td></tr>"
            for i, a in enumerate(left))
        body = (f"<p>{letters}</p><table>{rows}</table>"
                f"{_confidence()}<button>Check matches</button>")
    elif etype == "9":
        steps = p.get("expected", [])
        rows = "".join(
            f"<tr><td>Step {i + 1}</td>"
            f"<td><input name='s{i}' size='12'></td></tr>"
            for i in range(len(steps))) or \
            "<tr><td>Value</td><td><input name='s0' size='12'></td></tr>"
        body = (f"<table>{rows}</table>{_confidence()}"
                f"<button>Check trace</button>")
    elif etype in ("10", "11"):
        body = (parsonsmod.block_html(cid, p.get("lines", []))
                + f"{_confidence()}<button>Check order</button>{PARSONS_JS}")
    elif etype in ("12", "14", "19", "20", "23"):
        body = (f"<textarea name='answer' rows='12' cols='70' "
                f"placeholder='Write your code here'></textarea><br>"
                f"{_confidence()}<button>Run tests</button>")
    elif etype == "13":
        opts = "".join(
            f"<label><input type='radio' name='answer' value='{i + 1}'> "
            f"{html.escape(l)}</label><br>"
            for i, l in enumerate(p.get("snippet", "").splitlines()))
        body = f"{opts}{_confidence()}<button>Accuse this line</button>"
    else:
        body = (f"<input name='answer' size='50' placeholder='Your answer'> "
                f"{_confidence()}<button>Submit</button>")
    giveup = (f"<form method='post' action='/cards/{cid}/review'>"
              f"<input type='hidden' name='answer' value=''>"
              f"<input type='hidden' name='confidence' value='1'>"
              f"<input type='hidden' name='origin' value='{html.escape(origin, quote=True)}'>"
              f"<button class='giveup'>Give up — show me the answer</button></form>")
    from . import grading as gradingmod
    how = gradingmod.disclosure_html(etype)
    from . import disputes as dismod
    dispute = dismod.dispute_form_html(card["id"], origin)
    return (f"{open_form}{body}</form>" + hints_html(card, attempts)
            + how + dispute + giveup)


def _difficulty_dots(difficulty, extra: str = "") -> str:
    """5-dot difficulty meter from the FSRS difficulty estimate."""
    try:
        n = int(round(float(difficulty if difficulty is not None else 0.5) * 5))
    except (TypeError, ValueError):
        n = 3
    n = max(1, min(5, n))
    return (f"<small{extra} title='Difficulty {n}/5'>"
            f"{'●' * n}{'○' * (5 - n)}</small>")


def _memory_bar(card, extra: str = "") -> str:
    """Memory-strength bar from the FSRS stability estimate (I-76)."""
    get = card.get if isinstance(card, dict) else lambda k: card[k]
    try:
        stab = float(get("stability") or 0.0)
    except (TypeError, ValueError):
        return ""
    try:
        retr = float(get("retrievability") or 0.0)
    except (TypeError, ValueError):
        retr = 0.0
    pct = int(round(max(0.0, min(1.0, retr if retr > 0 else stab / 30.0)) * 100))
    return (f"<p{extra}><small>Memory strength {stab:.1f}d</small>"
            f"<span class='bar' aria-hidden='true'>"
            f"<i style='width:{pct}%'></i></span></p>")


def _due_why(card, extra: str = "") -> str:
    """Scheduler explainability: why is this card due today?"""
    get = card.get if isinstance(card, dict) else lambda k: card[k]
    try:
        from . import sched as schedmod
        due = schedmod.parse_iso(str(get("due") or ""))
        days = (schedmod.utcnow() - due).days
        when = "due today" if days <= 0 else f"{days}d overdue"
    except Exception:  # noqa: BLE001 — bad date still renders
        when = "due now"
    try:
        stab = float(get("stability") or 0.0)
    except (TypeError, ValueError):
        stab = 0.0
    lapses = get("lapses") or 0
    tip = (f"{when}; memory strength {stab:.1f} days; "
           f"lapses {lapses}")
    return (f" <small><span{extra} title='{html.escape(tip)}'>"
            f"why due?</span></small>")


_WEEK_SECS = 7 * 86400


def _rel_time(iso_ts: str) -> str:
    """Relative time with exact timestamp on hover (I-25, I-26, I-93).

    Renders `<time datetime>` so dates read as "3h ago" but keep their
    exact, timezone-explicit value one hover away.
    """
    raw = iso_ts or ""
    try:
        from . import sched as schedmod
        stamp = schedmod.parse_iso(raw)
        delta = schedmod.utcnow() - stamp
        secs = int(delta.total_seconds())
        if secs < 0:
            rel = "in the future"
        elif secs < 90:
            rel = "just now"
        elif secs < 5400:
            rel = f"{secs // 60}m ago"
        elif secs < 129600:
            rel = f"{secs // 3600}h ago"
        elif secs < _WEEK_SECS:
            rel = f"{secs // 86400}d ago"
        else:
            rel = raw[:10]
    except Exception:  # noqa: BLE001 — bad date still renders
        rel = raw[:10] or "unknown"
    return (f"<time datetime='{html.escape(raw)}' title='{html.escape(raw)}'>"
            f"{html.escape(rel)}</time>")


def status_chip(card, attempts: int = 0, extra: str = "") -> str:
    """Due vs overdue vs new, at a glance (I-219)."""
    get = card.get if isinstance(card, dict) else lambda k: card[k]
    if not attempts:
        return f"<span class='chip'{extra}>new</span>"
    try:
        from . import sched as schedmod
        due = schedmod.parse_iso(str(get("due") or ""))
        days = (schedmod.utcnow() - due).days
    except Exception:  # noqa: BLE001 — bad date still renders
        return f"<span class='chip'{extra}>due</span>"
    if days >= 1:
        return f"<span class='chip stale'{extra}>{days}d overdue</span>"
    return f"<span class='chip'{extra}>due</span>"


def bloom_chip(card) -> str:
    """Bloom-tier chip for a due card header (I-56).

    Looks up the card's exercise type in the exercise registry and
    renders the shared bloomchips hook; unknown/missing types render
    nothing so a bad row can never break the queue. Never raises.
    """
    try:
        from . import bloomchips as bloomchipsmod
        from . import exercises as exmod
        get = card.get if isinstance(card, dict) else lambda k: card[k]
        tier = exmod.TYPES[int(get("exercise_type") or 0)][1]
        if not tier or not isinstance(tier, str):
            return ""
        return bloomchipsmod.chip_html(tier)
    except Exception:  # noqa: BLE001 — chips must never break cards
        return ""


def forecast_html(card, extra: str = "") -> str:
    """Next-gap forecast at steady passes, from stability (I-203)."""
    from . import sched as schedmod
    get = card.get if isinstance(card, dict) else lambda k: card[k]
    try:
        stab = float(get("stability") or 0.0)
    except (TypeError, ValueError):
        return ""
    gap = schedmod.forecast_gap(stab)
    return (f"<p{extra}><small>Forecast: steady passes "
            f"stretch the next gap to {html.escape(gap)}</small></p>")
