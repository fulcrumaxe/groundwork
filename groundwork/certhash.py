"""Offline-checkable certificate hashes (F-180).

Teaching certificates (teachcert.py) state claims; this module makes
them portable. Each fully-owned pack issues a self-describing text
block whose last line is the sha256 of its canonical claims. Any
holder verifies offline by recomputing over the pasted claims: no
server round-trip, no identity layer, no shared secret. The hash
proves the block was not altered in transit, not who wrote it --
authorship needs identities this single-learner app has no honest
source for. Pure reads over existing tables; never raises.
"""
from __future__ import annotations

import hashlib
import html

STATUS_ANCHOR = "status-b28-certhash"

VERSION = "GW-CERT/1"
FIELDS = ("pack", "summary", "owned", "total", "issued")
PARAM = "certcheck"


def _flat(value) -> str:
    """One line, single-spaced: byte-stable claim values."""
    try:
        return " ".join(str(value if value is not None else "").split())
    except Exception:  # noqa: BLE001 -- flattening must never raise
        return ""


def claims_for(cert: dict) -> dict:
    """The five hashed claims for one teachcert certificate dict."""
    try:
        if not isinstance(cert, dict):
            return {k: "" for k in FIELDS}
        return {k: _flat(cert.get(k, "")) for k in FIELDS}
    except Exception:  # noqa: BLE001 -- claims must never raise
        return {k: "" for k in FIELDS}


def canonical(claims) -> str:
    """Canonical bytes: version line + fixed-order field lines."""
    try:
        get = claims.get if isinstance(claims, dict) else (lambda k, d="": d)
        lines = [VERSION]
        lines += [f"{k}:{_flat(get(k, ''))}" for k in FIELDS]
        return "\n".join(lines) + "\n"
    except Exception:  # noqa: BLE001 -- canonical must never raise
        return VERSION + "\n"


def digest(text: str) -> str:
    """sha256 hex over the canonical bytes."""
    try:
        return hashlib.sha256(str(text).encode("utf-8")).hexdigest()
    except Exception:  # noqa: BLE001 -- digest must never raise
        return "0" * 64


def issue_block(cert: dict) -> str:
    """Portable certificate block: canonical claims + hash line."""
    try:
        body = canonical(claims_for(cert))
        return body + f"hash:{digest(body)}\n"
    except Exception:  # noqa: BLE001 -- issue must never raise
        return VERSION + "\n"


def parse_block(text) -> tuple | None:
    """(claims, hash) from a pasted block; None when not a block."""
    try:
        lines = [ln.strip() for ln in str(text or "").splitlines()
                 if ln.strip()]
        if len(lines) != len(FIELDS) + 2:
            return None
        if lines[0] != VERSION:
            return None
        claims = {}
        for key, line in zip(FIELDS, lines[1:-1]):
            name, sep, val = line.partition(":")
            if not sep or name != key:
                return None
            claims[key] = val.strip()
        name, sep, val = lines[-1].partition(":")
        if not sep or name != "hash":
            return None
        return claims, val.strip().lower()
    except Exception:  # noqa: BLE001 -- parse must never raise
        return None


def verify_block(text) -> tuple:
    """(ok, reason): recompute-over-claims; never raises."""
    try:
        parsed = parse_block(text)
        if parsed is None:
            return False, "not a certificate block"
        claims, want = parsed
        if digest(canonical(claims)) == want:
            return True, "certificate matches its hash"
        return False, "claims do not match the hash"
    except Exception:  # noqa: BLE001 -- verify must never raise
        return False, "could not check this block"


def cert_claims(db_path: str) -> list:
    """Eligible (fully-owned) packs; the only issuable certificates."""
    try:
        from . import teachcert as certmod
        return [c for c in certmod.eligible(db_path)]
    except Exception:  # noqa: BLE001 -- claims must never raise
        return []


def section_html(db_path: str, query=None) -> str:
    """Checkable blocks plus the paste-to-verify form, on History."""
    try:
        certs = cert_claims(db_path)
        if not certs:
            head = ("<p>No verifiable certificates yet -- own a whole "
                    "pack and its checkable block appears here.</p>")
        else:
            bits = []
            for c in certs:
                block = issue_block(c)
                short = digest(canonical(claims_for(c)))[:12]
                pack = html.escape(str(c.get("pack", "")))
                summ = html.escape(str(c.get("summary") or c.get("pack", "")))
                bits.append(
                    f"<p>Verifiable certificate: "
                    f"<a href='/modules/{pack}'>{summ}</a> -- "
                    f"sha256 <code>{short}</code>"
                    f"<details><summary>portable block</summary>"
                    f"<pre>{html.escape(block)}</pre></details></p>")
            head = "".join(bits)
        pasted = ""
        try:
            if isinstance(query, dict):
                vals = query.get(PARAM, []) or []
                pasted = str(vals[0]) if vals else ""
        except Exception:  # noqa: BLE001 -- hostile query keeps empty form
            pasted = ""
        verdict = ""
        if pasted.strip():
            ok, reason = verify_block(pasted)
            cls = "ok" if ok else "stale"
            verdict = (f"<p class='{cls}' id='cert-verdict'>"
                       f"{html.escape(reason)}</p>")
        form = (f"<form method='get' action='/reviews'>"
                f"<p><label for='certcheck'>Check a pasted "
                f"certificate:</label><br>"
                f"<textarea id='certcheck' name='{PARAM}' rows='8' "
                f"cols='60'>{html.escape(pasted)}</textarea><br>"
                f"<button type='submit'>Verify offline</button></p></form>")
        return (f"<h2 id='cert-hashes'>Verifiable certificates</h2>"
                f"{head}{verdict}{form}")
    except Exception:  # noqa: BLE001 -- section must never raise
        return ("<h2 id='cert-hashes'>Verifiable certificates</h2>"
                "<p>Certificate checks temporarily unavailable.</p>")


def status_section_html() -> str:
    """Anchored status subsection; joined by the Batch 28 home module."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Verifiable certificates "
            "<small>(feature)</small></h3>"
            "<p>Teaching certificates with content hashes -- "
            "<code>groundwork/certhash.py</code> freezes each fully-owned "
            "pack's claims plus a sha256 into a portable block, and "
            "?certcheck on History recomputes over pasted claims so any "
            "holder verifies offline.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Verifiable certificates</h3>"
                "<p>Certificate help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "cert-hashes",
        "kind": "feature",
        "title": "Verifiable certificates",
        "blurb": "Certificates with hashes any holder can check offline.",
        "path": "/reviews",
        "anchor": "cert-hashes",
    }
