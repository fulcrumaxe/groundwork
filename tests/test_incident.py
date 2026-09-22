"""Tests for the incident-replay drill (type 77, F-73)."""
import unittest
from types import SimpleNamespace

from groundwork import incident as mod


def make_concept(name="serve"):
    return SimpleNamespace(node_id="c", name=name, kind="handler",
                           file="serve.py", line=7)


PASS_ANSWERS = {
    "bad-deploy": ("signal=error-rate alert after deploy\n"
                   "detect=diffed the release, found breaking change\n"
                   "mitigate=rollback to previous release\n"
                   "prevent=canary gate plus deploy freeze\n"),
    "secret-leak": ("signal=secret-scan flagged the API key\n"
                    "detect=traced repo history to the deploy\n"
                    "mitigate=rotated the key and purged history\n"
                    "prevent=pre-commit hook plus rotation runbook\n"),
    "retry-storm": ("signal=ingest latency alert, deliveries replaying\n"
                    "detect=read queue depth, found retry loop\n"
                    "mitigate=idempotency keys and backoff drained queue\n"
                    "prevent=jittered backoff with circuit breaker\n"),
}


def passing_answer(ex):
    p = ex["payload"]
    seq = " ".join(chr(65 + list(p["order"]).index(k))
                   for k in range(len(p["shown"])))
    return PASS_ANSWERS[p["scenario"]] + f"order={seq}\n"


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex77", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (77, "incident-replay", "evaluate"))
        self.assertTrue(e["front"] and e["back"] and e["check"])
        self.assertTrue(e["payload"]["grounded"])

    def test_never_none_never_raises(self):
        for args in [("ex77", make_concept(), ["x = 1"], {}),
                     (None, None, None, None)]:
            e = mod.generate(*args)
            self.assertIsNotNone(e)
            self.assertTrue(e["front"] and e["check"])

    def test_legacy_no_data_fallback_pinned(self):
        e = mod.generate(None, None, None, None)
        self.assertFalse(e["payload"]["grounded"])
        self.assertIn(e["payload"]["scenario"], PASS_ANSWERS)

    def test_deterministic(self):
        a = mod.generate("ex77", make_concept(), ["x = 1"], {})
        b = mod.generate("ex77", make_concept(), ["x = 1"], {})
        self.assertEqual(a["check"], b["check"])
        self.assertEqual(a["payload"]["shown"], b["payload"]["shown"])

    def test_distinct_ids_diverge(self):
        seen = {mod.generate(f"ex77-{i}", make_concept(), ["x = 1"], {})["check"]
                for i in range(6)}
        self.assertGreater(len(seen), 1)


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex77", make_concept(), ["x = 1"], {})
        r = mod.grade(e, passing_answer(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_check_key_passes(self):
        e = mod.generate("ex77", make_concept(), ["x = 1"], {})
        r = mod.grade(e, e["check"])
        self.assertTrue(r["pass"])

    def test_wrong_order_fails_order_point(self):
        e = mod.generate("ex77", make_concept(), ["x = 1"], {})
        bad = passing_answer(e).splitlines()
        bad = [l if not l.startswith("order=") else "order=A B C D"
               for l in bad]
        if e["payload"]["order"] == [0, 1, 2, 3]:
            bad = [l if not l.startswith("signal=") else "signal=sunny"
                   for l in bad]
        r = mod.grade(e, "\n".join(bad))
        self.assertLess(r["score"], 1.0)

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex77", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", "hello world", None, "def broken(:"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex77", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "def f(): pass"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class EffectTest(unittest.TestCase):
    def test_due_flow_renders_grades_legacy_untouched(self):
        from groundwork import exercises as exmod
        e = exmod.generate(77, "ex77eff", make_concept(), ["x = 1"], {})
        self.assertEqual(e["type_name"], "incident-replay")
        html_body = exmod.render(e)
        self.assertIn("How grading works", html_body)
        self.assertIn("serve.py:7", html_body)
        ok = exmod.grade(e, e["check"])
        self.assertTrue(ok["pass"])
        # Legacy types untouched: same inputs, same contracts.
        legacy = exmod.generate(71, "ex71eff", make_concept(), ["x = 1"], {})
        self.assertEqual(legacy["type_name"], "ratelimit")
        lr = exmod.grade(legacy, "scope=x\nwindow=y\nburst=z\nretry=w\nwhy=q")
        self.assertIn("score", lr)
        flash = exmod.generate(1, "ex01eff", make_concept(), ["x = 1"], {})
        self.assertEqual(flash["type_name"], "flashcard")


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex77", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("serve.py:7", body)

    def test_render_escapes(self):
        e = mod.generate("ex77", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b18-incident'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "incident-replay", "kind": "feature",
                          "title": "Incident replay",
                          "blurb": "Replay a past outage — signal, detection, mitigation, prevention, and timeline order, rubric-graded.",
                          "path": "/status", "anchor": "status-b18-incident"})


if __name__ == "__main__":
    unittest.main()
