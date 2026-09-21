"""URL-based session share: signed tokens, fail-closed decode, private render."""
import unittest

from groundwork import snapshot as mod


SECRET = "test-secret-49"
STATE = {"module_id": "m1", "answered": 10, "correct": 7}


class RoundTripTest(unittest.TestCase):
    def test_encode_then_decode(self):
        token = mod.encode_snapshot(STATE, SECRET, now=1000.0)
        self.assertIn(".", token)
        self.assertEqual(mod.decode_snapshot(token, SECRET, now=1000.0),
                         {"module_id": "m1", "answered": 10,
                          "correct": 7, "accuracy": 70})

    def test_token_is_url_safe(self):
        token = mod.encode_snapshot(STATE, SECRET, now=1000.0)
        for ch in ("+", "/", "=", " ", "\n"):
            self.assertNotIn(ch, token)

    def test_expiry_still_valid_before_deadline(self):
        token = mod.encode_snapshot(STATE, SECRET, ttl_seconds=60, now=1000.0)
        self.assertIsNotNone(mod.decode_snapshot(token, SECRET, now=1059.0))

    def test_accuracy_recomputed_not_trusted(self):
        token = mod.encode_snapshot(
            {"module_id": "m1", "answered": 4, "correct": 1,
             "accuracy": 100}, SECRET, now=1000.0)
        got = mod.decode_snapshot(token, SECRET, now=1000.0)
        self.assertEqual(got["accuracy"], 25)

    def test_encode_rejects_bad_args(self):
        with self.assertRaises(TypeError):
            mod.encode_snapshot(["nope"], SECRET)
        with self.assertRaises(ValueError):
            mod.encode_snapshot(STATE, "")
        with self.assertRaises(ValueError):
            mod.encode_snapshot(STATE, SECRET, ttl_seconds=0)


class FailClosedTest(unittest.TestCase):
    def setUp(self):
        self.token = mod.encode_snapshot(STATE, SECRET, ttl_seconds=60,
                                         now=1000.0)

    def test_tampered_body_rejected(self):
        body, _, sig = self.token.partition(".")
        other = mod.encode_snapshot({"module_id": "m9", "answered": 99,
                                     "correct": 99}, SECRET, now=1000.0)
        forged = other.partition(".")[0] + "." + sig
        self.assertNotEqual(body, other.partition(".")[0])
        self.assertIsNone(mod.decode_snapshot(forged, SECRET, now=1000.0))

    def test_tampered_signature_rejected(self):
        body, _, sig = self.token.partition(".")
        bad_sig = ("A" if sig[0] != "A" else "B") + sig[1:]
        self.assertIsNone(
            mod.decode_snapshot(body + "." + bad_sig, SECRET, now=1000.0))

    def test_expired_token_rejected(self):
        self.assertIsNone(
            mod.decode_snapshot(self.token, SECRET, now=2000.0))

    def test_wrong_secret_rejected(self):
        self.assertIsNone(
            mod.decode_snapshot(self.token, "other-secret", now=1000.0))

    def test_malformed_tokens_rejected(self):
        for bad in ("", "no-dot-here", "a.b.c", ".", ".sig", "body.",
                    "!!!.???", None, 12345, "x" * 5000):
            self.assertIsNone(mod.decode_snapshot(bad, SECRET), bad)

    def test_unknown_version_rejected(self):
        import base64
        import hashlib
        import hmac
        import json
        payload = {"v": 999, "exp": 9999999999, "data": STATE}
        raw = json.dumps(payload, sort_keys=True,
                         separators=(",", ":")).encode()
        body = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        sig = hmac.new(SECRET.encode(), body.encode(),
                       hashlib.sha256).digest()
        forged = (body + "." +
                  base64.urlsafe_b64encode(sig).decode().rstrip("="))
        self.assertIsNone(mod.decode_snapshot(forged, SECRET))

    def test_decode_never_raises(self):
        self.assertIsNone(mod.decode_snapshot(self.token, None))
        self.assertIsNone(mod.decode_snapshot(None, SECRET))
        self.assertIsNone(mod.decode_snapshot(self.token, ""))


class PrivacyTest(unittest.TestCase):
    def test_private_fields_stripped_from_token(self):
        rich = {**STATE, "answer": "secret text",
                "submission": "my attempt", "journal": "dear diary",
                "reviews": [{"grade": 5}], "front": "Q", "back": "A",
                "grade": 5, "confidence": 5}
        got = mod.decode_snapshot(
            mod.encode_snapshot(rich, SECRET, now=1000.0), SECRET, now=1000.0)
        self.assertEqual(set(got), {"module_id", "answered",
                                    "correct", "accuracy"})

    def test_private_fields_never_render(self):
        body = mod.snapshot_html(
            {"module_id": "m1", "answered": 2, "correct": 1,
             "answer": "secret text", "journal": "dear diary",
             "reviews": [{"grade": 1, "submission": "shh"}]})
        for leak in ("secret text", "dear diary", "shh", "submission"):
            self.assertNotIn(leak, body)
        self.assertIn("2 answered", body)

    def test_renderer_escapes_module_id(self):
        body = mod.snapshot_html({"module_id": "<script>x</script>",
                                  "answered": 1, "correct": 1})
        self.assertNotIn("<script>", body)
        self.assertIn("&lt;script&gt;", body)


class RenderTest(unittest.TestCase):
    def test_section_html_anchor(self):
        body = mod.section_html()
        self.assertIn("id='status-b9-snapshot'", body)
        self.assertIn("snapshot.py", body)

    def test_tour_entry_shape(self):
        entry = mod.tour_entry()
        self.assertEqual(entry["id"], "session-share")
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], "status-b9-snapshot")

    def test_snapshot_html_always_renders(self):
        for bad in (None, {}, "x", {"answered": "nonsense"}):
            body = mod.snapshot_html(bad)
            self.assertIn("id='snapshot'", body)


if __name__ == "__main__":
    unittest.main()
