"""Tests for the transfer-test exercise (type 74, F-70)."""
import json
import unittest
from types import SimpleNamespace

from groundwork import cards as cardsmod
from groundwork import exercises as exmod
from groundwork import transfer as mod


def make_concept(name="add"):
    return SimpleNamespace(node_id="c1", name=name, kind="function",
                           file="calc.py", line=3)


def ctx():
    return {"runnable": "def add(a=2, b=3):\n    return a + b",
            "expected_output": "5", "commit": "abc"}


class FakeRunner:
    def __init__(self, stdout="5", ok=True):
        self.stdout, self.ok, self.seen = stdout, ok, []
        self.stderr = ""

    def run(self, code):
        self.seen.append(code)
        return SimpleNamespace(ok=self.ok, stdout=self.stdout,
                               stderr=self.stderr)


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex74", make_concept(), ["x = 1"], ctx())
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (74, "transfer-test", "apply"))
        self.assertTrue(e["payload"]["grounded"])

    def test_no_anchor_on_front(self):
        # "no anchor": front carries no file:line pointer, no "see the
        # lesson" back-link (the prose word "lesson" itself is fine).
        e = mod.generate("ex74", make_concept(), ["x = 1"], ctx())
        self.assertNotIn("calc.py", e["front"])
        self.assertNotIn(":3", e["front"])
        self.assertNotIn("see the lesson", e["front"].lower())
        self.assertNotIn("see lesson", e["front"].lower())

    def test_novel_differs_but_runs_same(self):
        e = mod.generate("ex74", make_concept(), ["x = 1"], ctx())
        self.assertNotEqual(e["payload"]["novel"], ctx()["runnable"])
        ns: dict = {}
        exec(compile(e["payload"]["novel"], "<novel>", "exec"), ns)
        fn = next(v for v in ns.values() if callable(v))
        self.assertEqual(repr(fn()), "5")

    def test_never_none(self):
        for args in [("ex74", make_concept(), ["x = 1"], ctx()),
                     (None, None, None, None)]:
            e = mod.generate(*args)
            self.assertIsNotNone(e)
            self.assertTrue(e["front"])

    def test_thin_input_ungrounded_fallback(self):
        # Legacy no-data path pinned: thin input -> ungrounded, pipeline skips.
        e = mod.generate("ex74", make_concept(), [], {})
        self.assertFalse(e["payload"]["grounded"])

    def test_deterministic(self):
        a = mod.generate("ex74", make_concept(), ["x"], ctx())
        b = mod.generate("ex74", make_concept(), ["x"], ctx())
        self.assertEqual(a["payload"]["novel"], b["payload"]["novel"])

    def test_distinct_ids_feed_the_seed(self):
        # The id feeds renaming deterministically: same id replays the
        # same novel (see test_deterministic); distinct ids seed apart.
        self.assertNotEqual(mod._seed("ex74a"), mod._seed("ex74b"))


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex74", make_concept(), ["x"], ctx())
        r = mod.grade(e, "5", FakeRunner("5"))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_wrong_answer_fails(self):
        e = mod.generate("ex74", make_concept(), ["x"], ctx())
        r = mod.grade(e, "6", FakeRunner("5"))
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.0)

    def test_stale_reference_flagged(self):
        e = mod.generate("ex74", make_concept(), ["x"], ctx())
        r = mod.grade(e, "5", FakeRunner("CHANGED"))
        self.assertFalse(r["pass"])

    def test_no_runner_fails_closed(self):
        e = mod.generate("ex74", make_concept(), ["x"], ctx())
        r = mod.grade(e, "5", None)
        self.assertFalse(r["pass"])

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex74", make_concept(), ["x"], ctx())
        for bad in ["", "   ", None]:
            r = mod.grade(e, bad, FakeRunner("5"))
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex74", make_concept(), ["x"], ctx())
        for bad_ex, bad_sub in [({}, "5"), (e, None),
                                ({"payload": {}}, "5"), (None, None)]:
            r = mod.grade(bad_ex, bad_sub, FakeRunner("5"))
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex74", make_concept(), ["x"], ctx())
        body = mod.render(e)
        self.assertIn("name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("sandbox-measured", body)

    def test_render_escapes(self):
        e = mod.generate("ex74", make_concept(name="<b>"), ["x"], ctx())
        self.assertIn("&lt;b&gt;", mod.render(e))

    def test_section_html_anchor(self):
        self.assertIn("id='status-b18-transfer'", mod.section_html())

    def test_tour_entry_shape(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "transfer-test")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["path"], "/status")
        self.assertEqual(t["anchor"], "status-b18-transfer")


class EffectTest(unittest.TestCase):
    """Behavioral effect: type-74 card renders in the due flow with grading
    honored; the legacy no-data path stays as fallback; legacy types untouched."""

    def test_due_flow_with_legacy_fallback(self):
        fresh = mod.generate("ex74", make_concept(), ["x"], ctx())
        thin = mod.generate("ex74t", make_concept(), [], {})
        queue = [c for c in (fresh, thin)
                 if c["payload"].get("grounded", True)]
        self.assertEqual([c["type"] for c in queue], [74])  # thin skipped
        card = {"id": queue[0]["id"], "exercise_type": 74,
                "payload": json.dumps(queue[0]["payload"])}
        widget = cardsmod.answer_widget(card)
        self.assertIn("placeholder='Your answer'", widget)  # generic else
        self.assertIn("How grading works", widget)
        self.assertTrue(mod.grade(queue[0], "5", FakeRunner("5"))["pass"])
        self.assertFalse(mod.grade(queue[0], "nope", FakeRunner("5"))["pass"])

    def test_legacy_types_untouched(self):
        c = SimpleNamespace(node_id="c1", name="add", kind="function",
                            file="calc.py", line=1)
        legacy = exmod.generate(8, "ex008", c, ["x"],
                                {"runnable": "print(2 + 3)",
                                 "expected_output": "5"})
        self.assertEqual(legacy["type_name"], "predict-output")
        r = exmod.grade(legacy, "5", FakeRunner("5"))
        self.assertTrue(r["pass"])


if __name__ == "__main__":
    unittest.main()
