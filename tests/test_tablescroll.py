"""Scrollable tables with sticky first column (I-92)."""
import unittest

from groundwork import db as dbmod
from groundwork import history as histmod
from groundwork import tablescroll as tmod

from test_web import make_module

WIDE = ("<table class='log'><tr><th>Skill</th><th>Acc</th>"
        "<th>Conf</th><th>Gap</th></tr>"
        "<tr><td>a</td><td>1</td><td>2</td><td>3</td></tr></table>")
NARROW = ("<table><tr><th>A</th><th>B</th></tr>"
          "<tr><td>1</td><td>2</td></tr></table>")


class ColumnCountTest(unittest.TestCase):
    def test_counts_first_row_cells(self):
        self.assertEqual(tmod.column_count(WIDE), 4)
        self.assertEqual(tmod.column_count(NARROW), 2)

    def test_unparseable_is_zero(self):
        self.assertEqual(tmod.column_count(""), 0)
        self.assertEqual(tmod.column_count("<p>no table</p>"), 0)
        self.assertEqual(tmod.column_count(None), 0)
        self.assertEqual(tmod.column_count(42), 0)

    def test_wrap_threshold(self):
        self.assertTrue(tmod.needs_wrap(WIDE))
        self.assertFalse(tmod.needs_wrap(NARROW))
        self.assertFalse(tmod.needs_wrap(""))
        self.assertFalse(tmod.needs_wrap(None))


class WrapTableTest(unittest.TestCase):
    def test_wide_table_gets_container(self):
        out = tmod.wrap_table(WIDE)
        self.assertIn('<div class="tscroll">', out)
        self.assertIn("<table", out)

    def test_narrow_table_untouched(self):
        self.assertEqual(tmod.wrap_table(NARROW), NARROW)

    def test_legacy_no_data_fallback(self):
        # Empty History (no reviews, no table) renders exactly as
        # before: no wrapper, no empty scroll region.
        self.assertEqual(tmod.wrap_table(""), "")
        self.assertEqual(tmod.wrap_table(None), None)

    def test_idempotent(self):
        once = tmod.wrap_table(WIDE)
        self.assertEqual(tmod.wrap_table(once), once)
        self.assertEqual(once.count('class="tscroll"'), 1)


class ScrollCssTest(unittest.TestCase):
    def test_container_scrolls(self):
        css = tmod.scroll_css()
        nospace = css.replace(" ", "")
        self.assertIn("overflow-x:auto", nospace)
        self.assertIn("max-width:100%", nospace)

    def test_first_column_sticks(self):
        css = tmod.scroll_css()
        nospace = css.replace(" ", "")
        self.assertIn("position:sticky", nospace)
        self.assertIn("left:0", nospace)
        self.assertIn("th:first-child", nospace)
        self.assertIn("td:first-child", nospace)
        # Stuck labels need a solid background or scrolled text
        # shows through.
        self.assertIn("background:var(--paper)", nospace)

    def test_raw_declarations_only(self):
        css = tmod.scroll_css()
        self.assertNotIn("<style", css.lower())

    def test_section_html_anchor(self):
        html = tmod.section_html()
        self.assertIn("id='status-b21-tablescroll'", html)
        self.assertIn("wrap_table", html)

    def test_tour_entry_shape(self):
        e = tmod.tour_entry()
        self.assertEqual(e, {
            "id": "scrollable-tables",
            "kind": "improvement",
            "title": "Scrollable tables",
            "blurb": "Wide tables pan sideways on phones with the first "
                     "column stuck — row labels stay visible while scrolling.",
            "path": "/status",
            "anchor": "status-b21-tablescroll",
        })

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "tablescroll.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


class HistoryCallerTest(unittest.TestCase):
    """Behavioral effect: History log tables ride in scroll containers."""

    def test_seeded_history_wraps_its_log_tables(self):
        tmp, db, server, out = make_module("tablescroll mod")
        dbmod.init_db(db)
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        html = histmod.history_html(db)
        # Coach, coverage-timeline, and last-14-days grids all wrap.
        self.assertEqual(html.count('<div class="tscroll">'), 3)
        self.assertIn("<table class='log'>", html)

    def test_empty_history_has_no_wrapper(self):
        # Legacy no-data fallback: no reviews, no table, no scroll region.
        tmp, db, server, out = make_module("tablescroll empty mod")
        dbmod.init_db(db)
        html = histmod.history_html(db)
        self.assertNotIn("tscroll", html)
        self.assertNotIn("<table", html)


if __name__ == "__main__":
    unittest.main()
