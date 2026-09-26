"""Sandbox output inline on predict-output cards (I-156)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import sandout as sandoutmod


def _card(**payload):
    return {"id": "c1", "exercise_type": "8",
            "payload": json.dumps(payload)}


class MeasuredOutputTest(unittest.TestCase):
    def test_returns_stripped_expected(self):
        self.assertEqual(
            sandoutmod.measured_output(
                {"code": "print(1)", "expected": "  1\n"}), "1")

    def test_empty_without_code_or_expected(self):
        self.assertEqual(sandoutmod.measured_output({}), "")
        self.assertEqual(
            sandoutmod.measured_output({"code": "print(1)"}), "")
        self.assertEqual(
            sandoutmod.measured_output({"code": "print(1)",
                                        "expected": "   "}), "")
        self.assertEqual(
            sandoutmod.measured_output({"code": "", "expected": "1"}), "")

    def test_non_dict_is_no_data(self):
        self.assertEqual(sandoutmod.measured_output("nope"), "")
        self.assertEqual(sandoutmod.measured_output(None), "")


class OutputHtmlTest(unittest.TestCase):
    def test_reveal_block_with_escaped_output(self):
        body = sandoutmod.output_html(
            _card(code="print('<x>')", expected="<x>"))
        self.assertIn("<details", body)
        self.assertIn("Show measured output", body)
        self.assertIn("&lt;x&gt;", body)
        self.assertNotIn("<x>", body)

    def test_legacy_fallback_is_empty_string(self):
        self.assertEqual(sandoutmod.output_html(_card()), "")
        self.assertEqual(
            sandoutmod.output_html(_card(code="print(1)")), "")
        self.assertEqual(sandoutmod.output_html({}), "")

    def test_long_output_truncated(self):
        body = sandoutmod.output_html(
            _card(code="print('x')", expected="y" * 900))
        self.assertIn("…", body)
        self.assertLess(len(body), 900)

    def test_never_raises(self):
        self.assertEqual(sandoutmod.output_html(None), "")
        self.assertEqual(
            sandoutmod.output_html({"payload": "{broken"}), "")


class StatusSectionTest(unittest.TestCase):
    def test_anchored_subsection(self):
        body = sandoutmod.section_html()
        self.assertIn(f"id='{sandoutmod.STATUS_ANCHOR}'", body)
        self.assertIn("groundwork/sandout.py", body)


class EffectTest(unittest.TestCase):
    def test_caller_widget_reveals_measured_output(self):
        body = cardsmod.answer_widget(
            _card(code="print(2 + 3)", expected="5"))
        self.assertIn("Show measured output", body)
        self.assertIn("<pre>5</pre>", body)

    def test_unmeasured_cards_byte_identical(self):
        plain = cardsmod.answer_widget(_card())
        self.assertNotIn("Show measured output", plain)
        self.assertIn("It prints/returns:", plain)


if __name__ == "__main__":
    unittest.main()
