"""Web IA tests: distinct pages, full nav, origin-aware results, lessons."""
import tempfile
import unittest
from pathlib import Path
from urllib.parse import urlencode

from groundwork import db as dbmod
from groundwork import mcp as mcplib
from groundwork import sched as schedmod
from groundwork import web as webmod


def make_module(summary="web ia module"):
    tmp = Path(tempfile.mkdtemp(prefix="gw-web-"))
    (tmp / "calc.py").write_text(
        "def add(a=2, b=3):\n    total = a + b\n    return total\n",
        encoding="utf-8")
    db = str(tmp / "web.db")
    server = mcplib.MCPServer(db)
    out = server.tool_create_learning_module(
        {"repo_path": str(tmp), "task_summary": summary})
    return tmp, db, server, out


def handler_for(db):
    h = webmod.Handler.__new__(webmod.Handler)
    h.db_path = db
    return h


def nav_links(html_text):
    """Nav links in header order."""
    head = html_text.split("<header", 1)[1].split("</header>", 1)[0]
    return head


class PageShellTest(unittest.TestCase):
    def test_nav_counts_render_when_provided(self):
        raw = webmod.page("T", "<p>x</p>", active="due", page_id="due",
                          counts={"due": 3, "modules": 2, "history": 9}).decode()
        self.assertIn("Due (3)", raw)
        self.assertIn("Modules (2)", raw)
        self.assertIn("History (9)", raw)
        plain = webmod.page("T", "<p>x</p>").decode()
        self.assertIn(">Due</a>", plain)

    def test_nav_counts_from_db(self):
        tmp, db, server, out = make_module("counts mod")
        h = handler_for(db)
        counts = h._nav_counts()
        self.assertEqual(set(counts), {"due", "modules", "history"})
        self.assertGreaterEqual(counts["modules"], 1)
        self.assertGreaterEqual(counts["due"], 0)

    def test_three_nav_links_with_active_state(self):
        for active in ("due", "modules", "history"):
            raw = webmod.page("T", "<p>x</p>", active=active,
                              page_id=active).decode()
            self.assertIn("href='/'", raw)
            self.assertIn("href='/modules'", raw)
            self.assertIn("href='/reviews'", raw)
            self.assertIn("aria-current=\"page\"", raw)
            self.assertIn(f"data-page='{active}'", raw)

    def test_lede_renders_when_given(self):
        raw = webmod.page("T", "<p>x</p>", lede="What next").decode()
        self.assertIn("What next", raw)


class DistinctPagesTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module()
        self.h = handler_for(self.db)

    def test_due_and_history_have_distinct_titles(self):
        due = webmod.page("Due", self.h.due_html()).decode()
        hist = webmod.page("History", self.h.history_html()).decode()
        self.assertIn("<h1>Due</h1>", due)
        self.assertIn("<h1>History</h1>", hist)
        self.assertNotEqual(due, hist)

    def test_due_links_to_modules_not_embeds_list(self):
        due = self.h.due_html()
        self.assertIn("/modules", due)
        self.assertNotIn("<h2>Modules</h2>", due)

    def test_anki_export_and_rss_feed(self):
        tsv = self.h.anki_tsv()
        rows = [l for l in tsv.splitlines() if l.strip()]
        self.assertGreater(len(rows), 0)
        for line in rows:
            self.assertEqual(len(line.split("\t")), 3)
        xml = self.h.feed_xml("http://x")
        self.assertIn("<rss version='2.0'>", xml)
        self.assertIn(f"/modules/{self.out['module_id']}", xml)
        self.assertIn("<pubDate>", xml)

    def test_diagnose_links_traceback_to_lessons(self):
        self.assertEqual(
            webmod._trace_symbols(
                'File "a.py", line 10, in main\n'
                'File "a.py", line 3, in add\n'
                "NameError: name 'helper' is not defined"),
            ["main", "add", "helper"])
        self.assertEqual(webmod._trace_symbols("no traceback here"), [])
        empty = self.h.diagnose_html()
        self.assertIn("Paste a Python traceback", empty)
        body = self.h.diagnose_html(
            'File "calc.py", line 1, in add\n'
            'File "calc.py", line 9, in nosuchfn\n'
            "NameError: name 'add' is not defined")
        self.assertIn("Study these, then diagnose", body)
        self.assertIn("/modules/", body)
        self.assertIn("Unknown here", body)

    def test_debt_meter_shows_unowned_repo(self):
        body = self.h.debt_html()
        self.assertIn("comprehension debt", body)
        self.assertIn("100% comprehension debt", body)
        self.assertIn("calc.py", body)
        shell = webmod.page("Debt", body, active="debt",
                            page_id="debt").decode()
        self.assertIn("href='/debt'", shell)
        self.assertIn("aria-current=\"page\"", shell)

    def test_modules_index_lists_new_module(self):
        body = self.h.modules_html()
        self.assertIn("web ia module", body)
        self.assertIn(f"/modules/{self.out['module_id']}", body)
        self.assertIn("concepts owned", body)

    def test_resume_points_at_first_unowned_lesson(self):
        body = self.h.modules_html()
        self.assertIn(">Resume</a>", body)
        self.assertIn("#lesson-", body)
        self.assertEqual(
            webmod._first_unowned({"a": (0, False), "b": (3, True)}, ["a", "b"]), "a")
        self.assertEqual(
            webmod._first_unowned({"a": (2, True), "b": (0, False)}, ["a", "b"]), "b")
        self.assertIsNone(
            webmod._first_unowned({"a": (2, True)}, ["a"]))

    def test_module_page_has_breadcrumb(self):
        body = self.h.module_html(self.out["module_id"])
        self.assertIn("/modules'>Modules</a>", body)
        self.assertIn("web ia module", body)

    def test_coverage_timeline_lists_module(self):
        con = dbmod.connect(self.db)
        try:
            card = con.execute("SELECT id FROM cards LIMIT 1").fetchone()
        finally:
            con.close()
        self.server.submit_review(card["id"], "5", 4)
        body = self.h.history_html()
        self.assertIn("Coverage timeline", body)
        self.assertIn("what it made", body)
        self.assertIn(f"/modules/{self.out['module_id']}", body)
        self.assertIn("web ia module", body)

    def test_calibration_coach_nudge(self):
        from groundwork import exercises as exmod
        con = dbmod.connect(self.db)
        try:
            card = con.execute(
                "SELECT id, exercise_type FROM cards LIMIT 1").fetchone()
            for _ in range(3):
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence)"
                    " VALUES(?,?,?)", (card["id"], 1, 5))
            con.commit()
        finally:
            con.close()
        bloom = exmod.TYPES[int(card["exercise_type"])][1]
        body = self.h.history_html()
        self.assertIn("Calibration coach", body)
        self.assertIn(f"on {bloom} exercises you feel", body)

    def test_calibration_coach_quiet_when_calibrated(self):
        rows = [("1", 5, 4), ("1", 5, 5), ("8", 5, 4)]
        body = webmod.calibration_coach(rows)
        self.assertIn("Calibration coach", body)
        self.assertNotIn("Coach:", body)
        self.assertEqual(webmod.calibration_coach([]), "")

    def test_history_lists_attempts_with_module_link(self):
        con = self.server._con()
        try:
            card = con.execute("SELECT id FROM cards LIMIT 1").fetchone()
        finally:
            con.close()
        self.server.submit_review(card["id"], "5", 4)
        body = self.h.history_html()
        self.assertIn("Calibration:", body)
        self.assertIn(f"/modules/{self.out['module_id']}", body)
        self.assertIn("Attempts", body)

    def test_history_empty_state_points_to_due(self):
        tmp2 = Path(tempfile.mkdtemp(prefix="gw-web-empty-"))
        db2 = str(tmp2 / "e.db")
        mcplib.MCPServer(db2)  # init only, no modules
        body = handler_for(db2).history_html()
        self.assertIn("No attempts yet", body)


class OriginFlowTest(unittest.TestCase):
    def test_answer_widget_carries_origin(self):
        card = {"id": "c1", "exercise_type": "8",
                "payload": '{"expected": "5"}'}
        w = webmod.answer_widget(card, 0, "/modules/abc")
        self.assertIn("name='origin' value='/modules/abc'", w)

    def test_safe_origin_rejects_offsite(self):
        self.assertEqual(webmod._safe_origin("/modules/abc"), "/modules/abc")
        self.assertEqual(webmod._safe_origin("/"), "/")
        self.assertEqual(webmod._safe_origin("https://evil/x"), "/")
        self.assertEqual(webmod._safe_origin("//evil"), "/")
        self.assertEqual(webmod._safe_origin("javascript:alert(1)"), "/")
        self.assertEqual(webmod._safe_origin(""), "/")

    def test_parse_review_form_round_trip(self):
        raw = urlencode({"answer": "5", "confidence": "4",
                         "origin": "/modules/abc"})
        answer, conf, origin = webmod._parse_review_form(raw)
        self.assertEqual((answer, conf, origin), ("5", 4, "/modules/abc"))

    def test_parse_review_form_defaults_without_origin(self):
        answer, conf, origin = webmod._parse_review_form("answer=5")
        self.assertEqual((answer, conf, origin), ("5", 3, "/due"))


class LessonPageTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("lesson history mod")
        self.h = handler_for(self.db)

    def test_submission_column_migrated_on_old_db(self):
        db = str(Path(tempfile.mkdtemp(prefix="gw-old-")) / "old.db")
        con = dbmod.connect(db)
        try:
            con.execute(
                "CREATE TABLE reviews (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " card_id TEXT NOT NULL, grade INTEGER NOT NULL,"
                " confidence INTEGER NOT NULL DEFAULT 3,"
                " reviewed_at TEXT NOT NULL DEFAULT '')")
            con.commit()
        finally:
            con.close()
        dbmod.init_db(db)
        con = dbmod.connect(db)
        try:
            cols = [r[1] for r in con.execute("PRAGMA table_info(reviews)").fetchall()]
        finally:
            con.close()
        self.assertIn("submission", cols)

    def test_submit_review_records_submission(self):
        con = self.server._con()
        try:
            card = con.execute(
                "SELECT id FROM cards WHERE exercise_type != '1' LIMIT 1").fetchone()
        finally:
            con.close()
        self.server.submit_review(card["id"], "not-the-output-xyz", 2)
        con = dbmod.connect(self.db)
        try:
            row = con.execute(
                "SELECT submission FROM reviews WHERE card_id=?",
                (card["id"],)).fetchone()
        finally:
            con.close()
        self.assertEqual(row["submission"], "not-the-output-xyz")

    def test_submission_appears_on_lesson_page(self):
        con = self.server._con()
        try:
            card = con.execute(
                "SELECT id FROM cards WHERE exercise_type != '1' LIMIT 1").fetchone()
        finally:
            con.close()
        self.server.submit_review(card["id"], "not-the-output-xyz", 2)
        body = self.h.module_html(self.out["module_id"])
        self.assertIn("not-the-output-xyz", body)
        self.assertIn("Past attempts (1)", body)

    def test_lesson_sections_group_study_practice_history(self):
        body = self.h.module_html(self.out["module_id"])
        con = dbmod.connect(self.db)
        try:
            n = con.execute(
                "SELECT COUNT(*) FROM concepts WHERE module_id=?",
                (self.out["module_id"],)).fetchone()[0]
        finally:
            con.close()
        self.assertGreater(n, 0)
        self.assertEqual(body.count("<section id='lesson-"), n)
        self.assertIn("In this module:", body)
        self.assertIn("Practice</h3>", body)
        self.assertIn("No attempts yet", body)

    def test_bloom_ladder_lights_up(self):
        body = self.h.module_html(self.out["module_id"])
        self.assertIn("class='ladder'", body)
        self.assertIn("Highest demonstrated: none yet", body)
        con = dbmod.connect(self.db)
        try:
            card = con.execute(
                "SELECT id, concept_id, exercise_type FROM cards LIMIT 1"
            ).fetchone()
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES(?,?,?)", (card["id"], 5, 4))
            con.commit()
            reached = webmod._bloom_reached(con, self.out["module_id"])
        finally:
            con.close()
        from groundwork import exercises as exmod
        want = webmod.BLOOM_RUNGS.index(exmod.TYPES[int(card["exercise_type"])][1])
        self.assertEqual(reached[card["concept_id"]], want)
        body = self.h.module_html(self.out["module_id"])
        self.assertIn("class='on'", body)

    def test_concept_status_chip(self):
        body = self.h.module_html(self.out["module_id"])
        self.assertIn("<span class='chip'>New</span>", body)
        self.assertEqual(webmod._concept_status(False, 0, False), "New")
        self.assertEqual(webmod._concept_status(False, 3, False), "Learning")
        self.assertEqual(webmod._concept_status(False, 3, True), "Owned")
        self.assertEqual(webmod._concept_status(True, 3, True), "Stale")
        # Same-day fluency alone never owns: a pass on the first visit
        # is still Learning.
        self.assertEqual(webmod._concept_status(False, 1, False), "Learning")
        self.assertTrue(webmod._slug("mcp.py:MCPServer.submit_review").startswith("mcp-py"))

    def test_owned_needs_spaced_modify_pass(self):
        con = dbmod.connect(self.db)
        try:
            con.execute(
                "INSERT INTO modules(id, repo) VALUES('m-owned','r')")
            con.execute(
                "INSERT INTO concepts(id, module_id, name)"
                " VALUES('m-owned:c','m-owned','c')")
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type)"
                " VALUES('card-o','m-owned:c','19')")
            self.assertEqual(webmod._owned_map(con, "m-owned"),
                             {"m-owned:c": (0, False)})
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES('card-o',5,4)")
            self.assertEqual(webmod._owned_map(con, "m-owned")["m-owned:c"],
                             (1, False))
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES('card-o',5,4)")
            self.assertEqual(webmod._owned_map(con, "m-owned")["m-owned:c"],
                             (2, True))
            # Recall passes alone never own, however repeated.
            con.execute(
                "INSERT INTO concepts(id, module_id, name)"
                " VALUES('m-owned:r','m-owned','r')")
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type)"
                " VALUES('card-r','m-owned:r','1')")
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES('card-r',5,4)")
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence)"
                " VALUES('card-r',5,4)")
            self.assertEqual(webmod._owned_map(con, "m-owned")["m-owned:r"],
                             (2, False))
            con.rollback()
        finally:
            con.close()


class StyleSignalsTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("style signals mod")
        self.h = handler_for(self.db)

    def test_due_marks_first_card_up_next(self):
        body = self.h.due_html()
        self.assertIn("Up next", body)
        self.assertIn("<article class='next'>", body)
        self.assertEqual(body.count("Up next"), 1)

    def test_due_queue_position_and_difficulty(self):
        body = self.h.due_html()
        n = body.count("<article")
        self.assertGreater(n, 0)
        self.assertIn(f"Card 1 of {n}", body)
        self.assertIn(f"Card {n} of {n}", body)
        self.assertIn("Difficulty", body)
        self.assertEqual(webmod._difficulty_dots(0.0).count("●"), 1)
        self.assertEqual(webmod._difficulty_dots(1.0).count("●"), 5)
        self.assertEqual(webmod._difficulty_dots(0.6).count("●"), 3)
        self.assertIn("Difficulty 3/5", webmod._difficulty_dots(0.6))

    def test_module_progress_bar_and_sticky_toc(self):
        body = self.h.module_html(self.out["module_id"])
        self.assertIn("class='toc'", body)
        self.assertIn("concepts owned", body)
        self.assertIn("data-page", webmod.page("M", body, page_id="modules").decode())

    def test_result_nav_returns_to_origin(self):
        same = webmod.result_nav("/modules/abc", "abc")
        self.assertIn("Continue where you left off", same)
        self.assertNotIn("Back to module", same)
        other = webmod.result_nav("/", "abc")
        self.assertIn("/modules/abc", other)

    def test_give_up_path_and_due_why(self):
        card = {"id": "c9", "exercise_type": "8",
                "payload": '{"expected": "5"}'}
        w = webmod.answer_widget(card)
        self.assertIn("Give up", w)
        self.assertIn("name='confidence' value='1'", w)
        why = webmod._due_why({"due": "2001-01-01T00:00:00Z",
                               "stability": 2.5, "lapses": 1})
        self.assertIn("why due?", why)
        self.assertIn("overdue", why)
        self.assertIn("lapses 1", why)
        self.assertIn("why due?", self.h.due_html())

    def test_confidence_pills_and_global_js(self):
        pills = webmod._confidence()
        self.assertEqual(pills.count("type='radio'"), 5)
        self.assertIn("value='3' checked", pills)
        shell = webmod.page("T", "<p>x</p>").decode()
        for marker in ("gw-draft", "clipboard", "ctrlKey", "copybtn", "conf-group"):
            self.assertIn(marker, shell)

    def test_links_never_purple_and_actions_are_buttons(self):
        css = webmod.CSS.lower()
        self.assertNotIn("purple", css)
        self.assertIn("a:visited", webmod.CSS)
        self.assertIn("a.btn", webmod.CSS)
        self.assertIn("class='btn'", webmod.result_nav("/", "abc"))
        self.assertIn("class='btn'", self.h.due_html())

    def test_render_result_verdict_and_due_left(self):
        body = webmod.render_result(True, "nice", "because", "tomorrow",
                                    "/", "abc", 3)
        self.assertIn("verdict ok", body)
        self.assertIn("3 more cards due", body)
        solo = webmod.render_result(False, "try again", "because", "soon",
                                    "/", "abc", 1)
        self.assertIn("verdict stale", solo)
        self.assertIn("1 more card due", solo)
        empty = webmod.render_result(True, "nice", "because", "tomorrow",
                                     "/", "abc", 0)
        self.assertNotIn("more card", empty)


class ProjectsPageTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("proj mod")
        self.h = handler_for(self.db)

    def test_projects_lists_repo_with_progress(self):
        body = self.h.projects_html()
        self.assertIn("id='projects'", body)
        self.assertIn(str(self.tmp), body)
        self.assertIn("/modules?repo=", body)

    def test_modules_filters_by_repo(self):
        con = dbmod.connect(self.db)
        try:
            got = con.execute("SELECT repo FROM modules LIMIT 1").fetchone()
        finally:
            con.close()
        repo = got["repo"]
        body = self.h.modules_html(repo)
        self.assertIn("Projects</a>", body)
        self.assertIn("id='library'", body)
        missing = self.h.modules_html("/no/such/repo")
        self.assertIn("No modules for this project yet", missing)
        self.assertNotIn("id='library'", missing)

    def test_due_moved_off_root(self):
        self.assertIn("id='queue'", self.h.due_html())
        shell = webmod.page("Projects", self.h.projects_html(),
                            active="projects", page_id="projects").decode()
        self.assertIn("aria-current=\"page\"", shell)
        self.assertIn("href='/due'", shell)


class RelativeTimesTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("times mod")
        self.h = handler_for(self.db)

    def _ago(self, **kw):
        import datetime
        return schedmod.iso(schedmod.utcnow() -
                            datetime.timedelta(**kw))

    def test_buckets(self):
        self.assertIn("just now", webmod._rel_time(self._ago(seconds=10)))
        self.assertIn("30m ago", webmod._rel_time(self._ago(minutes=30)))
        self.assertIn("5h ago", webmod._rel_time(self._ago(hours=5)))
        self.assertIn("3d ago", webmod._rel_time(self._ago(days=3)))
        old = webmod._rel_time(self._ago(days=40))
        self.assertIn("<time datetime=", old)
        self.assertNotIn("ago", old)

    def test_bad_input_still_renders(self):
        self.assertIn("<time datetime=", webmod._rel_time("not-a-date"))
        self.assertIn("<time datetime=", webmod._rel_time(""))

    def test_history_attempts_use_relative_times(self):
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        self.server.submit_review(card["id"], "5", 4)
        body = self.h.history_html()
        self.assertIn("id='timestamps'", body)
        self.assertIn("<time datetime=", body)
        self.assertIn("just now", body)


class ModuleSortTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("first mod")
        self.server.tool_create_learning_module(
            {"repo_path": str(self.tmp), "task_summary": "second mod"})
        self.h = handler_for(self.db)

    def test_toggle_present_with_newest_default(self):
        body = self.h.modules_html()
        self.assertIn("id='sort'", body)
        self.assertIn("<b>Newest</b>", body)
        self.assertIn("sort=oldest", body)

    def test_oldest_reverses_order(self):
        new = self.h.modules_html()
        old = self.h.modules_html("", "oldest")
        self.assertLess(new.index("second mod"), new.index("first mod"))
        self.assertLess(old.index("first mod"), old.index("second mod"))
        self.assertIn("<b>Oldest</b>", old)

    def test_bad_sort_falls_back_to_newest(self):
        body = self.h.modules_html("", "random")
        self.assertIn("<b>Newest</b>", body)


class MemoryStrengthTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("memory mod")
        self.h = handler_for(self.db)

    def test_due_cards_show_memory_bar(self):
        body = self.h.due_html()
        self.assertIn("id='memory'", body)
        self.assertIn("Memory strength", body)
        self.assertIn("class='bar'", body)

    def test_zero_stability_renders_empty_bar(self):
        self.assertIn("width:0%", webmod._memory_bar({}))

    def test_garbage_stability_renders_nothing(self):
        self.assertEqual(webmod._memory_bar({"stability": "high"}), "")


if __name__ == "__main__":
    unittest.main()
