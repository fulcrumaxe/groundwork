"""Worked-example replay (I-105): step through the measured trace."""
import unittest

from groundwork import lessons as lesmod
from groundwork import replay as replmod


def _lesson():
    return {"concept_id": "c", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1,
            "summary": "add() totals two numbers via its defaults.",
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
            "how": ["Sets total.", "Hands back."],
            "worked": {"call": "add(2, 3)", "output": "5",
                       "trace": {"var": "total", "steps": ["1", "3", "5"]}},
            "dualcode": {"steps": ["Sets total.", "Hands back."],
                         "states": ["1", "5"]}}


class ReplayUnitTest(unittest.TestCase):
    def test_steps_prefer_measured_trace(self):
        rows = replmod.replay_steps(_lesson())
        self.assertEqual([r["step"] for r in rows], [1, 2, 3])
        self.assertEqual(rows[0]["state"], "1")
        self.assertEqual(rows[2]["state"], "5")

    def test_clamp_and_links(self):
        self.assertEqual(replmod.clamp_step(_lesson(), 99), 3)
        self.assertEqual(replmod.clamp_step(_lesson(), "garbage"), 1)
        self.assertIsNone(replmod.clamp_step({}, 1))
        html_out = replmod.replay_html(_lesson(), 99)
        self.assertIn("Step 3 of 3", html_out)
        self.assertIn("?replay=2#replay", html_out)

    def test_empty_without_trace(self):
        for bad in ({}, {"summary": "hi"}, None, 42, "x"):
            self.assertEqual(replmod.replay_steps(bad), [])
            self.assertEqual(replmod.replay_html(bad), "")
        # Diagram steps without a measured trace keep the legacy pack.
        plain = _lesson()
        plain["worked"] = None
        self.assertEqual(replmod.replay_steps(plain), [])

    def test_steps_capped(self):
        lesson = _lesson()
        lesson["worked"]["trace"]["steps"] = [str(i) for i in range(20)]
        self.assertEqual(len(replmod.replay_steps(lesson)), replmod.MAX_STEPS)

    def test_never_raises(self):
        replmod.replay_steps(None)
        replmod.replay_html(None)
        replmod.clamp_step(None, None)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{replmod.STATUS_ANCHOR}'",
                      replmod.section_html())
        e = replmod.tour_entry()
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], replmod.STATUS_ANCHOR)


class ReplayEffectTest(unittest.TestCase):
    def test_caller_renders_stepped_replay(self):
        html_out = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/",
                                        replay_step=2)
        self.assertIn("Step 2 of 3", html_out)
        self.assertIn("?replay=3#replay", html_out)
        self.assertNotIn("dual-trace", html_out)

    def test_caller_legacy_pack_without_trace(self):
        lesson = _lesson()
        lesson["worked"] = None
        html_out = lesmod.render_levels(lesson, 0.0, 0, "auto", "/")
        self.assertIn("dual-diagram", html_out)
        self.assertNotIn("class='replay'", html_out)

    def test_caller_default_step_is_first(self):
        html_out = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        self.assertIn("Step 1 of 3", html_out)


if __name__ == "__main__":
    unittest.main()
