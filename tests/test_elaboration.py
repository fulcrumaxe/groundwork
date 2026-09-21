"""Elaboration drills (F-59): partner picking, fail-closed, escaping."""
import unittest

from groundwork import elaboration as elmod


def _c(name, repo="", summary=""):
    return {"name": name, "repo": repo, "summary": summary}


class ElaborationDrillTest(unittest.TestCase):
    def test_picks_two_highest_overlap_partners(self):
        new = _c("retry queue", repo="web", summary="backoff retry worker")
        owned = [
            _c("retry worker", repo="web", summary="backoff retry jobs"),
            _c("garden stages", repo="web", summary="seed sprout tree"),
            _c("backoff policy", repo="cli", summary="backoff delay retry"),
        ]
        drill = elmod.elaboration_drill(new, owned)
        self.assertEqual(drill["concept"], "retry queue")
        self.assertEqual(len(drill["partners"]), 2)
        self.assertIn("retry worker", drill["partners"])
        self.assertIn("backoff policy", drill["partners"])
        self.assertIn("retry queue", drill["prompt"])

    def test_repo_bonus_wins_and_ties_break_alphabetically(self):
        new = _c("alpha", repo="web", summary="zzz")
        owned = [
            _c("zebra", repo="other", summary="zzz"),
            _c("apple", repo="web", summary="zzz"),
            _c("mango", repo="web", summary="zzz"),
        ]
        drill = elmod.elaboration_drill(new, owned)
        self.assertEqual(drill["partners"], ["apple", "mango"])

    def test_fewer_than_two_owned_study_first_never_raises(self):
        for bad_owned in ([], [_c("only one")], None, "nope"):
            drill = elmod.elaboration_drill(_c("new thing"), bad_owned)
            self.assertEqual(drill["partners"], [])
            self.assertIn("study", drill["prompt"].lower())
        for bad_new in (None, {}, [], _c("")):
            drill = elmod.elaboration_drill(bad_new, [])
            self.assertEqual(drill["partners"], [])
            self.assertTrue(drill["prompt"])

    def test_drill_html_escapes_names(self):
        drill = elmod.elaboration_drill(
            _c("<script>alert(1)</script>"),
            [_c("<b>p1</b>"), _c("<img src=x onerror=y>")])
        html = elmod.drill_html(drill)
        self.assertNotIn("<script>", html)
        self.assertNotIn("<b>p1</b>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;b&gt;", html)

    def test_section_html_anchor_and_tour_entry_shape(self):
        self.assertIn("id='status-b12-elaboration'", elmod.section_html())
        entry = elmod.tour_entry()
        self.assertEqual(entry, {
            "id": "elaboration-drills", "kind": "feature",
            "title": "Elaboration drills",
            "blurb": "Connect a new concept to two you already own — shared tokens pick the partners.",
            "path": "/status", "anchor": "status-b12-elaboration"})

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "elaboration.py").read_text(encoding="utf-8")
        for marker in ("[REDACTED]", "TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
