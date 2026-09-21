"""Tests for the i18n-extract exercise (type 53, F-30). Module-only imports."""
import unittest
from types import SimpleNamespace

from groundwork import i18n as mod

SAMPLE = (
    'def greet(name):\n'
    '    """Greet a user."""\n'
    '    import os\n'
    '    title = "Welcome back"\n'
    '    msg = f"Hello, {name}!"\n'
    '    print("Press continue to proceed")\n'
    '    return msg\n'
)

WANT = ["Hello, {...}!", "Press continue to proceed", "Welcome back"]


def make_concept(name="greet"):
    return SimpleNamespace(node_id="c53", name=name, kind="function",
                           file="ui.py", line=7)


class CollectTest(unittest.TestCase):
    def test_reference_set(self):
        self.assertEqual(mod.reference_set(SAMPLE), WANT)

    def test_docstring_excluded(self):
        self.assertNotIn("Greet a user.", mod.reference_set(SAMPLE))

    def test_import_excluded(self):
        self.assertNotIn("os", mod.reference_set(SAMPLE))

    def test_dunder_excluded(self):
        src = '__all__ = ["greet"]\nX = "Ship it"\n'
        self.assertEqual(mod.reference_set(src), ["Ship it"])

    def test_hole_contributes_nothing(self):
        self.assertEqual(mod.reference_set('f"{x}"\n'), [])

    def test_bad_syntax_never_raises(self):
        self.assertEqual(mod.collect_strings("def broken(:"), [])
        self.assertEqual(mod.reference_set("def broken(:"), [])


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex53", make_concept(), SAMPLE.splitlines(), {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (53, "i18n-extract", "analyse"))

    def test_payload_grounded(self):
        e = mod.generate("ex53", make_concept(), SAMPLE.splitlines(), {})
        self.assertTrue(e["payload"]["grounded"])
        self.assertEqual(e["payload"]["strings"], WANT)
        self.assertEqual(e["payload"]["count"], 3)
        self.assertIn("{...}", e["front"])

    def test_no_strings_yields_ungrounded_card(self):
        # Never None (all-types-generate contract): no strings is an
        # ungrounded card the pipeline drops.
        e = mod.generate("ex53", make_concept(), ["x = 1"], {})
        self.assertTrue(e["front"])
        self.assertFalse(e["payload"]["grounded"])
        self.assertEqual(e["payload"]["strings"], [])

    def test_fallback_never_raises(self):
        e = mod.generate("ex53", None, None, None)
        self.assertTrue(e["front"] and e["payload"]["strings"])
        self.assertFalse(e["payload"]["grounded"])


def answer_for(e, order=None):
    strings = order if order is not None else e["payload"]["strings"]
    return "\n".join(strings)


class GradeTest(unittest.TestCase):
    def test_exact_accept(self):
        e = mod.generate("ex53", make_concept(), SAMPLE.splitlines(), {})
        r = mod.grade(e, answer_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_order_insensitive_whitespace_fold(self):
        e = mod.generate("ex53", make_concept(), SAMPLE.splitlines(), {})
        got = "\n".join("  " + s + "  " for s in reversed(e["payload"]["strings"]))
        r = mod.grade(e, got)
        self.assertTrue(r["pass"])

    def test_missing_rejects(self):
        e = mod.generate("ex53", make_concept(), SAMPLE.splitlines(), {})
        r = mod.grade(e, "\n".join(e["payload"]["strings"][:2]))
        self.assertFalse(r["pass"])
        self.assertIn("missing", r["feedback"])

    def test_extra_rejects(self):
        e = mod.generate("ex53", make_concept(), SAMPLE.splitlines(), {})
        r = mod.grade(e, answer_for(e) + "\nGreet a user.")
        self.assertFalse(r["pass"])
        self.assertIn("extra", r["feedback"])

    def test_substring_extra_still_rejects(self):
        # A wrong call/string CONTAINING a required string is still extra.
        e = mod.generate("ex53", make_concept(), SAMPLE.splitlines(), {})
        bad = [s for s in e["payload"]["strings"]
               if s != "Welcome back"] + ["Welcome back!"]
        r = mod.grade(e, "\n".join(bad))
        self.assertFalse(r["pass"])

    def test_hostile_never_raises(self):
        e = mod.generate("ex53", make_concept(), SAMPLE.splitlines(), {})
        for bad_ex, bad_sub in [({}, "a"), (e, None), (e, ""),
                                (e, "drop table; --"), (None, None),
                                ({"payload": {}}, "x")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex53", make_concept(), SAMPLE.splitlines(), {})
        body = mod.render(e)
        self.assertIn("<pre>", body)
        self.assertIn("name='answer'", body)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("ui.py:7", body)

    def test_render_escapes(self):
        e = mod.generate("ex53", make_concept(name="<b>"),
                         SAMPLE.splitlines(), {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b9-i18n'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "i18n-extraction")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b9-i18n")


if __name__ == "__main__":
    unittest.main()
