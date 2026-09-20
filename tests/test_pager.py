"""Lesson pager: next/previous card nav per lesson article (I-8)."""
import unittest

from groundwork import db as dbmod
from groundwork import pager as pagermod

from test_web import handler_for, make_module


def entries3():
    return [{"slug": "add", "name": "add"},
            {"slug": "total", "name": "total"},
            {"slug": "return", "name": "return"}]


def concepts_of(db, mid):
    con = dbmod.connect(db)
    try:
        return con.execute(
            "SELECT id AS cid, name FROM concepts"
            " WHERE module_id=? ORDER BY rowid", (mid,)).fetchall()
    finally:
        con.close()


class NeighborsTest(unittest.TestCase):
    def test_middle_has_both_sides(self):
        self.assertEqual(pagermod.neighbors(["a", "b", "c"], 1), (0, 2))

    def test_edges_have_one_side(self):
        self.assertEqual(pagermod.neighbors(["a", "b"], 0), (None, 1))
        self.assertEqual(pagermod.neighbors(["a", "b"], 1), (0, None))

    def test_empty_single_or_bad_index(self):
        self.assertEqual(pagermod.neighbors([], 0), (None, None))
        self.assertEqual(pagermod.neighbors(["a"], 0), (None, None))
        self.assertEqual(pagermod.neighbors(["a", "b"], 5), (None, None))
        self.assertEqual(pagermod.neighbors(["a", "b"], -1), (None, None))


class PagerHtmlTest(unittest.TestCase):
    def test_middle_links_both_neighbours_with_position(self):
        out = pagermod.pager_html(entries3(), 1)
        self.assertIn("class='lesson-pager'", out)
        self.assertIn("href='#lesson-add'", out)
        self.assertIn("href='#lesson-return'", out)
        self.assertIn("rel='prev'", out)
        self.assertIn("rel='next'", out)
        self.assertIn("Lesson 2 of 3", out)

    def test_first_renders_next_only(self):
        out = pagermod.pager_html(entries3(), 0)
        self.assertNotIn("rel='prev'", out)
        self.assertIn("href='#lesson-total'", out)
        self.assertIn("Lesson 1 of 3", out)

    def test_last_renders_prev_only(self):
        out = pagermod.pager_html(entries3(), 2)
        self.assertNotIn("rel='next'", out)
        self.assertIn("href='#lesson-total'", out)
        self.assertIn("Lesson 3 of 3", out)

    def test_first_flag_owns_tour_anchor(self):
        self.assertIn("id='pager'",
                      pagermod.pager_html(entries3(), 0, first=True))
        self.assertNotIn("id='pager'", pagermod.pager_html(entries3(), 1))

    def test_escapes_names(self):
        entries = [{"slug": "a", "name": "<b>bold</b>"},
                   {"slug": "b", "name": "plain"}]
        out = pagermod.pager_html(entries, 1)
        self.assertIn("&lt;b&gt;bold&lt;/b&gt;", out)
        self.assertNotIn("<b>bold</b>", out)

    def test_single_or_bad_index_renders_empty(self):
        self.assertEqual(
            pagermod.pager_html([{"slug": "a", "name": "a"}], 0), "")
        self.assertEqual(pagermod.pager_html([], 0), "")
        self.assertEqual(pagermod.pager_html(entries3(), 9), "")


class SectionSlugsTest(unittest.TestCase):
    def test_from_prefixed_concept_ids(self):
        rows = [{"cid": "mid123:calc.py:add", "name": "add"},
                {"cid": "mid123:helper", "name": "helper"}]
        got = pagermod.section_slugs(rows)
        self.assertEqual([e["slug"] for e in got],
                         ["calc-py-add", "helper"])
        self.assertEqual([e["name"] for e in got], ["add", "helper"])

    def test_pager_targets_match_module_sections(self):
        tmp, db, server, out = make_module("pager mod")
        h = handler_for(db)
        body = h.module_html(out["module_id"])
        rows = pagermod.section_slugs(
            concepts_of(db, out["module_id"]))
        self.assertTrue(rows)
        self.assertIn(f"id='lesson-{rows[0]['slug']}'", body)
        demo = ([{"slug": "prev-card", "name": "prev"}] + rows
                + [{"slug": "next-card", "name": "next"}])
        nav = pagermod.pager_html(demo, 0)
        self.assertIn(f"href='#lesson-{rows[0]['slug']}'", nav)


class StatusSectionTest(unittest.TestCase):
    def test_section_html_has_b6_anchor(self):
        out = pagermod.section_html()
        self.assertIn("id='status-b6-pager'", out)
        self.assertIn("groundwork/pager.py", out)


if __name__ == "__main__":
    unittest.main()
