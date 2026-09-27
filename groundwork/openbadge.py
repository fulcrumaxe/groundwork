"""Portable Open Badges 3.0 assertions for teaching certificates (F-181).

Every fully-owned pack (see teachcert.eligible) earns a standards-shaped
Open Badges 3.0 credential: one Assertion per pack, one BadgeClass
(Achievement) per pack, one Issuer for this Groundwork library. Served
on the History page as copyable JSON plus a per-pack download link --
no new route, no schema change, no PII.

Recipient: this app has no accounts, so no email or DID exists to name.
The recipient id is a hash-only pseudonym ("urn:sha256:" + the sha256
of a fixed local-learner label), identical for every assertion from
this library. Nothing identifying ever leaves the database.

Verification is hosted recomputation: verify_assertion rebuilds the
expected fields from the live owned-proofs and compares, so any edit
to the name, date, evidence, or recipient fails. Pure reads over
existing tables; never raises.
"""
from __future__ import annotations

import hashlib
import html
import json
from urllib.parse import quote

STATUS_ANCHOR = "status-b28-openbadge"

OB_CONTEXT = [
    "https://www.w3.org/ns/credentials/v2",
    "https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json",
]

ISSUER_ID = "urn:groundwork:issuer"
ISSUER_NAME = "Groundwork Library"
RECIPIENT_LABEL = "groundwork-local-learner:v1"
CLASS_PREFIX = "urn:groundwork:badgeclass:"


def recipient_id() -> str:
    """Hash-only pseudonymous recipient id; no identity exists to name."""
    digest = hashlib.sha256(RECIPIENT_LABEL.encode("utf-8")).hexdigest()
    return "urn:sha256:" + digest


def issuer() -> dict:
    """The awarding issuer: this Groundwork library."""
    return {"id": ISSUER_ID, "type": "Profile", "name": ISSUER_NAME}


def badge_class(cert: dict) -> dict:
    """BadgeClass (Achievement) for one eligible pack certificate."""
    try:
        pack = str(cert.get("pack", "pack") or "pack")
        name = str(cert.get("summary", pack) or pack)
        total = int(cert.get("total", 0) or 0)
    except (TypeError, ValueError, AttributeError):
        pack, name, total = "pack", "pack", 0
    return {
        "id": CLASS_PREFIX + pack,
        "type": "Achievement",
        "name": name,
        "description": ("Own all %d concepts in this pack well enough "
                        "to teach them." % total),
        "criteria": {"narrative": ("Two passing reviews per concept; "
                                    "issued on the last concept owned.")},
        "issuer": issuer(),
    }


def evidence(db_path: str, pack: str) -> list:
    """Owned proofs for one pack: concept ids plus owned dates."""
    try:
        from . import db as dbmod
        from . import milestones as milesmod
        owned = milesmod.owned_dates(db_path)
        con = dbmod.connect(db_path)
        try:
            rows = con.execute(
                "SELECT id FROM concepts WHERE module_id=?",
                (pack,)).fetchall()
        finally:
            con.close()
        return [{"id": str(r["id"]), "ownedOn": owned[str(r["id"])]}
                for r in rows if str(r["id"]) in owned]
    except Exception:  # noqa: BLE001 -- evidence must never raise
        return []


def assertion_for(cert: dict, db_path: str) -> dict:
    """Open Badge 3.0 assertion over one eligible pack certificate."""
    try:
        pack = str(cert.get("pack", "pack") or "pack")
        issued = str(cert.get("issued", "") or "")
    except (TypeError, ValueError, AttributeError):
        pack, issued = "pack", ""
    return {
        "@context": list(OB_CONTEXT),
        "id": "urn:groundwork:assertion:%s:%s" % (pack, issued[:10]),
        "type": ["VerifiableCredential", "OpenBadgeCredential"],
        "issuer": issuer(),
        "validFrom": issued,
        "credentialSubject": {
            "id": recipient_id(),
            "type": "AchievementSubject",
            "achievement": badge_class(cert),
        },
        "evidence": evidence(db_path, pack),
    }


def assertions(db_path: str) -> list:
    """One assertion per eligible (fully-owned) pack; [] when none."""
    try:
        from . import teachcert as certmod
        return [assertion_for(c, db_path)
                for c in certmod.eligible(db_path)]
    except Exception:  # noqa: BLE001 -- assertions must never raise
        return []


def assertion_json(pack: str, db_path: str) -> str:
    """Canonical assertion JSON for one pack; "" when not eligible."""
    try:
        want = CLASS_PREFIX + str(pack)
        for a in assertions(db_path):
            ach = ((a.get("credentialSubject") or {}).get("achievement")
                   or {})
            if ach.get("id") == want:
                return json.dumps(a, sort_keys=True, indent=2)
        return ""
    except Exception:  # noqa: BLE001 -- export must never raise
        return ""


def _pack_of(obj: dict) -> str:
    try:
        ach = ((obj.get("credentialSubject") or {}).get("achievement")
               or {})
        aid = str(ach.get("id", "") or "")
        if aid.startswith(CLASS_PREFIX):
            return aid[len(CLASS_PREFIX):]
    except (TypeError, AttributeError):
        pass
    return ""


def _norm(items) -> list:
    try:
        return sorted((str(e.get("id")), str(e.get("ownedOn")))
                      for e in items
                      if isinstance(e, dict))
    except (TypeError, AttributeError):
        return []


def verify_assertion(obj, db_path: str) -> bool:
    """True when the assertion matches live owned-proofs exactly.

    Hosted verification by recomputation: the pack must still be
    fully owned, and the recipient, name, date, and evidence must
    equal what the live database says. Anything else fails.
    """
    try:
        if not isinstance(obj, dict):
            return False
        if "OpenBadgeCredential" not in (obj.get("type") or []):
            return False
        subj = obj.get("credentialSubject") or {}
        if not isinstance(subj, dict) or subj.get("id") != recipient_id():
            return False
        pack = _pack_of(obj)
        if not pack:
            return False
        from . import teachcert as certmod
        certs = {str(c["pack"]): c for c in certmod.eligible(db_path)}
        cert = certs.get(pack)
        if cert is None:
            return False
        ach = subj.get("achievement") or {}
        if ach.get("name") != str(cert.get("summary") or pack):
            return False
        if obj.get("validFrom") != str(cert.get("issued") or ""):
            return False
        want = _norm(evidence(db_path, pack))
        if not want or _norm(obj.get("evidence")) != want:
            return False
        return True
    except Exception:  # noqa: BLE001 -- verification fails closed
        return False


def section_html(db_path: str) -> str:
    """Badge assertions on History; "" keeps legacy pages byte-identical."""
    try:
        items = assertions(db_path)
        if not items:
            return ""
        bits = []
        for a in items:
            ach = ((a.get("credentialSubject") or {}).get("achievement")
                   or {})
            pack = str(ach.get("id", "") or "")[len(CLASS_PREFIX):]
            safe = html.escape(pack)
            name = html.escape(str(ach.get("name", pack) or pack))
            blob = json.dumps(a, sort_keys=True, indent=2)
            href = "data:application/json," + quote(blob, safe="")
            bits.append(
                f"<details id='open-badge-{safe}'>"
                f"<summary>Open Badge: {name} "
                "(portable assertion JSON)</summary>"
                f"<p><a download='openbadge-{safe}.json' "
                f"href='{href}'>Download assertion JSON</a></p>"
                f"<pre>{html.escape(blob)}</pre></details>")
        return ("<h2 id='open-badges'>Portable open badges</h2>"
                "<p>Each fully-owned pack exports as an Open Badges 3.0 "
                "assertion -- BadgeClass per pack, issuer this library, "
                "recipient a hash-only pseudonym (no accounts exist). "
                "Verifiers recompute against live owned-proofs.</p>"
                + "".join(bits))
    except Exception:  # noqa: BLE001 -- section must never raise
        return ""


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Portable open badges "
            "<small>(feature)</small></h3>"
            "<p>Every teaching certificate exports as Open Badges 3.0 "
            "JSON -- <code>groundwork/openbadge.py</code> emits one "
            "assertion per fully-owned pack (BadgeClass per pack, issuer "
            "this library, hash-only recipient, owned-proofs evidence) "
            "with hosted recomputation as verification.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Portable open badges</h3>"
                "<p>Badge help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; parent appends it to ENTRIES."""
    return {
        "id": "open-badges",
        "kind": "feature",
        "title": "Portable open badges",
        "blurb": ("Fully-owned packs export as Open Badges 3.0 "
                  "assertions -- download the JSON from History."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
