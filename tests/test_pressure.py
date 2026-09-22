"""Tests for the pressure-drill exercise (type 76, F-72)."""
import json
import unittest
from types import SimpleNamespace

from groundwork import pressure as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="service",
                           file="checkout.py", line=41)


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex76", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (76, "pressure-drill", "analyse"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])
        self.assertEqual(e["payload"]["budget_s"], 90)

    def test_never_none(self):
        for args in [("ex76", make_concept(), ["x = 1"], {}),
                     ("ex76", make_concept(), ["boom timeout x"], {}),
                     (None, None, None, None)]:
            e = mod.generate(*args)
            self.assertIsNotNone(e)
            self.assertTrue(e["front"] and e["back"])

    def test_deterministic(self):
        a = mod.generate("ex76", make_concept(), ["x = 1"], {})
        b = mod.generate("ex76", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["log"], b["payload"]["log"])
        self.assertEqual(a["payload"]["cause"], b["payload"]["cause"])

    def test_distinct_ids_diverge(self):
        logs = {mod.generate(f"ex76-{i}", make_concept(), ["x = 1"], {})["payload"]["log"]
                for i in range(6)}
        self.assertGreater(len(logs), 1)

    def test_grounded_from_signals(self):
        e = mod.generate("ex76", make_concept(),
                         ["FATAL: connection refused on db"], {})
        self.assertEqual(e["payload"]["mode"], "grounded")
        self.assertEqual(e["payload"]["cause"], "database connection refused")

    def test_log_shape(self):
        e = mod.generate("ex76", make_concept(), ["x = 1"], {})
        log = e["payload"]["log"]
        victim, decoy = e["payload"]["victim"], e["payload"]["decoy"]
        self.assertNotEqual(victim, decoy)
        self.assertIn(victim, log)
        self.assertIn("FATAL", log)


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex76", make_concept(), ["x = 1"], {})
        r = mod.grade(e, e["payload"]["cause"])
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_alias_passes(self):
        e = mod.generate("ex76", make_concept(), ["x = 1"], {})
        alias = e["payload"]["aliases"][0]
        self.assertTrue(mod.grade(e, f'  "{alias}." ')["pass"])

    def test_herring_and_decoy_fail(self):
        e = mod.generate("ex76", make_concept(), ["x = 1"], {})
        for bad in list(mod.HERRING_WARNS) + list(mod.HERRING_ERRORS):
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_pasted_log_fails(self):
        e = mod.generate("ex76", make_concept(), ["x = 1"], {})
        r = mod.grade(e, e["payload"]["log"])
        self.assertFalse(r["pass"])

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex76", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", "hello world", None, "def broken(:"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex76", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "def f(): pass"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex76", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("<pre>", body)
        self.assertIn("drill-clock", body)
        self.assertIn("How grading works", body)
        self.assertIn("checkout.py:41", body)

    def test_render_escapes(self):
        e = mod.generate("ex76", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b18-pressure'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "pressure-drill", "kind": "feature",
                          "title": "Pressure drill",
                          "blurb": "Diagnose a production-style log against a 90s clock — follow the victim request, not the noise.",
                          "path": "/status", "anchor": "status-b18-pressure"})


class DueFlowEffectTest(unittest.TestCase):
    """Effect: a type-76 card renders in the due flow with grading honored,
    legacy types untouched (legacy no-data path pinned as fallback)."""

    def test_due_widget_renders_with_disclosure(self):
        from groundwork import cards as cardsmod
        from groundwork import grading as gradingmod
        e = mod.generate("ex76", make_concept(), ["x = 1"], {})
        card = {"id": "ex76", "exercise_type": "76",
                "payload": json.dumps({"cause": e["payload"]["cause"]}),
                "front": e["front"], "back": e["back"],
                "concept": e["concept"], "file": e["file"], "line": e["line"]}
        body = cardsmod.answer_widget(card, origin="/due")
        # Generic else-branch handles the unknown-to-cards type: no new
        # widget branch required (verified: cards.py line ~181 else).
        self.assertIn("Your answer", body)
        self.assertIn(gradingmod.disclosure(76)[:20], body)

    def test_grading_honored_end_to_end(self):
        e = mod.generate("ex76", make_concept(), ["x = 1"], {})
        self.assertTrue(mod.check(e, e["payload"]["cause"]))
        self.assertFalse(mod.check(e, mod.HERRING_WARNS[0]))

    def test_legacy_no_data_fallback_pinned(self):
        # Thin input still yields a self-contained drill card (fallback),
        # and legacy type 58 keeps its exact contract untouched.
        from groundwork import logread as legacymod
        thin = mod.generate("ex76", make_concept(), [], {})
        self.assertIsNotNone(thin)
        self.assertTrue(thin["payload"]["grounded"])
        legacy = legacymod.generate("ex58", make_concept(), [], {})
        self.assertEqual((legacy["type"], legacy["type_name"]),
                         (58, "log-reading"))
        self.assertFalse(legacymod.grade(legacy, "definitely not a cause")["pass"])


if __name__ == "__main__":
    unittest.main()
