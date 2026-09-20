"""Empty-answer guard (I-151)."""
import unittest

from groundwork import answerguard as agmod


class GuardTest(unittest.TestCase):
    def test_ok_answer(self):
        self.assertEqual(agmod.guard("  hello  "), {"ok": True, "warning": ""})

    def test_empty_and_blank(self):
        for bad in ("", "   ", None):
            res = agmod.guard(bad)
            self.assertFalse(res["ok"])
            self.assertTrue(res["warning"])

    def test_min_chars(self):
        self.assertFalse(agmod.guard("hi", min_chars=5)["ok"])
        self.assertTrue(agmod.guard("hello world", min_chars=5)["ok"])

    def test_guard_html(self):
        self.assertEqual(agmod.guard_html(""), "")
        body = agmod.guard_html("looks empty")
        self.assertIn("role='alert'", body)
        self.assertIn("looks empty", body)


if __name__ == "__main__":
    unittest.main()
