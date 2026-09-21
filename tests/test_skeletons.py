"""Loading skeletons for module pages (I-81)."""
import re
import unittest

from groundwork import skeletons as skmod


def durations_ms(css):
    """Every (value, unit) duration in the CSS, normalized to ms."""
    out = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)\s*(ms|s)\b", css):
        val, unit = float(m.group(1)), m.group(2)
        out.append(val if unit == "ms" else val * 1000.0)
    return out


def text_content(html):
    return re.sub(r"<[^>]+>", "", html)


class SkeletonHtmlTest(unittest.TestCase):
    def test_structure_mirrors_module_page(self):
        html = skmod.skeleton_html()
        self.assertIn("sk-titlebar", html)  # title bar
        self.assertIn("class='bar", html)  # real progress-bar selectors
        self.assertIn("sk-titlebar", html)
        self.assertIn("sk-progress", html)
        self.assertEqual(html.count("sk-row'>"), 3)  # default 3 lesson rows

    def test_row_count_follows_argument(self):
        self.assertEqual(skmod.skeleton_html(rows=5).count("sk-row'>"), 5)
        self.assertEqual(skmod.skeleton_html(rows=1).count("sk-row'>"), 1)

    def test_rows_fail_closed_never_raise(self):
        for bad in (None, "many", 0, -2, 999, True, False, object()):
            html = skmod.skeleton_html(rows=bad)
            self.assertIsInstance(html, str)
            self.assertEqual(html.count("sk-row'>"), skmod.DEFAULT_ROWS)

    def test_aria_busy_parent_and_hidden_inner(self):
        html = skmod.skeleton_html()
        self.assertIn("aria-busy='true'", html)
        self.assertIn("aria-hidden='true'", html)
        busy_at = html.index("aria-busy")
        hidden_at = html.index("aria-hidden")
        self.assertLess(busy_at, hidden_at)

    def test_no_fake_content_readable_by_at(self):
        html = skmod.skeleton_html(rows=5)
        self.assertEqual(text_content(html).strip(), "")
        self.assertNotIn("lorem", html.lower())


class SkeletonCssTest(unittest.TestCase):
    def test_raw_declarations_only_no_style_tags(self):
        css = skmod.skeletons_css().lower()
        self.assertNotIn("<style", css)

    def test_braces_balanced_media_closes(self):
        # Regression (Batch 13): the trailing no-preference @media
        # once missed its closing brace (f-string }} emits one), which
        # swallowed every later stylesheet rule into its query.
        css = skmod.skeletons_css()
        self.assertEqual(css.count("{"), css.count("}"))
        self.assertTrue(css.rstrip().endswith("}"))

    def test_duration_budget_every_duration_within_300ms(self):
        css = skmod.skeletons_css()
        durs = durations_ms(css)
        self.assertTrue(durs)  # the gated pulse is present to measure
        for ms in durs:
            self.assertLessEqual(ms, 300)

    def test_no_shimmer_slide(self):
        css = skmod.skeletons_css().lower()
        self.assertNotIn("background-position", css)
        self.assertNotIn("shimmer", css)

    def test_reduced_motion_gate(self):
        css = skmod.skeletons_css().replace(" ", "")
        self.assertIn("prefers-reduced-motion", css)

    def test_reuses_page_tokens_and_progress_selectors(self):
        css = skmod.skeletons_css()
        self.assertIn("var(--paper)", css)
        self.assertIn(".bar", css)


class SectionAndTourTest(unittest.TestCase):
    def test_section_html_anchor(self):
        html = skmod.section_html()
        self.assertIn("id='status-b12-skeletons'", html)

    def test_tour_entry_shape(self):
        entry = skmod.tour_entry()
        self.assertEqual(entry, {
            "id": "loading-skeletons",
            "kind": "improvement",
            "title": "Loading skeletons",
            "blurb": "Module pages show a static placeholder shell — title, progress, lesson rows — while lessons generate.",
            "path": "/status",
            "anchor": "status-b12-skeletons",
        })

    def test_module_constraints(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "skeletons.py").read_text(encoding="utf-8")
        self.assertLessEqual(src.count("\n") + 1, 350)
        self.assertNotIn("from groundwork", src)
        self.assertNotIn("import groundwork", src)
        self.assertNotIn("sqlite", src.lower())


if __name__ == "__main__":
    unittest.main()
