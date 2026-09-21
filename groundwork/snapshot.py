"""URL-based session share: read-only snapshot link per module (I-49).

A shareable link encodes a read-only snapshot of one module's session
state (answered / accuracy so far) that renders without login and
without leaking private data: no answer text, no journal, no review
detail — counts and accuracy only.

Token design: a JSON payload (version + expiry + allowlisted counts),
base64url-encoded and sealed with HMAC-SHA256 under a caller-supplied
secret. Anyone holding the link can read the counts; nobody can forge
or alter them without the secret. Decoding fails closed: bad
signature, expiry, malformed token, or unknown version -> None.

Pure functions, stdlib only (`base64`, `hashlib`, `hmac`, `html`,
`json`, `time`). No DB, no schema changes, no I/O, no groundwork
imports. Owns ONLY the token plus the read-only render: module-file
export stays with `share.py`, personal-data export with `exports.py`.

WIRES (parent implements; no web.py edits here): add a GET route such
as `/share/<token>` that calls `decode_snapshot(token, SECRET)` and
renders `snapshot_html()` (None -> 404); append `section_html()` to the
Batch 9 status block and `tour_entry()` to `tour.ENTRIES`.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import html
import json
import time

VERSION = 1
DEFAULT_TTL_SECONDS = 7 * 24 * 3600
MAX_TOKEN_LEN = 4096
MAX_MODULE_ID_LEN = 200
STATUS_ANCHOR = "status-b9-snapshot"

# The ONLY state fields a snapshot may carry. Everything else in the
# caller's dict (answer text, submissions, journal, reviews, cards,
# decisions, …) is dropped by sanitize_snapshot() before it can reach
# a token or the renderer.
ALLOWED_KEYS = frozenset({"module_id", "answered", "correct", "accuracy"})


def _now(now=None) -> float:
    """Injectable clock (tests pass now= explicitly); never raises."""
    if isinstance(now, bool):
        return time.time()
    if isinstance(now, (int, float)):
        return float(now)
    return time.time()


def _b64e(raw: bytes) -> str:
    """Base64url without padding (URL-safe token half)."""
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(text: str) -> bytes:
    """Inverse of _b64e; raises on malformed input (callers catch)."""
    if not isinstance(text, str) or not text:
        raise ValueError("empty segment")
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _to_int(value, default: int = 0) -> int:
    """Coerce to a non-negative int; garbage -> default, never raises."""
    try:
        if isinstance(value, bool):
            return default
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def sanitize_snapshot(state) -> dict:
    """Allowlisted snapshot dict; private fields cannot pass through.

    Keeps only module_id/answered/correct, clamps correct <= answered,
    and recomputes accuracy so a stale or inconsistent value can never
    be rendered. Non-dict input renders as an empty snapshot.
    """
    if not isinstance(state, dict):
        return {"module_id": "", "answered": 0, "correct": 0, "accuracy": 0}
    mid = state.get("module_id", "")
    mid = mid if isinstance(mid, str) else str(mid or "")
    answered = _to_int(state.get("answered", 0))
    correct = min(_to_int(state.get("correct", 0)), answered)
    accuracy = round(100 * correct / answered) if answered else 0
    return {"module_id": mid[:MAX_MODULE_ID_LEN], "answered": answered,
            "correct": correct, "accuracy": accuracy}


def encode_snapshot(state: dict, secret: str,
                    ttl_seconds: float = DEFAULT_TTL_SECONDS,
                    now=None) -> str:
    """Sign an allowlisted snapshot into a URL-safe token.

    Raises TypeError for a non-dict state, ValueError for an empty
    secret or a non-positive TTL.
    """
    if not isinstance(state, dict):
        raise TypeError("state must be a dict")
    if not isinstance(secret, str) or not secret:
        raise ValueError("secret must be a non-empty string")
    try:
        ttl = float(ttl_seconds)
    except (TypeError, ValueError):
        raise ValueError("ttl_seconds must be a number")
    if not ttl > 0:
        raise ValueError("ttl_seconds must be positive")
    payload = {"v": VERSION, "exp": int(_now(now) + ttl),
               "data": sanitize_snapshot(state)}
    raw = json.dumps(payload, sort_keys=True,
                     separators=(",", ":")).encode("utf-8")
    body = _b64e(raw)
    sig = hmac.new(secret.encode("utf-8"), body.encode("ascii"),
                   hashlib.sha256).digest()
    return body + "." + _b64e(sig)


def decode_snapshot(token, secret, now=None) -> dict | None:
    """Verify a token; fail closed -> None on any problem.

    None covers: non-str/empty token or secret, oversize token, bad
    shape, undecodable segments, signature mismatch, unknown version,
    missing/non-int expiry, and expired tokens. Never raises.
    """
    try:
        if not isinstance(token, str) or not isinstance(secret, str):
            return None
        if not token or not secret or len(token) > MAX_TOKEN_LEN:
            return None
        if token.count(".") != 1:
            return None
        body, _, sig_b64 = token.partition(".")
        body_raw = _b64d(body)
        sig = _b64d(sig_b64)
        if len(sig) != hashlib.sha256().digest_size:
            return None
        expect = hmac.new(secret.encode("utf-8"), body.encode("ascii"),
                          hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expect):
            return None
        payload = json.loads(body_raw.decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("v") != VERSION:
            return None
        exp = payload.get("exp")
        if isinstance(exp, bool) or not isinstance(exp, (int, float)):
            return None
        if float(exp) < _now(now):
            return None
        data = payload.get("data")
        if not isinstance(data, dict):
            return None
        return sanitize_snapshot(data)
    except Exception:
        return None


def snapshot_html(snapshot) -> str:
    """Read-only render: counts + accuracy only, stable id='snapshot'.

    Re-sanitizes first, so even a hand-built dict can never smuggle
    answer text, journal, or review detail into the page. Always
    renders (zeros when empty) so the tour anchor never moves.
    """
    data = sanitize_snapshot(snapshot)
    mid = html.escape(data["module_id"] or "unknown module")
    return (
        f"<div id='snapshot'><p>{mid}: {data['answered']} answered · "
        f"{data['correct']} correct · {data['accuracy']}% accuracy.</p></div>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "session-share", "kind": "improvement",
            "title": "Shareable session snapshot",
            "blurb": "A link showing one module's answered count and "
                     "accuracy — read-only, no login, no private data.",
            "path": "/status", "anchor": "status-b9-snapshot"}


def section_html() -> str:
    """Status-page subsection: visible home for this item."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Shareable session snapshot "
        "<small>(improvement)</small></h3>"
        "<p>One module's session state (answered, accuracy) packs into a "
        "signed URL token: counts render without login while answer text, "
        "journal, and review detail never leave the database — "
        "<code>decode_snapshot()</code> fails closed on forged or expired "
        "links. No DB change. <code>groundwork/snapshot.py</code>.</p>"
    )
