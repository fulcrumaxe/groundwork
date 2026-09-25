"""See-it-in-the-real-file links and the jailed viewer (I-129)."""
import io
import os
import unittest

from groundwork import realfile as mod

from test_web import handler_for, make_module


def _get(h, path):
    h.path = path
    h.headers = {}
    h.rfile = io.BytesIO(b"")
    h._send = lambda data, code=200, ctype="text/html": setattr(
        h, "_captured", (data, code, ctype))
    h.do_GET()
    return h._captured


class LinkTest(unittest.TestCase):
    def test_link_shape(self):
        body = mod.file_link("calc.py", 3)
        self.assertIn("/file?path=calc.py&line=3#L3", body)
        self.assertIn("see it in the real file", body)
        self.assertNotIn("id='realfile'", body)

    def test_first_carries_anchor(self):
        self.assertIn("id='realfile'", mod.file_link("a.py", 1, True))

    def test_unusable_empty(self):
        for bad in ((None, 1), ("", 1), ("calc.py", 0), ("calc.py", -2),
                    ("calc.py", "x"), ("a\x00.py", 1)):
            self.assertEqual(mod.file_link(*bad), "")


class JailTest(unittest.TestCase):
    def test_traversal_refused(self):
        _tmp, db, _s, _o = make_module("realfile jail")
        root = os.path.dirname(os.path.abspath(db))
        for bad in ("../x.py", "/etc/passwd", "..", "a/../../b.py"):
            title, body = mod.page_html(root, bad, 1)
            self.assertEqual(title, "Not found")
            self.assertIn("outside the repo", body)

    def test_missing_refused(self):
        _tmp, db, _s, _o = make_module("realfile missing")
        root = os.path.dirname(os.path.abspath(db))
        title, body = mod.page_html(root, "nope.py", 1)
        self.assertEqual(title, "Not found")

    def test_binary_refused(self):
        _tmp, db, _s, _o = make_module("realfile binary")
        root = os.path.dirname(os.path.abspath(db))
        with open(os.path.join(root, "blob.bin"), "wb") as f:
            f.write(b"\x00\x01\x02binary")
        title, _body = mod.page_html(root, "blob.bin", 1)
        self.assertEqual(title, "Not found")

    def test_oversize_refused(self):
        _tmp, db, _s, _o = make_module("realfile big")
        root = os.path.dirname(os.path.abspath(db))
        with open(os.path.join(root, "big.py"), "w") as f:
            f.write("x = 1\n" * 60000)
        title, _body = mod.page_html(root, "big.py", 1)
        self.assertEqual(title, "Not found")

    def test_lines_anchored_and_target_lit(self):
        _tmp, db, _s, _o = make_module("realfile lines")
        root = os.path.dirname(os.path.abspath(db))
        title, body = mod.page_html(root, "calc.py", 2)
        self.assertIn("File: calc.py", title)
        self.assertIn("id='L1'", body)
        self.assertIn("id='L2' class='at'", body)
        self.assertIn("line 2 of", body)

    def test_hostile_never_raises(self):
        self.assertEqual(mod.lines_html(None), "")
        title, _body = mod.page_html(None, None, None)
        self.assertEqual(title, "Not found")


class CallerEffectTest(unittest.TestCase):
    def test_module_header_links_source(self):
        _tmp, db, _s, out = make_module("realfile caller")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("see it in the real file", body)
        self.assertIn("id='realfile'", body)
        self.assertIn("#L1", body)

    def test_file_route_serves_repo(self):
        _tmp, db, _s, _o = make_module("realfile route")
        data, code, _ctype = _get(handler_for(db),
                                  "/file?path=calc.py&line=2")
        self.assertEqual(code, 200)
        text = data.decode()
        self.assertIn("id='L2' class='at'", text)

    def test_file_route_jails(self):
        _tmp, db, _s, _o = make_module("realfile route jail")
        _data, code, _ctype = _get(handler_for(db),
                                   "/file?path=../x.py&line=1")
        self.assertEqual(code, 404)


if __name__ == "__main__":
    unittest.main()
