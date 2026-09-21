"""Tests for the secret-scan exercise (type 50, F-27)."""
import unittest
from types import SimpleNamespace

from groundwork import secretscan as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="service",
                           file="deploy.py", line=3)


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex50", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (50, "secret-scan", "analyse"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_planted_is_fake_and_deterministic(self):
        a = mod.generate("ex50", make_concept(), ["x = 1"], {})
        b = mod.generate("ex50", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["mode"], "planted")
        self.assertTrue(a["payload"]["secret"].startswith("[REDACTED]"))
        self.assertEqual(a["payload"]["secret"], b["payload"]["secret"])
        self.assertEqual(a["payload"]["leak_line"], 2)

    def test_found_mode_uses_snippet_secret(self):
        e = mod.generate("ex50", make_concept(),
                         ['x = 1', 'password = "hunter2"'], {})
        self.assertEqual(e["payload"]["mode"], "found")
        self.assertEqual(e["payload"]["secret"], "hunter2")
        self.assertEqual(e["payload"]["leak_line"], 2)

    def test_no_surface_returns_none(self):
        self.assertIsNone(mod.generate("ex50", None, [], {}))
        self.assertIsNone(mod.generate("ex50", None, None, None))

    def test_never_raises(self):
        self.assertIsNone(mod.generate(None, None, None, None))


def answer_for(e):
    return e["payload"]["secret"]


class GradeTest(unittest.TestCase):
    def test_exact_accept(self):
        e = mod.generate("ex50", make_concept(), ["x = 1"], {})
        r = mod.grade(e, answer_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_quote_whitespace_normalized(self):
        e = mod.generate("ex50", make_concept(), ["x = 1"], {})
        s = e["payload"]["secret"]
        for variant in [f'  "{s}"  ', f"  '{s}'", f"\n{s}\n"]:
            r = mod.grade(e, variant)
            self.assertTrue(r["pass"], variant)

    def test_substring_and_dump_must_not_pass(self):
        e = mod.generate("ex50", make_concept(), ["x = 1"], {})
        s = e["payload"]["secret"]
        # A wrong value embedding the secret, and a dump of the whole
        # numbered snippet (which contains both the secret and its line
        # number among other digits), never isolate the leak: both fail.
        for bad in [f"xx{s}yy", f"prefix-{s}", e["payload"]["snippet"]]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"], bad)

    def test_wrong_value_rejected(self):
        e = mod.generate("ex50", make_concept(), ["x = 1"], {})
        r = mod.grade(e, "[REDACTED]")
        self.assertFalse(r["pass"])

    def test_line_number_accepted(self):
        e = mod.generate("ex50", make_concept(), ["x = 1"], {})
        for good in (str(e["payload"]["leak_line"]),
                     f"line {e['payload']['leak_line']}"):
            r = mod.grade(e, good)
            self.assertTrue(r["pass"], good)

    def test_wrong_line_rejected(self):
        e = mod.generate("ex50", make_concept(), ["x = 1"], {})
        self.assertFalse(mod.grade(e, "999")["pass"])
        self.assertFalse(mod.grade(e, "line 999")["pass"])

    def test_secret_digits_are_not_line_numbers(self):
        e = mod.generate("ex50", make_concept(), ["x = 1"], {})
        # Pasting the secret alone passes as a VALUE; digits buried in a
        # longer text never read as a line guess.
        r = mod.grade(e, e["payload"]["secret"])
        self.assertTrue(r["pass"])
        self.assertFalse(mod.grade(e, "leak 12345")["pass"])

    def test_hostile_never_raises(self):
        e = mod.generate("ex50", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None), (e, ""),
                                (e, "drop table; --"), (None, None),
                                ({"payload": {}}, "1")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex50", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("deploy.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex50", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b9-secretscan'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "secret-scan")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b9-secretscan")


if __name__ == "__main__":
    unittest.main()
