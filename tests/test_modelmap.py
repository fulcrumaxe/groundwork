"""Tests for the model-map exercise (type 82, F-78)."""
import unittest

from groundwork import exercises as exmod
from groundwork import grading as gradingmod


class _Node:
    def __init__(self, name, calls=()):
        self.name = name
        self.calls = list(calls)


class _Graph:
    def __init__(self, edges, nodes):
        self.edges = edges
        self.nodes = nodes


def _concept(name="add", node_id="calc.py:add"):
    return type("C", (), {"name": name, "node_id": node_id,
                          "file": "calc.py", "line": 1})()


def _ctx():
    graph = _Graph(
        edges=[("serve", "calc.py:add", "calls"),
               ("calc.py:add", "total", "calls")],
        nodes={"calc.py:add": _Node("add", ["total"]),
               "serve": _Node("serve"), "total": _Node("total")})
    return {"graph": graph, "commit": "abc1234"}


def _snippet():
    return ["def add(a, b):", "    total = a + b", "    return total"]


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        card = exmod.generate(82, "ex001", _concept(), _snippet(), _ctx())
        self.assertEqual(
            (card["type"], card["type_name"], card["bloom"]),
            (82, "model-map", "analyse"))

    def test_reference_edges_and_no_neighbour_leak(self):
        card = exmod.generate(82, "ex001", _concept(), _snippet(), _ctx())
        p = card["payload"]
        self.assertTrue(p["grounded"])
        self.assertEqual(p["nodes"], ["serve", "add", "total"])
        self.assertEqual(p["edges"], [["serve", "add"], ["add", "total"]])
        self.assertNotIn("serve", card["front"].split("```")[0])
        self.assertIn("serve -> add -> total", card["back"])

    def test_alias(self):
        from groundwork import modelmap as mmmod
        a = mmmod.generate("e1", _concept(), _snippet(), _ctx())
        b = mmmod.gen_model_map("e1", _concept(), _snippet(), _ctx())
        self.assertEqual(a, b)

    def test_isolated_is_ungrounded(self):
        card = exmod.generate(82, "ex9", _concept(), ["x = 1"], {})
        self.assertFalse(card["payload"]["grounded"])

    def test_never_none_never_raises(self):
        for args in [(None, None, None, None),
                     ("x", None, None, None),
                     ("x", _concept(), None, None)]:
            card = exmod.generate(82, *args)
            self.assertIsNotNone(card)
            self.assertEqual(card["type"], 82)


class GradeTest(unittest.TestCase):
    def _card(self):
        return exmod.generate(82, "ex001", _concept(), _snippet(), _ctx())

    def test_exact_set_passes(self):
        res = exmod.grade(self._card(), "serve -> add\nadd -> total")
        self.assertTrue(res["pass"])
        self.assertEqual(res["score"], 1.0)

    def test_separators_accepted(self):
        res = exmod.grade(self._card(), "serve > add\nadd : total")
        self.assertTrue(res["pass"])

    def test_partial_credit(self):
        res = exmod.grade(self._card(), "serve -> add\nadd -> wrong")
        self.assertFalse(res["pass"])
        self.assertEqual(res["score"], 0.5)
        self.assertIn("missing", res["feedback"])
        self.assertIn("extra", res["feedback"])

    def test_empty_and_empty_reference_fail_closed(self):
        res = exmod.grade(self._card(), "   ")
        self.assertFalse(res["pass"])
        res = exmod.grade({"type": 82, "payload": {"edges": []}}, "a -> b")
        self.assertFalse(res["pass"])

    def test_grading_never_raises(self):
        from groundwork import modelmap as mmmod
        res = mmmod.grade(None, None)
        self.assertFalse(res["pass"])


class RenderTest(unittest.TestCase):
    def test_widget_shape(self):
        card = exmod.generate(82, "ex001", _concept(), _snippet(), _ctx())
        out = exmod.render(card)
        self.assertIn("textarea", out)
        self.assertIn("How grading works", out)
        self.assertIn("calc.py:1", out)


class DisclosureTest(unittest.TestCase):
    def test_disclosure_names_flow(self):
        text = gradingmod.disclosure(82)
        self.assertIn("data flow", text)
        self.assertIn("partial credit", text)


if __name__ == "__main__":
    unittest.main()
