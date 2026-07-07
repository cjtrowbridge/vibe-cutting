import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "host_readiness_report.py"
SPEC = importlib.util.spec_from_file_location("host_readiness_report", SCRIPT)
host_readiness_report = importlib.util.module_from_spec(SPEC)
sys.modules["host_readiness_report"] = host_readiness_report
SPEC.loader.exec_module(host_readiness_report)


class HostReadinessReportTests(unittest.TestCase):
    def test_report_omits_user_home_and_records_helpers(self):
        data = host_readiness_report.report()
        self.assertEqual(data["schema_version"], 1)
        self.assertGreaterEqual(len(data["helper_tools"]), 4)
        self.assertIn("environment_manager", data)
        text = repr(data)
        self.assertNotIn(str(Path.home()), text)

    def test_write_reports_creates_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data = host_readiness_report.write_reports(root)
            self.assertTrue((root / "host-readiness-full.json").is_file())
            self.assertTrue((root / "host-readiness-full.md").is_file())
            self.assertEqual(data["schema_version"], 1)


if __name__ == "__main__":
    unittest.main()
