"""Tests for the pre-mortem exercise (type 78, F-74)."""
import json
import unittest
from types import SimpleNamespace

from groundwork import premortem as mod


def make_concept(name="send_receipt"):
    return SimpleNamespace(node_id="c", name=name, kind="function",
                           file="billing.py", line=11)


RISKY = ("def send_receipt(uid, path=\"/tmp/out\"):\n"
         "    import requests\n"
         "    resp = requests.get(\"https://api/x?u=\" + str(uid))\n"
         "    f = open(path, \"w\")\n"
         "    f.write(resp.text)\n"
         "    try:\n"
         "        save(resp.text)\n"
         "    except Exception:\n"
         "        return []\n")


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex78", make_concept(), [RISKY], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (78, "pre-mortem", "evaluate"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_never_none(self):
        for args in [("ex78", make_concept(), [RISKY], {}),
                     ("ex78", make_concept(), [], {}),
                     (None, None, None, None)]:
            e = mod.generate(*args)
            self.assertIsNotNone(e)
            self.assertTrue(e["front"])

    def test_thin_input_ungrounded(self):
        e = mod.generate("ex78", make_concept(), ["   "], {})
        self.assertFalse(e["payload"]["grounded"])
        self.assertEqual(e["payload"]["items"], [])

    def test_deterministic(self):
        a = mod.generate("ex78", make_concept(), [RISKY], {})
        b = mod.generate("ex78", make_concept(), [RISKY], {})
        self.assertEqual(a["payload"]["items"], b["payload"]["items"])

    def test_gen_alias(self):
        e = mod.gen_premortem("ex78", make_concept(), [RISKY], {})
        self.assertEqual(e["type"], 78)


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex78", make_concept(), [RISKY], {})
        r = mod.grade(e, "\n".join(e["payload"]["items"]))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_half_passes(self):
        e = mod.generate("ex78", make_concept(), [RISKY], {})
        items = e["payload"]["items"]
        half = items[: max(1, len(items) // 2)]
        # half of >=2 items passes only when it reaches the 0.5 bar
        r = mod.grade(e, "\n".join(half))
        self.assertEqual(r["score"], len(half) / len(items))

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex78", make_concept(), [RISKY], {})
        for bad in ["", "   ", "looks fine to me", None, "def broken(:"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex78", make_concept(), [RISKY], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "a\nb"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class EffectTest(unittest.TestCase):
    """Behavioral effect: a type-78 card flows through Due with grading honored."""

    def test_due_flow_with_grading_and_legacy_untouched(self):
        from groundwork import exercises as exmod
        from groundwork import grading as gradingmod
        e = mod.generate("ex78", make_concept(), [RISKY], {"commit": "abc"})
        # cards.answer_widget falls to the generic else (no new widget branch)
        from groundwork import cards as cardsmod
        widget = cardsmod.answer_widget(
            {"id": "ex78", "exercise_type": "78",
             "payload": json.dumps({})}, origin="/due")
        self.assertIn("Your answer", widget)
        # grading honored through the registry + disclosure
        via = exmod.grade({"type": 78, "payload": e["payload"]},
                          "\n".join(e["payload"]["items"]), None)
        self.assertTrue(via["pass"])
        miss = exmod.grade({"type": 78, "payload": e["payload"]},
                           "everything is fine", None)
        self.assertFalse(miss["pass"])
        self.assertIn("half", gradingmod.disclosure(78).lower()
                      + gradingmod.disclosure(78))
        # legacy fallback pinned: pre-existing types grade exactly as before
        self.assertEqual(gradingmod.disclosure(49),
                         "Name at least half the abuse cases — checklist match "
                         "with partial credit per item.")
        legacy = exmod.grade(
            {"type": 49,
             "payload": {"items": ["a", "b"], "keys": [["a"], ["b"]]}},
            "a\nb", None)
        self.assertTrue(legacy["pass"])


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex78", make_concept(), [RISKY], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("billing.py:11", body)

    def test_render_escapes(self):
        e = mod.generate("ex78", make_concept(name="<b>"), [RISKY], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b18-premortem'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "pre-mortem", "kind": "feature",
                          "title": "Pre-mortem",
                          "blurb": "List how this code could fail before it does -- errors, retries, races, leaks.",
                          "path": "/status", "anchor": "status-b18-premortem"})


if __name__ == "__main__":
    unittest.main()
