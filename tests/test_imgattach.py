"""Image attachments in concept notes (I-130)."""
import json
import unittest

from groundwork import db as dbmod
from groundwork import imgattach as iamod

from test_web import handler_for, make_module


class CleanAttachmentTest(unittest.TestCase):
    def test_relative_screenshot_ok(self):
        got = iamod.clean_attachment("shots/board1.png")
        self.assertEqual(got["src"], "shots/board1.png")
        self.assertTrue(got["alt"])

    def test_dict_with_caption(self):
        got = iamod.clean_attachment({"src": "a.jpg", "alt": "Board",
                                      "caption": "Sprint sketch"})
        self.assertEqual(got["caption"], "Sprint sketch")

    def test_rejects_scripts_and_svg(self):
        self.assertIsNone(iamod.clean_attachment("javascript:alert(1)"))
        self.assertIsNone(iamod.clean_attachment("pic.svg"))
        self.assertIsNone(iamod.clean_attachment(""))
        self.assertIsNone(iamod.clean_attachment(None))
        self.assertIsNone(iamod.clean_attachment(42))

    def test_rejects_absolute_and_parent_paths(self):
        self.assertIsNone(iamod.clean_attachment("/etc/passwd.png"))
        self.assertIsNone(iamod.clean_attachment("../secret.png"))

    def test_https_with_ext_ok(self):
        got = iamod.clean_attachment("https://x.example/s.png")
        self.assertTrue(got["src"].startswith("https://"))


class ImagesInTextTest(unittest.TestCase):
    def test_markdown_ref_extracted(self):
        shots = iamod.images_in_text("see ![board](shots/b.png) for flow")
        self.assertEqual(len(shots), 1)
        self.assertEqual(shots[0]["alt"], "board")

    def test_non_image_link_ignored(self):
        self.assertEqual(iamod.images_in_text("see [docs](a.svg)"), [])
        self.assertEqual(iamod.images_in_text(None), [])
        self.assertEqual(iamod.images_in_text(42), [])


class AttachmentsInTest(unittest.TestCase):
    def test_frame_list_plus_note_scan(self):
        lesson = {"concept_id": "m:add", "name": "add",
                  "attachments": ["shots/a.png"]}
        notes = {"m:add": "whiteboard ![w](shots/w.jpg)"}
        shots = iamod.attachments_in(lesson, notes)
        self.assertEqual([s["src"] for s in shots],
                         ["shots/a.png", "shots/w.jpg"])

    def test_name_key_fallback(self):
        shots = iamod.attachments_in({"name": "add"},
                                     {"add": "![x](i.gif)"})
        self.assertEqual(len(shots), 1)

    def test_why_note_scanned_at_render_time(self):
        # The raw notes mapping exists only at creation; at render
        # time notes survive as the lesson's why_note string.
        shots = iamod.attachments_in(
            {"concept_id": "m:add", "name": "add",
             "why_note": "see ![w](shots/w.jpg) for the flow"})
        self.assertEqual([s["src"] for s in shots], ["shots/w.jpg"])

    def test_capped_and_hostile_safe(self):
        lesson = {"attachments": [f"s{i}.png" for i in range(20)]}
        self.assertEqual(len(iamod.attachments_in(lesson)),
                         iamod.MAX_ATTACHMENTS)
        self.assertEqual(iamod.attachments_in(None), [])
        self.assertEqual(iamod.attachments_in("nope", "nope"), [])


class FiguresHtmlTest(unittest.TestCase):
    def test_figures_escaped_and_lazy(self):
        body = iamod.figures_html({"attachments": [
            {"src": "shots/b.png", "alt": "A<B", "caption": "C&D"}]})
        self.assertIn("class='concept-shots'", body)
        self.assertIn("loading='lazy'", body)
        self.assertIn("A&lt;B", body)
        self.assertIn("<figcaption>C&amp;D</figcaption>", body)

    def test_empty_renders_nothing(self):
        self.assertEqual(iamod.figures_html({}), "")
        self.assertEqual(iamod.figures_html(None), "")
        self.assertEqual(
            iamod.figures_html({"attachments": ["evil.svg"]}), "")


def _inject(db, mid, mutate):
    con = dbmod.connect(db)
    try:
        row = con.execute("SELECT lessons FROM modules WHERE id=?",
                          (mid,)).fetchone()[0]
        lessons = json.loads(row or "[]")
        mutate(lessons[0])
        con.execute("UPDATE modules SET lessons=? WHERE id=?",
                    (json.dumps(lessons), mid))
        con.commit()
    finally:
        con.close()


class CallerEffectTest(unittest.TestCase):
    def test_module_html_renders_attached_figures(self):
        tmp, db, server, out = make_module("imgattach shots mod")
        mid = out["module_id"]
        _inject(db, mid,
                lambda lesson: lesson.update(
                    {"attachments": ["shots/board1.png"]}))
        body = handler_for(db).module_html(mid)
        self.assertIn("class='concept-shots'", body)
        self.assertIn("shots/board1.png", body)

    def test_module_html_renders_why_note_images(self):
        tmp, db, server, out = make_module("imgattach note mod")
        mid = out["module_id"]
        _inject(db, mid,
                lambda lesson: lesson.update(
                    {"why_note": "photo ![w](shots/w.jpg) shows it"}))
        body = handler_for(db).module_html(mid)
        self.assertIn("class='concept-shots'", body)
        self.assertIn("shots/w.jpg", body)

    def test_legacy_module_page_has_no_figures(self):
        tmp, db, server, out = make_module("imgattach legacy page")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("concept-shots", body)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{iamod.STATUS_ANCHOR}'",
                      iamod.section_html())
        e = iamod.tour_entry()
        self.assertEqual(e["id"], "concept-images")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], iamod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
