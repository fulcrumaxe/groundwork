"""Symbol-mention lesson links (I-104): mentions link to lessons."""
import unittest

from groundwork import lessons as lesmod
from groundwork import symlinks as symmod


def _index():
    return symmod.build_index([
        {"name": "grade", "module_id": "m1", "file": "calc.py", "line": 12},
        {"name": "render_levels", "module_id": "m2",
         "file": "lessons.py", "line": 14},
    ], "m1")


def _lesson(summary="grade totals its inputs."):
    return {"concept_id": "c", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1, "summary": summary,
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
            "how": ["Hands back `a + b`."], "worked": None}


class SymlinksUnitTest(unittest.TestCase):
    def test_slug_matches_lessons_scheme(self):
        self.assertEqual(symmod.slug("render_levels"),
                         lesmod.slug("render_levels"))
        self.assertEqual(symmod.slug(""), "lesson")

    def test_symbol_href_prefers_same_module_lesson_anchor(self):
        self.assertEqual(symmod.symbol_href("grade", "m1", _index()),
                         "/modules/m1#lesson-grade")

    def test_symbol_href_cross_module_points_at_owner(self):
        self.assertEqual(symmod.symbol_href("render_levels", "m1", _index()),
                         "/modules/m2#lesson-render-levels")

    def test_unknown_symbol_href_is_empty(self):
        self.assertEqual(symmod.symbol_href("nope", "m1", _index()), "")
        self.assertEqual(symmod.symbol_href("grade", "", _index()), "")
        self.assertEqual(symmod.symbol_href("grade", "m1", {}), "")

    def test_link_symbols_wraps_known_leaves_unknown(self):
        out = symmod.link_symbols("grade and frobnicate", _index(), "m1")
        self.assertIn("href='/modules/m1#lesson-grade'", out)
        self.assertIn("frobnicate", out)
        self.assertNotIn("frobnicate</a>", out)

    def test_link_symbols_skips_tags_and_existing_links(self):
        out = symmod.link_symbols("<a href='/x'>grade</a> grade", _index(), "m1")
        self.assertEqual(out.count("lesson-grade"), 1)

    def test_link_symbols_skips_glossary_spans(self):
        frag = ("<dfn class='gloss' tabindex='0' title='x'>grade</dfn> grade")
        out = symmod.link_symbols(frag, _index(), "m1")
        self.assertEqual(out.count("lesson-grade"), 1)

    def test_budget_caps_links(self):
        out = symmod.link_symbols("grade grade grade", _index(), "m1", budget=1)
        self.assertEqual(out.count("lesson-grade"), 1)

    def test_empty_index_returns_fragment_unchanged(self):
        frag = "grade totals"
        self.assertEqual(symmod.link_symbols(frag, {}, "m1"), frag)
        self.assertEqual(symmod.link_symbols(frag, None, "m1"), frag)

    def test_never_raises(self):
        for bad in (None, 123, ["x"], {"a": 1}):
            symmod.link_symbols(bad, _index(), "m1")
            symmod.link_symbols("grade", bad, "m1")
            symmod.build_index(bad)
            symmod.symbol_href(bad, "m1", _index())
        symmod.link_symbols("grade", _index(), None)

    def test_status_section_has_stable_anchor(self):
        self.assertIn(f"id='{symmod.STATUS_ANCHOR}'", symmod.section_html())

    def test_tour_entry_shape(self):
        e = symmod.tour_entry()
        self.assertEqual(e["kind"], "improvement")
        self.assertTrue(e["path"] and e["anchor"])


class SymlinksEffectTest(unittest.TestCase):
    def test_rendered_lesson_links_symbol_mentions(self):
        html_out = lesmod.render_levels(
            _lesson("grade totals; render_levels shows it."),
            0.0, 0, "auto", "/", symbols=_index(), sym_mid="m1")
        self.assertIn("class='symlink'", html_out)
        self.assertIn("/modules/m1#lesson-grade", html_out)
        self.assertIn("/modules/m2#lesson-render-levels", html_out)

    def test_rendered_lesson_leaves_unknown_symbols_alone(self):
        html_out = lesmod.render_levels(
            _lesson("frobnicate wanders."), 0.0, 0, "auto", "/",
            symbols=_index(), sym_mid="m1")
        self.assertNotIn("class='symlink'", html_out)
        self.assertIn("frobnicate", html_out)

    def test_legacy_no_index_path_pinned_byte_identical(self):
        base = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        self.assertEqual(
            lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/",
                                 symbols=None, sym_mid=""),
            base)
        self.assertEqual(
            lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/",
                                 symbols={}, sym_mid="m1"),
            base)


if __name__ == "__main__":
    unittest.main()
