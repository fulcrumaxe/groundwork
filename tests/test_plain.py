"""Plain mode: zero gamification over the same engine (F-140)."""
import unittest

from groundwork import emoji as emojimod
from groundwork import plain as plainmod
from groundwork import web as webmod
from test_web import handler_for, make_module


class NormalizeTest(unittest.TestCase):
    def test_one_enables(self):
        self.assertEqual(plainmod.normalize("1"), "1")
        self.assertEqual(plainmod.normalize(" 1 "), "1")
        self.assertTrue(plainmod.is_plain("1"))

    def test_anything_else_is_off(self):
        for bad in ("", "0", "2", "true", "on", "yes", None, 1, "  "):
            self.assertEqual(plainmod.normalize(bad), "")
            self.assertFalse(plainmod.is_plain(bad))


class CarryTest(unittest.TestCase):
    def test_appends_to_bare_path(self):
        self.assertEqual(plainmod.carry("/due", "1"), "/due?plain=1")

    def test_appends_with_ampersand(self):
        self.assertEqual(plainmod.carry("/due?mode=one", "1"),
                         "/due?mode=one&plain=1")

    def test_preserves_fragment(self):
        self.assertEqual(plainmod.carry("/modules/abc#lesson-add", "1"),
                         "/modules/abc?plain=1#lesson-add")

    def test_never_doubles_existing_plain(self):
        self.assertEqual(plainmod.carry("/due?plain=1", "1"), "/due?plain=1")

    def test_off_leaves_links_clean(self):
        self.assertEqual(plainmod.carry("/due", ""), "/due")
        self.assertIs(plainmod.carry_html("<a href='/due'>x</a>", ""), "<a href='/due'>x</a>")

    def test_external_and_fragments_untouched(self):
        for href in ("https://example.com/x", "//cdn/x.js",
                     "mailto:a@b.c", "#lesson-add", ""):
            self.assertEqual(plainmod.carry(href, "1"), href)

    def test_carry_html_rewrites_internal_only(self):
        raw = ("<a href='/due'>Due</a> "
               "<a href=\"/modules?sort=newest\">Lib</a> "
               "<a href='https://example.com/'>Ext</a>")
        out = plainmod.carry_html(raw, "1")
        self.assertIn("href='/due?plain=1'", out)
        self.assertIn('href="/modules?sort=newest&plain=1"', out)
        self.assertIn("href='https://example.com/'", out)


class ExitHrefTest(unittest.TestCase):
    def test_removes_flag_keeps_rest(self):
        self.assertEqual(plainmod.exit_href("/due?plain=1"), "/due")
        self.assertEqual(plainmod.exit_href("/due?plain=1&mode=one"),
                         "/due?mode=one")
        self.assertEqual(plainmod.exit_href("/due?mode=one&plain=1"),
                         "/due?mode=one")
        self.assertEqual(plainmod.exit_href("/due?plain=1#queue"), "/due#queue")

    def test_plain_path_and_hostile(self):
        self.assertEqual(plainmod.exit_href("/due"), "/due")
        self.assertEqual(plainmod.exit_href(None), "/")
        self.assertEqual(plainmod.exit_href(""), "/")


class GateTest(unittest.TestCase):
    def test_gate_keeps_off_drops_on(self):
        block = "<p id='mascot'>Momo</p>"
        self.assertEqual(plainmod.gate(block, ""), block)
        self.assertEqual(plainmod.gate(block, "bogus"), block)
        self.assertEqual(plainmod.gate(block, "1"), "")


class StripUnitTest(unittest.TestCase):
    def test_off_returns_input_untouched(self):
        raw = "<p id='mascot'>x</p><h2 id='bests'>y</h2><p>z</p>"
        self.assertIs(plainmod.strip_html(raw, ""), raw)
        self.assertIs(plainmod.strip_html(raw, "bogus"), raw)
        self.assertIs(plainmod.strip_html(None, "1"), None)

    def test_sections_spans_and_singles_go(self):
        raw = ("<section id='partytrick'><h2>Party trick</h2><p>x</p></section>"
               "<section id='quests'><h2>Unlock quests</h2><h3>n</h3></section>"
               "<section id='anniversary'><h2>Year</h2><p>x</p></section>"
               "<p id='mascot' class='mascot'>Momo</p>"
               "<p class='avatar-box' id='library-identity'><svg></svg></p>"
               "<span class='cbadge cbadge-star' style='--cb-hue:1'>loops</span>"
               "<span class='unlock-fx mo-reveal'>Unlocked - new</span>"
               "<p id='queue'>kept</p>")
        out = plainmod.strip_html(raw, "1")
        self.assertEqual(plainmod.stripped_ids(out), [])
        self.assertIn("<p id='queue'>kept</p>", out)

    def test_h2_sections_go_with_exact_bodies(self):
        raw = ("<h2 id='bests'>Personal bests</h2><p>mem prac skill</p>"
               "<h2 id='milestones'>Milestone moments</h2><ul><li>x</li></ul>"
               "<h2 id='endorsements'>Skill endorsements</h2><p>none</p>"
               "<h2 id='teaching-certificates'>Teaching certificates</h2>"
               "<p><a href='/modules/m'>s</a> - 1/2 owned, 1 to go.</p>"
               "<h2 id='teamchallenge'>Team challenges</h2>"
               "<p><small>Own together.</small></p><ul><li>x</li></ul>"
               "<h2 id='seasonal-event'>Owntober - own 5</h2><p>1 of 5</p>"
               "<h2 id='showcase'>Badge showcase</h2>"
               "<div class='showcase-tile'><span class='chip'>a</span></div>"
               "<h2 id='growth-rings-head'>Growth rings</h2>"
               "<div id='growth-rings'><svg></svg></div>"
               "<h2 id='knowledge-garden'>Knowledge garden</h2>"
               "<h3>repo</h3><p class='bed'><svg></svg></p>"
               "<h2 id='attempts'>Attempts</h2>")
        out = plainmod.strip_html(raw, "1")
        self.assertEqual(plainmod.stripped_ids(out), [])
        self.assertIn("<h2 id='attempts'>Attempts</h2>", out)

    def test_theme_and_wagers_special_endings(self):
        raw = ("<h2 id='theme-unlocks'>Theme unlocks</h2>"
               "<div class='theme-gallery'>"
               "<div class='theme-locked'><span>t</span></div></div>"
               "<script data-themes>(function(){})</script>"
               "<h3 id='status-wagers'>Friendly wagers</h3>"
               "<p class='wager-open'>you vs pal</p>"
               "<form class='wager-place' method='get' action='/reviews'>"
               "<button type='submit'>Bet coffee</button></form>"
               "<h2 id='week'>This week</h2>")
        out = plainmod.strip_html(raw, "1")
        self.assertEqual(plainmod.stripped_ids(out), [])
        self.assertIn("<h2 id='week'>This week</h2>", out)

    def test_keep_blocks_are_byte_identical(self):
        keep = ("<p id='calibration'>Calibration: accuracy 80%</p>"
                "<h2>Calibration coach</h2>"
                "<h2 id='coverage'>Coverage timeline</h2>"
                "<h2 id='antistreak'>Anti-streak pledge</h2>"
                "<h2 id='attempts'>Attempts</h2>"
                "<div id='queue'><article>card</article></div>")
        self.assertEqual(plainmod.strip_html(keep, "1"), keep)

    def test_notice_injected_once_after_main(self):
        raw = "<main id='main'><p id='queue'>q</p></main>"
        out = plainmod.strip_html(raw, "1", "/due")
        self.assertEqual(out.count("id='plain-mode'"), 1)
        self.assertIn("<a href='/due'>Show decorations</a>", out)


class StrippedIdsTest(unittest.TestCase):
    def test_reports_labels_present(self):
        raw = "<p id='mascot'>x</p><h2 id='bests'>y</h2><p>z</p>"
        self.assertEqual(plainmod.stripped_ids(raw), ["bests", "mascot"])

    def test_hostile_gives_empty(self):
        self.assertEqual(plainmod.stripped_ids(None), [])
        self.assertEqual(plainmod.stripped_ids(42), [])

    def test_catalog_covers_hint_families(self):
        for label in ("showcase", "bests", "knowledge-garden", "mascot",
                      "milestones", "quests", "status-wagers"):
            self.assertIn(label, plainmod.STRIPPED)


class PlainEffectTest(unittest.TestCase):
    def test_plain_caller_path_strips_decorations_same_engine(self):
        _t1, db1, s1, o1 = make_module("plain mode engine a")
        _t2, db2, s2, o2 = make_module("plain mode engine b")
        h1 = handler_for(db1)
        bodies = {"due": h1.due_html(),
                  "history": h1.history_html({}),
                  "module": h1.module_html(o1["module_id"])}
        seen_any = []
        for _name, body in bodies.items():
            full = webmod.page("T", body).decode()
            # Legacy fallback pinned: flag off is byte-identical.
            self.assertEqual(plainmod.strip_html(full, ""), full)
            self.assertEqual(plainmod.carry_html(full, ""), full)
            # Caller path, exactly as Handler._send will run it.
            on = plainmod.strip_html(
                plainmod.carry_html(full, "1"), "1", "/due")
            seen_any += plainmod.stripped_ids(full)
            self.assertEqual(plainmod.stripped_ids(on), [])
            self.assertIn("id='plain-mode'", on)
            self.assertIn("plain=1", on)
        # The test is not vacuous: the fixture really had decorations.
        self.assertNotEqual(seen_any, [])
        # Lists survive: queue, forms, lessons, attempts intact.
        due_full = webmod.page("T", bodies["due"]).decode()
        due_on = plainmod.strip_html(due_full, "1", "/due")
        self.assertIn("id='queue'", due_on)
        self.assertEqual(due_full.count("<article"), due_on.count("<article"))
        self.assertEqual(due_full.count("/review"), due_on.count("/review"))
        rev_full = webmod.page("T", bodies["history"]).decode()
        rev_on = plainmod.strip_html(rev_full, "1", "/reviews")
        self.assertEqual("id='antistreak'" in rev_full,
                         "id='antistreak'" in rev_on)
        self.assertEqual(rev_full.count("id='attempts'"),
                         rev_on.count("id='attempts'"))
        mod_full = webmod.page("T", bodies["module"]).decode()
        mod_on = plainmod.strip_html(mod_full, "1", "/modules/x")
        self.assertEqual(mod_full.count("id='lesson-"),
                         mod_on.count("id='lesson-"))
        # Same engine: twin DBs grade and schedule byte-identically,
        # because no grading/scheduling function takes the flag.
        d1 = s1.tool_list_due_reviews({"limit": 20})["due"]
        d2 = s2.tool_list_due_reviews({"limit": 20})["due"]
        self.assertTrue(d1 and d2)
        self.assertEqual([c["front"] for c in d1],
                         [c["front"] for c in d2])
        r1 = s1.submit_review(d1[0]["id"], "4", 3)
        r2 = s2.submit_review(d2[0]["id"], "4", 3)
        self.assertNotIn("error", r1)
        self.assertEqual(r1["result"], r2["result"])
        self.assertEqual(r1["next_due"][:16], r2["next_due"][:16])
        q1 = s1.tool_list_due_reviews({"limit": 20})["due"]
        q2 = s2.tool_list_due_reviews({"limit": 20})["due"]
        self.assertEqual([c["front"] for c in q1],
                         [c["front"] for c in q2])


class PlainShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = plainmod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["anchor"], plainmod.NOTICE_ANCHOR)

    def test_section_anchor(self):
        self.assertIn(f"id='{plainmod.STATUS_ANCHOR}'",
                      plainmod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(plainmod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
