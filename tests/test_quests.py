"""Prerequisite unlock quests (F-54): chain + unlock state over prereq edges."""
import unittest

from groundwork import quests as qmod


class QuestPathTest(unittest.TestCase):
    def test_linear_chain_order_and_next(self):
        path = qmod.quest_path(
            "C", {"C": ["B"], "B": ["A"], "A": []}, owned={"A"})
        self.assertEqual(path["chain"], ["A", "B", "C"])
        self.assertFalse(path["unlocked"])
        self.assertEqual(path["next"], "B")

    def test_fully_owned_unlocks_with_no_next(self):
        path = qmod.quest_path(
            "C", {"C": ["B"], "B": ["A"], "A": []},
            owned={"A", "B", "C"})
        self.assertEqual(path["chain"], ["A", "B", "C"])
        self.assertTrue(path["unlocked"])
        self.assertIsNone(path["next"])

    def test_missing_node_fails_closed_to_single_step(self):
        path = qmod.quest_path("Z", {"C": ["B"]}, owned=set())
        self.assertEqual(path["chain"], ["Z"])
        self.assertFalse(path["unlocked"])
        self.assertEqual(path["next"], "Z")
        owned = qmod.quest_path("Z", {"C": ["B"]}, owned={"Z"})
        self.assertTrue(owned["unlocked"])
        self.assertIsNone(owned["next"])

    def test_cycle_terminates(self):
        path = qmod.quest_path(
            "A", {"A": ["B"], "B": ["A"]}, owned=set())
        self.assertEqual(sorted(path["chain"]), ["A", "B"])
        self.assertEqual(path["chain"][-1], "A")
        self.assertFalse(path["unlocked"])

    def test_hostile_input_never_raises(self):
        for bad in (None, 123, "", [], {},
                    qmod.quest_path(None, None, None)):
            path = qmod.quest_path(bad, "nope", "nope")
            self.assertIn("chain", path)
            self.assertIn("unlocked", path)
            self.assertIn("next", path)
        self.assertEqual(qmod.quest_path("A", "nope", object())["chain"], ["A"])


class QuestsHtmlTest(unittest.TestCase):
    def test_locked_unlocked_classes(self):
        html = qmod.quests_html(qmod.quest_path(
            "C", {"C": ["B"], "B": ["A"], "A": []}, owned={"A"}))
        self.assertIn("<ol class='quest-path'>", html)
        self.assertIn("<li class='quest-unlocked'>A</li>", html)
        self.assertIn("<li class='quest-locked'>B</li>", html)
        self.assertIn("<li class='quest-locked'>C</li>", html)

    def test_escapes_names_and_emits_no_style(self):
        html = qmod.quests_html({"chain": ["<b>A</b>", "B"],
                                 "unlocked": False, "next": "<b>A</b>"})
        self.assertNotIn("<b>", html)
        self.assertIn("&lt;b&gt;", html)
        self.assertNotIn("<style", html.lower())

    def test_empty_and_hostile_render_empty_never_raise(self):
        self.assertEqual(qmod.quests_html({}), "")
        self.assertEqual(qmod.quests_html(None), "")
        self.assertEqual(qmod.quests_html(object()), "")


class StatusTourTest(unittest.TestCase):
    def test_section_html_anchor(self):
        self.assertIn("id='status-b12-quests'", qmod.section_html())

    def test_tour_entry_shape(self):
        entry = qmod.tour_entry()
        self.assertEqual(entry["id"], "unlock-quests")
        self.assertEqual(entry["kind"], "feature")
        self.assertTrue(entry["title"] and entry["blurb"])
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], "status-b12-quests")

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "quests.py").read_text(encoding="utf-8")
        for marker in ("[REDACTED]", "TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
