"""Buddy matching by repo overlap (F-126): opt-in, local only."""
import unittest

from test_web import handler_for, make_module

from groundwork import buddymatch as mod


ME = {"name": "Ann", "repos": ["calc", "web"],
      "concepts": ["add", "loops"]}
BO = {"name": "Bo", "repos": ["calc", "art"],
      "concepts": ["add", "color"]}
CY = {"name": "Cy", "repos": ["music"], "concepts": ["melody"]}


class ScoreTest(unittest.TestCase):
    def test_identical_profiles_score_one(self):
        self.assertEqual(mod.overlap_score(ME, dict(ME)), 1.0)

    def test_disjoint_profiles_score_zero(self):
        self.assertEqual(mod.overlap_score(ME, CY), 0.0)

    def test_partial_overlap_between(self):
        score = mod.overlap_score(ME, BO)
        self.assertGreater(score, 0.0)
        self.assertLess(score, 1.0)

    def test_empty_union_is_zero_not_nan(self):
        self.assertEqual(mod.jaccard(set(), set()), 0.0)
        self.assertEqual(mod.overlap_score({}, {}), 0.0)

    def test_hostile_never_raises(self):
        self.assertEqual(mod.overlap_score(None, "nope"), 0.0)
        self.assertEqual(mod.jaccard(None, None), 0.0)
        self.assertEqual(mod.clean_profile("nope")["name"], "")
        self.assertEqual(mod.clean_profile({"repos": 42})["repos"], set())

    def test_comma_string_splits(self):
        self.assertEqual(mod._str_set("calc, web"), {"calc", "web"})


class MatchTest(unittest.TestCase):
    def test_ranks_best_first_with_shared(self):
        ranked = mod.match_buddies(ME, [CY, BO])
        self.assertEqual([r[0] for r in ranked], ["Bo"])
        name, score, repos, concepts = ranked[0]
        self.assertIn("calc", repos)
        self.assertIn("add", concepts)

    def test_skips_self_and_nameless(self):
        ranked = mod.match_buddies(ME, [dict(ME), {"repos": ["calc"]}, BO])
        self.assertEqual([r[0] for r in ranked], ["Bo"])

    def test_respects_limit(self):
        pals = [{"name": f"P{i}", "repos": ["calc"],
                 "concepts": ["add"]} for i in range(8)]
        self.assertLessEqual(len(mod.match_buddies(ME, pals, limit=3)), 3)

    def test_hostile_profiles_give_empty(self):
        self.assertEqual(mod.match_buddies(ME, "nope"), [])
        self.assertEqual(mod.match_buddies(None, None), [])


class HtmlTest(unittest.TestCase):
    def test_opt_out_renders_nothing(self):
        self.assertEqual(mod.match_html(ME, [BO]), "")
        self.assertEqual(mod.match_html(ME, [BO], opt_in=False), "")

    def test_no_overlap_renders_nothing(self):
        self.assertEqual(mod.match_html(ME, [CY], opt_in=True), "")

    def test_opt_in_renders_ranked_escaped(self):
        evil = {"name": "<i>Bo</i>", "repos": ["calc"], "concepts": ["add"]}
        body = mod.match_html(ME, [evil], opt_in=True)
        self.assertIn("buddy-match", body)
        self.assertIn("calc", body)
        self.assertNotIn("<i>Bo</i>", body)

    def test_hostile_never_raises(self):
        self.assertEqual(mod.match_html(None, None, opt_in=True), "")

    def test_entry_form_shape(self):
        form = mod.entry_html("/modules/m")
        self.assertIn("buddy-match-entry", form)
        self.assertIn("name='buddymatch'", form)
        self.assertIn("name='bmatch_repos'", form)
        self.assertIn("name='bmatch_concepts'", form)
        self.assertIn("/modules/m", form)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_default_page_carries_entry_but_no_list(self):
        _tmp, db, _s, out = make_module("buddymatch caller")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("buddy-match-entry", body)
        self.assertNotIn("Buddies by repo overlap", body)

    def test_opt_in_with_shared_repo_ranks_buddy(self):
        tmp, db, _s, out = make_module("buddymatch scored")
        h = handler_for(db)
        body = h.module_html(
            out["module_id"], buddies=["Ann", "Bo"], match_opt_in=True,
            match_repos=[str(tmp)], match_concepts=["zzz-no-concept"])
        self.assertIn("Buddies by repo overlap", body)
        self.assertIn("Bo", body)

    def test_opt_in_without_overlap_renders_nothing(self):
        _tmp, db, _s, out = make_module("buddymatch empty")
        h = handler_for(db)
        body = h.module_html(
            out["module_id"], buddies=["Ann", "Bo"], match_opt_in=True,
            match_repos=["no-such-repo"], match_concepts=["zzz-no-concept"])
        self.assertNotIn("Buddies by repo overlap", body)


if __name__ == "__main__":
    unittest.main()
