"""Study-buddy pings without leaderboards (F-125)."""
import unittest

from test_web import handler_for, make_module

from groundwork import buddyping as mod


class PingTest(unittest.TestCase):
    def test_solo_renders_nothing(self):
        self.assertEqual(mod.ping_html([]), "")
        self.assertEqual(mod.ping_html(["Solo"]), "")
        self.assertEqual(mod.ping_html(["A", "A", ""]), "")

    def test_welcome_before_first_owned(self):
        body = mod.ping_html(["Ann", "Bo"], 0, 5)
        self.assertIn("buddy-ping", body)
        self.assertIn("Ann", body)
        self.assertIn("Bo", body)
        self.assertIn("first concept", body)

    def test_cheer_midway_and_celebrate_at_full(self):
        mid = mod.ping_html(["Ann", "Bo"], 2, 5)
        self.assertIn("2 of 5 owned", mid)
        full = mod.ping_html(["Ann", "Bo"], 5, 5)
        self.assertIn("all 5", full)

    def test_no_leaderboard_language(self):
        for kind in (mod.WELCOME, mod.CHEER, mod.CELEBRATE):
            text = mod.ping_text(kind, ["Ann", "Bo"], 2, 5).lower()
            for word in ("rank", "leaderboard", "beat", "lose", "score"):
                self.assertNotIn(word, text)
        body = mod.ping_html(["Ann", "Bo"], 2, 5).lower()
        for word in ("rank", "leaderboard"):
            self.assertNotIn(word, body)

    def test_names_escaped_and_hostile_never_raises(self):
        body = mod.ping_html(["<i>A</i>", "B"], 1, 3)
        self.assertNotIn("<i>A</i>", body)
        self.assertEqual(mod.ping_html(None, None, None), "")
        self.assertEqual(mod.ping_text("bogus", None), "")
        self.assertEqual(mod.pick_ping("x", "y"), mod.WELCOME)
        self.assertEqual(mod.pair_names("nope"), [])

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_solo_module_page_has_no_ping(self):
        _tmp, db, _s, out = make_module("buddyping caller")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("buddy-ping", body)

    def test_duo_module_page_carries_ping(self):
        _tmp, db, _s, out = make_module("buddyping duo")
        h = handler_for(db)
        body = h.module_html(out["module_id"], buddies=["Ann", "Bo"])
        self.assertIn("buddy-ping", body)
        self.assertIn("Ann", body)


if __name__ == "__main__":
    unittest.main()
