"""Reading-group mode (F-89)."""
import unittest

from groundwork import readgroup as rgmod

from test_web import handler_for, make_module


def _lesson():
    return {"name": "add",
            "summary": "add() totals two numbers via its defaults.",
            "how": ["Read the defaults."]}


class PromptsTest(unittest.TestCase):
    def test_three_deterministic_prompts(self):
        first = rgmod.discussion_prompts(_lesson())
        self.assertEqual(len(first), 3)
        self.assertEqual(first, rgmod.discussion_prompts(_lesson()))
        self.assertTrue(all(p for p in first))

    def test_thin_lesson_gets_generic_trio(self):
        self.assertEqual(rgmod.discussion_prompts({}),
                         list(rgmod.GENERIC_PROMPTS))
        self.assertEqual(rgmod.discussion_prompts(None),
                         list(rgmod.GENERIC_PROMPTS))


class PlanTest(unittest.TestCase):
    def test_minute_shares(self):
        self.assertEqual(rgmod.session_plan([("a", 1), ("b", 3)]),
                         [("a", 1, 25), ("b", 3, 75)])
        self.assertEqual(rgmod.session_plan([]), [])
        self.assertEqual(rgmod.session_plan(None), [])


class RosterTest(unittest.TestCase):
    def test_escaped_and_empty(self):
        out = rgmod.roster_html(["ann", "<b>"])
        self.assertIn("ann", out)
        self.assertIn("&lt;b&gt;", out)
        self.assertNotIn("<b>", out)
        self.assertEqual(rgmod.roster_html([]), "")
        self.assertEqual(rgmod.roster_html(None), "")


class MergeTest(unittest.TestCase):
    def test_last_writer_wins(self):
        local = {"ann": {"done": 1, "at": "2020-01-01"}}
        peer = {"ann": {"done": 2, "at": "2020-01-02"},
                "bob": {"done": 0, "at": "2020-01-01"}}
        got = rgmod.presence_merge(local, peer)
        self.assertEqual(got["ann"]["done"], 2)
        self.assertIn("bob", got)
        self.assertEqual(rgmod.presence_merge(None, "nope"), {})


class SessionTest(unittest.TestCase):
    def test_no_presence_no_section(self):
        self.assertEqual(rgmod.session_html({"n": _lesson()}, None), "")
        self.assertEqual(rgmod.session_html({"n": _lesson()}, {}), "")

    def test_live_presence_renders(self):
        out = rgmod.session_html({"n": _lesson()},
                                 {"ann": {"done": 2, "at": "2020-01-02"}},
                                 {"n": 4})
        self.assertIn("id='readgroup'", out)
        self.assertIn("ann", out)
        self.assertIn("<ol>", out)
        self.assertIn("4 min", out)


class CallerEffectTest(unittest.TestCase):
    def test_module_page_legacy_without_presence(self):
        tmp, db, server, out = make_module("readgroup mod")
        h = handler_for(db)
        body = h.module_html(out["module_id"])
        self.assertNotIn("id='readgroup'", body)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{rgmod.STATUS_ANCHOR}'",
                      rgmod.section_html())
        e = rgmod.tour_entry()
        self.assertEqual(e["id"], "reading-group")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["anchor"], rgmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
