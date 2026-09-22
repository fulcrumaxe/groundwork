"""Tests for API guessing (type 81, F-77)."""
import unittest

from groundwork import exercises as exmod
from groundwork import grading as gradingmod


def _concept(name="parse", file="app.py", line=1):
    return type("C", (), {"name": name, "file": file, "line": line,
                          "node_id": f"{file}:{name}"})()


def _snippet():
    return ["import json", "",
            "def parse(raw):",
            "    data = json.loads(raw)",
            "    return data"]


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        card = exmod.generate(81, "ex001", _concept(), _snippet(), {})
        self.assertEqual(
            (card["type"], card["type_name"], card["bloom"]),
            (81, "api-guess", "apply"))

    def test_grounded_on_mapped_call(self):
        card = exmod.generate(81, "ex001", _concept(), _snippet(), {})
        p = card["payload"]
        self.assertTrue(p["grounded"])
        self.assertEqual(p["answer"], "json.loads")
        self.assertEqual(len(p["choices"]), 4)
        self.assertIn("json.loads", p["choices"])
        self.assertTrue(card["front"])
        # Due shows the front text: the four choices must be on it.
        for c in p["choices"]:
            self.assertIn(c, card["front"])

    def test_never_none_never_raises(self):
        for args in [(None, None, None, None),
                     ("x", None, None, None),
                     ("x", _concept(), ["x = 1"], None),
                     ("x", _concept(), ["x = 1"], {"commit": "abc"})]:
            card = exmod.generate(81, *args)
            self.assertIsNotNone(card)
            self.assertEqual(card["type"], 81)

    def test_ungrounded_shape(self):
        card = exmod.generate(81, "ex9", _concept(), ["x = 1"], {})
        self.assertFalse(card["payload"]["grounded"])

    def test_determinism(self):
        a = exmod.generate(81, "ex007", _concept(), _snippet(), {})
        b = exmod.generate(81, "ex007", _concept(), _snippet(), {})
        self.assertEqual(a["payload"], b["payload"])


class GradeTest(unittest.TestCase):
    def test_dispatch_passes_and_fails(self):
        card = exmod.generate(81, "ex001", _concept(), _snippet(), {})
        ok = exmod.grade(card, "json.loads")
        self.assertTrue(ok["pass"])
        self.assertEqual(ok["score"], 1.0)
        bad = exmod.grade(card, "re.search")
        self.assertFalse(bad["pass"])
        self.assertIn("json.loads", bad["feedback"])

    def test_empty_fails_with_nudge(self):
        card = exmod.generate(81, "ex001", _concept(), _snippet(), {})
        res = exmod.grade(card, "   ")
        self.assertFalse(res["pass"])

    def test_grading_never_raises(self):
        from groundwork import apiguess as apimod
        res = apimod.grade(None, None)
        self.assertFalse(res["pass"])
        res = apimod.grade({}, object())
        self.assertFalse(res["pass"])


class RenderTest(unittest.TestCase):
    def test_widget_shape(self):
        card = exmod.generate(81, "ex001", _concept(), _snippet(), {})
        out = exmod.render(card)
        self.assertIn("Commit prediction", out)
        self.assertIn("How grading works", out)
        for c in card["payload"]["choices"]:
            self.assertIn(c.replace("<", "&lt;"), out)
        # The docs pointer lives on the back (verify step), never in the
        # widget: showing library/json upfront would leak the answer.
        self.assertNotIn("library/json", out)
        self.assertIn("library/json", card["back"])

    def test_no_unescaped_submission(self):
        card = exmod.generate(81, "ex001", _concept(), _snippet(), {})
        card["payload"]["choices"] = ["<script>alert(1)</script>"] + \
            card["payload"]["choices"][1:]
        out = exmod.render(card)
        self.assertNotIn("<script>alert", out)


class DisclosureTest(unittest.TestCase):
    def test_disclosure_names_prediction(self):
        text = gradingmod.disclosure(81)
        self.assertIn("Predict", text)
        self.assertIn("docs", text)


class LegacyFallbackTest(unittest.TestCase):
    def test_ungrounded_card_skipped_shape(self):
        card = exmod.generate(81, "ex9", _concept(), ["x = 1"], {})
        self.assertFalse(card["payload"]["grounded"])

    def test_unknown_type_error_unchanged(self):
        with self.assertRaises(ValueError):
            exmod.generate(999, "ex1", _concept(), [], {})


if __name__ == "__main__":
    unittest.main()
