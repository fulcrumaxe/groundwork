"""Global header search: ranking, box, script, and wiring (I-2)."""
import unittest

from groundwork import search as searchmod
from groundwork import shortcuts as shortcutsmod


def rec(kind, title, detail="d", url="/u"):
    return {"kind": kind, "title": title, "url": url, "detail": detail}


class SearchRankTest(unittest.TestCase):
    def test_blank_query_matches_nothing(self):
        rows = [rec("concept", "Due queue")]
        self.assertEqual(searchmod.search(rows, ""), [])
        self.assertEqual(searchmod.search(rows, "   "), [])
        self.assertEqual(searchmod.search(rows, None), [])

    def test_concept_title_match(self):
        rows = [rec("concept", "Spaced repetition"), rec("concept", "Anki export")]
        hits = searchmod.search(rows, "spaced")
        self.assertEqual([h["title"] for h in hits], ["Spaced repetition"])

    def test_module_and_symbol_kinds_searchable(self):
        rows = [rec("module", "m-123", "photosynthesis"),
                rec("symbol", "render_search", "symbol function")]
        self.assertEqual(searchmod.search(rows, "m-123")[0]["kind"], "module")
        self.assertEqual(searchmod.search(rows, "render_search")[0]["kind"], "symbol")

    def test_case_insensitive_and_prefix_first(self):
        rows = [rec("concept", "xray memory"), rec("concept", "Memory strength")]
        hits = searchmod.search(rows, "MEMORY")
        self.assertEqual(hits[0]["title"], "Memory strength")

    def test_multi_token_requires_all(self):
        rows = [rec("concept", "Memory strength bars")]
        self.assertEqual(len(searchmod.search(rows, "memory bars")), 1)
        self.assertEqual(searchmod.search(rows, "memory missing"), [])

    def test_limit_respected(self):
        rows = [rec("concept", f"c{i}") for i in range(5)]
        self.assertEqual(len(searchmod.search(rows, "c", limit=2)), 2)


class SearchChromeTest(unittest.TestCase):
    def test_header_box_posts_to_search(self):
        body = searchmod.header_html()
        self.assertIn(f"id='{searchmod.INPUT_ID}'", body)
        self.assertIn("action='/search'", body)
        self.assertIn("name='q'", body)
        self.assertIn("<kbd>/</kbd>", body)

    def test_slash_script_guards_typing_and_ignores_overlays(self):
        js = searchmod.script_js()
        self.assertIn("site-search", js)
        self.assertIn("textarea", js)
        self.assertIn("isContentEditable", js)
        self.assertNotIn("shortcuts", js)  # `?` overlay untouched
        keys = [k for k, _, _ in shortcutsmod.SHORTCUTS]
        self.assertNotIn("/", keys)  # no clash with `?` or g-sequences

    def test_results_escape_and_empty_state(self):
        body = searchmod.results_html([rec("concept", "<b>x</b>")], "<b>x</b>")
        self.assertIn("search-results", body)
        self.assertNotIn("<b>x</b>", body)
        empty = searchmod.results_html([], "zzz")
        self.assertIn("search-empty", empty)
        self.assertIn("/modules", empty)

    def test_concept_rows_yield_symbol_records(self):
        rows = [{"id": "m:c1", "module_id": "m", "name": "f",
                 "kind": "function"}]
        kinds = {r["kind"] for r in searchmod.concepts_to_records(rows)}
        self.assertEqual(kinds, {"concept", "symbol"})

    def test_status_anchor(self):
        body = searchmod.section_html()
        self.assertIn("id='status-b6-search'", body)


if __name__ == "__main__":
    unittest.main()
