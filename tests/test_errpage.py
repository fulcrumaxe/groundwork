"""Chrome error pages (I-83): 500s inside page chrome, no tracebacks."""
import unittest

from groundwork import errpage as errmod


class ErrpageTest(unittest.TestCase):
    def test_body_links_somewhere_real(self):
        body = errmod.server_error_html("ValueError")
        for href in ("/due", "/", "/modules", "/reviews", "/status"):
            self.assertIn(f"href='{href}'", body)
        self.assertIn("ValueError", body)
        self.assertIn("server-error", body)

    def test_no_traceback_anatomy_ever(self):
        evil = ("Traceback (most recent call last):\n"
                '  File "/app/groundwork/web.py", line 414, in do_GET\n'
                "secret=db-password")
        for kind in (evil, "<script>alert(1)</script>", "", None, 42,
                     "x" * 200):
            body = errmod.server_error_html(kind)
            for frag in errmod._FORBIDDEN:
                self.assertNotIn(frag, body)
            self.assertNotIn("<script", body)
            self.assertNotIn("secret=db-password", body)

    def test_ref_is_opaque_or_dropped(self):
        self.assertIn("abc-123", errmod.server_error_html("E", "abc-123"))
        body = errmod.server_error_html("E", "../../etc/passwd")
        self.assertNotIn("etc/passwd", body)
        self.assertNotIn("Reference", body)

    def test_safe_kind_fail_closed(self):
        self.assertEqual(errmod.safe_kind(ValueError("x")), "ValueError")
        self.assertEqual(errmod.safe_kind("KeyError"), "KeyError")
        for bad in ("", "a b", "x" * 200, None, 42, "<b>", "a/b"):
            self.assertEqual(errmod.safe_kind(bad), "Error")

    def test_renders_inside_page_chrome(self):
        from groundwork import web as webmod
        raw = webmod.page("Error", errmod.server_error_html("Boom"),
                          counts={"due": 0, "modules": 0, "tries": 0}) \
            .decode()
        self.assertIn("id='sitenav'", raw)
        self.assertIn("id='server-error'", raw)
        self.assertIn("site-footer", raw)

    def test_section_html_anchor(self):
        html = errmod.section_html()
        self.assertIn("id='status-b13-errpage'", html)
        self.assertIn("server_error_html", html)

    def test_tour_entry_shape(self):
        e = errmod.tour_entry()
        self.assertEqual(e, {
            "id": "error-pages",
            "kind": "improvement",
            "title": "Chrome error pages",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-errpage",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "errpage.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
