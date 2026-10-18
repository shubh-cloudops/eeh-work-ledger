"""Smoke tests for eeh.py. Run: python -m unittest -v"""
import os, subprocess, sys, tempfile, unittest

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "eeh.py")


class EEHTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.env = dict(os.environ, EEH_LEDGER=os.path.join(self.dir.name, "work-ledger.md"))
        self.run_eeh("init", "--name", "Test User", "--designation", "DevOps Engineer", "--hours", "09:30-18:30")

    def tearDown(self):
        self.dir.cleanup()

    def run_eeh(self, *args, ok=True):
        r = subprocess.run([sys.executable, SCRIPT, *args], env=self.env, cwd=self.dir.name,
                           capture_output=True, text=True)
        if ok:
            self.assertEqual(r.returncode, 0, r.stderr)
        return r

    def test_add_computes_minutes_and_confidence(self):
        out = self.run_eeh("add", "--date", "2026-10-01", "--start", "09:30", "--end", "11:00",
                           "--project", "Atlas", "--evidence", "https://example.com/pr/1", "--src", "git").stdout
        self.assertIn("E0001 2026-10-01 90m Atlas high", out)
        out = self.run_eeh("add", "--date", "2026-10-01", "--min", "30", "--project", "Atlas").stdout
        self.assertIn("30m Atlas low", out)

    def test_close_reports_gaps_and_blocks_second_close(self):
        self.run_eeh("add", "--date", "2026-10-01", "--start", "09:30", "--end", "12:00", "--project", "A")
        self.run_eeh("add", "--date", "2026-10-01", "--start", "13:00", "--end", "18:30", "--project", "A")
        out = self.run_eeh("close", "--date", "2026-10-01").stdout
        self.assertIn("total 480m", out)
        self.assertIn("gaps 12:00-13:00", out)
        self.assertNotEqual(self.run_eeh("close", "--date", "2026-10-01", ok=False).returncode, 0)

    def test_verify_detects_edit(self):
        self.run_eeh("add", "--date", "2026-10-01", "--min", "60", "--detail", "original")
        self.assertIn("OK", self.run_eeh("verify").stdout)
        path = self.env["EEH_LEDGER"]
        with open(path, encoding="utf-8") as f:
            text = f.read()
        with open(path, "w", encoding="utf-8") as f:
            f.write(text.replace("original", "edited"))
        self.assertIn("TAMPERED", self.run_eeh("verify").stdout)

    def test_request_report_logs_share(self):
        self.run_eeh("add", "--date", "2026-10-02", "--min", "120", "--project", "Atlas")
        self.run_eeh("req", "--by", "Project Manager", "--from", "2026-10-01", "--to", "2026-10-31",
                     "--purpose", "appraisal")
        out = self.run_eeh("report", "--req", "R0001", "--out", "r.html").stdout
        self.assertIn("2.0 h", out)
        self.assertIn("S0001 logged share for R0001", out)
        with open(os.path.join(self.dir.name, "r.html"), encoding="utf-8") as f:
            self.assertIn("Requested by:", f.read())

    def test_timesheet_rounds_to_15(self):
        self.run_eeh("add", "--date", "2026-10-03", "--min", "50", "--project", "Atlas", "--ref", "ZP-1")
        self.run_eeh("timesheet", "--from", "2026-10-01", "--to", "2026-10-31", "--out", "ts.csv")
        with open(os.path.join(self.dir.name, "ts.csv"), encoding="utf-8") as f:
            self.assertIn("2026-10-03,Atlas,ZP-1,0.75", f.read())


if __name__ == "__main__":
    unittest.main()
