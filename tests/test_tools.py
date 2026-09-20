"""Tool-call analytics (F-389): dispatch logs, Status aggregates."""
import unittest

from groundwork import db as dbmod
from groundwork import status as statusmod
from groundwork import tools as toolsmod

from test_web import make_module


class ToolCallsTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("tools mod")
        dbmod.init_db(self.db)

    def test_dispatch_logs_success_and_failure(self):
        self.server.dispatch("describe_tools", {})
        try:
            self.server.dispatch("nope_missing", {})
        except ValueError:
            pass
        out = toolsmod.section_html(self.db)
        self.assertIn("id='status-tools'", out)
        self.assertIn("describe_tools", out)
        self.assertIn("nope_missing", out)
        con = dbmod.connect(self.db)
        try:
            bad = con.execute(
                "SELECT ok FROM tool_calls WHERE method='nope_missing'"
                ).fetchone()[0]
        finally:
            con.close()
        self.assertEqual(bad, 0)

    def test_empty_state_has_anchor(self):
        import tempfile
        from groundwork import db as dbmod
        p = tempfile.mktemp(suffix=".db")
        dbmod.init_db(p)
        try:
            out = toolsmod.section_html(p)
        finally:
            import os
            os.unlink(p)
        self.assertIn("id='status-tools'", out)

    def test_status_page_carries_section(self):
        self.assertIn("status-tools", statusmod.page_html(self.db))


if __name__ == "__main__":
    unittest.main()
