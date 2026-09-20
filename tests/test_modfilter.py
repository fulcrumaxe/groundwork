"""Module status filter tabs (I-19): classify / filter / tab bar."""
import unittest

from groundwork import modfilter as mfmod


class ClassifyTest(unittest.TestCase):
    def test_fully_owned(self):
        self.assertEqual("owned",
                         mfmod.classify({"owned": 3, "total": 3, "stale": 0}))

    def test_owned_clamped_above_total(self):
        self.assertEqual("owned",
                         mfmod.classify({"owned": 9, "total": 3, "stale": 0}))

    def test_partial_is_in_progress(self):
        self.assertEqual("in-progress",
                         mfmod.classify({"owned": 1, "total": 3, "stale": 0}))

    def test_unstarted_counts_as_in_progress(self):
        # owned == 0 with total > 0 is still in-progress: the tab must
        # never hide unstarted work.
        self.assertEqual("in-progress",
                         mfmod.classify({"owned": 0, "total": 3, "stale": 0}))

    def test_empty_module_is_in_progress_not_owned(self):
        # total == 0 must not read as owned via 0 >= 0.
        self.assertEqual("in-progress",
                         mfmod.classify({"owned": 0, "total": 0, "stale": 0}))

    def test_stale_wins_over_owned(self):
        self.assertEqual("stale",
                         mfmod.classify({"owned": 3, "total": 3, "stale": 1}))

    def test_stale_wins_over_progress(self):
        self.assertEqual("stale",
                         mfmod.classify({"owned": 1, "total": 4, "stale": 2}))

    def test_missing_fields_default_to_zero(self):
        self.assertEqual("in-progress", mfmod.classify({}))

    def test_non_dict_is_in_progress(self):
        self.assertEqual("in-progress", mfmod.classify(None))


class FilterTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"id": "a", "owned": 0, "total": 2, "stale": 0},  # in-progress
            {"id": "b", "owned": 2, "total": 2, "stale": 0},  # owned
            {"id": "c", "owned": 2, "total": 2, "stale": 1},  # stale
            {"id": "d", "owned": 1, "total": 3, "stale": 0},  # in-progress
        ]

    def test_all_returns_everything(self):
        self.assertEqual(self.rows, mfmod.filter_rows(self.rows, "all"))

    def test_unknown_status_falls_back_to_all(self):
        for bad in ("done", "", "OWNED", None):
            self.assertEqual(self.rows, mfmod.filter_rows(self.rows, bad),
                             msg=f"status={bad!r}")

    def test_each_tab(self):
        self.assertEqual(["a", "d"],
                         [r["id"] for r in mfmod.filter_rows(self.rows, "in-progress")])
        self.assertEqual(["b"],
                         [r["id"] for r in mfmod.filter_rows(self.rows, "owned")])
        self.assertEqual(["c"],
                         [r["id"] for r in mfmod.filter_rows(self.rows, "stale")])

    def test_counts_correct(self):
        self.assertEqual({"all": 4, "in-progress": 2, "owned": 1, "stale": 1},
                         mfmod.counts(self.rows))


class TabbarTest(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"id": "a", "owned": 0, "total": 2, "stale": 0},
            {"id": "b", "owned": 2, "total": 2, "stale": 0},
        ]

    def test_active_tab_marked_not_linked(self):
        body = mfmod.tabbar(self.rows, "owned")
        self.assertIn("<b aria-current='page'>Owned (1)</b>", body)
        self.assertNotIn("status=owned", body)

    def test_inactive_tabs_link_with_status_param(self):
        body = mfmod.tabbar(self.rows, "all")
        self.assertIn("<b aria-current='page'>All (2)</b>", body)
        self.assertIn("status=in-progress", body)
        self.assertIn("status=owned", body)
        self.assertIn("status=stale", body)

    def test_unknown_active_falls_back_to_all(self):
        body = mfmod.tabbar(self.rows, "bogus")
        self.assertIn("<b aria-current='page'>All (2)</b>", body)

    def test_repo_escaped_in_links(self):
        body = mfmod.tabbar(self.rows, "all", repo='a&b"<>')
        self.assertIn("repo=a%26b", body)
        self.assertNotIn('a&b"<>', body)

    def test_section_anchor(self):
        self.assertIn("id='status-b7-modfilter'", mfmod.section_html())


if __name__ == "__main__":
    unittest.main()
