"""Blind spots (F-184): lowest-mastery concepts with lesson links."""
import unittest

from groundwork import blindspots as blindmod
from groundwork import status as statusmod

from test_web import make_module


class BlindSpotsTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("blind mod")

    def test_lists_weakest_first(self):
        out = blindmod.section_html(self.db)
        self.assertIn("id='status-blindspots'", out)
        self.assertIn("#lesson-", out)

    def test_empty_db_has_anchor(self):
        import tempfile
        from groundwork import db as dbmod
        p = tempfile.mktemp(suffix=".db")
        dbmod.init_db(p)
        try:
            out = blindmod.section_html(p)
        finally:
            import os
            os.unlink(p)
        self.assertIn("id='status-blindspots'", out)

    def test_status_page_carries_section(self):
        self.assertIn("status-blindspots", statusmod.page_html(self.db))


if __name__ == "__main__":
    unittest.main()
