"""Modules-index pagination (I-20): server-side page links, 50 per page."""
import unittest

from groundwork import modpages as mod


class PaginateTest(unittest.TestCase):
    def test_empty_list_is_one_empty_page(self):
        info = mod.paginate([], 1)
        self.assertEqual(info["pages"], 1)
        self.assertEqual(info["page"], 1)
        self.assertEqual(info["items"], [])
        self.assertEqual((info["start"], info["end"]), (0, 0))

    def test_exact_multiple_pages(self):
        items = list(range(100))
        first = mod.paginate(items, 1)
        second = mod.paginate(items, 2)
        self.assertEqual(first["pages"], 2)
        self.assertEqual(first["items"], list(range(50)))
        self.assertEqual(second["items"], list(range(50, 100)))
        self.assertEqual((second["start"], second["end"]), (51, 100))

    def test_partial_last_page(self):
        info = mod.paginate(list(range(123)), 3)
        self.assertEqual(info["pages"], 3)
        self.assertEqual((info["start"], info["end"]), (101, 123))

    def test_clamp_page_zero_to_first(self):
        info = mod.paginate(list(range(60)), 0)
        self.assertEqual(info["page"], 1)
        self.assertEqual(info["items"], list(range(50)))

    def test_clamp_huge_page_to_last(self):
        info = mod.paginate(list(range(60)), 999)
        self.assertEqual(info["page"], 2)
        self.assertEqual(info["items"], list(range(50, 60)))

    def test_garbage_page_falls_back_to_first(self):
        for raw in ("abc", None, "2.5", "", True):
            with self.subTest(raw=raw):
                self.assertEqual(mod.paginate(list(range(60)), raw)["page"], 1)

    def test_per_page_guard(self):
        info = mod.paginate(list(range(10)), 1, per_page=0)
        self.assertEqual(info["per_page"], mod.PAGE_SIZE)
        self.assertEqual(info["items"], list(range(10)))


class PagerHtmlTest(unittest.TestCase):
    def test_single_page_renders_no_nav(self):
        self.assertEqual(mod.pager_html(50, 1), "")
        self.assertEqual(mod.pager_html(0, 1), "")

    def test_prev_next_and_current_mark(self):
        out = mod.pager_html(120, 2)
        self.assertIn("rel='prev'", out)
        self.assertIn("rel='next'", out)
        self.assertIn("aria-current='page'", out)
        self.assertIn("page=1", out.replace("&amp;", "&"))
        self.assertIn("page=3", out.replace("&amp;", "&"))

    def test_first_page_has_no_prev_last_has_no_next(self):
        self.assertNotIn("rel='prev'", mod.pager_html(120, 1))
        self.assertNotIn("rel='next'", mod.pager_html(120, 3))

    def test_query_params_preserved(self):
        out = mod.pager_html(120, 2, params={"sort": "oldest", "status": "owned"})
        flat = out.replace("&amp;", "&")
        self.assertIn("sort=oldest", flat)
        self.assertIn("status=owned", flat)

    def test_values_escaped(self):
        # urlencode percent-encodes markup, so no raw tag can survive.
        out = mod.pager_html(120, 1, params={"status": "<script>alert(1)</script>"})
        self.assertNotIn("<script>", out)
        self.assertIn("%3Cscript%3E", out)
        self.assertIn("&amp;", out)  # query separators escaped in hrefs

    def test_many_pages_use_ellipsis(self):
        out = mod.pager_html(50 * 20, 10)
        self.assertIn("pager-gap", out)


class SummaryHtmlTest(unittest.TestCase):
    def test_empty_summary(self):
        self.assertIn("Showing 0 of 0 modules", mod.summary_html(0, 1))

    def test_first_page_numbers(self):
        self.assertIn("Showing 1\u201350 of 123", mod.summary_html(123, 1))

    def test_last_page_numbers(self):
        self.assertIn("Showing 101\u2013123 of 123", mod.summary_html(123, 3))

    def test_singular_module(self):
        self.assertIn("Showing 1\u20131 of 1 module.", mod.summary_html(1, 1))

    def test_clamped_page_summary(self):
        self.assertIn("Showing 51\u201360 of 60", mod.summary_html(60, 999))


class SectionHtmlTest(unittest.TestCase):
    def test_anchor(self):
        self.assertIn("id='status-b7-modpages'", mod.section_html())


if __name__ == "__main__":
    unittest.main()
