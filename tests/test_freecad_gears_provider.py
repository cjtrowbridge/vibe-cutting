import importlib.util
import json
from pathlib import Path
import subprocess
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = REPO_ROOT / "scripts" / "helper_tool.py"
DRIVER_PATH = REPO_ROOT / "setup" / "tools" / "freecad_gears.py"
SPEC = importlib.util.spec_from_file_location("helper_tool", HELPER_PATH)
helper_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper_tool)
DRIVER_SPEC = importlib.util.spec_from_file_location("freecad_gears_driver", DRIVER_PATH)
freecad_gears_driver = importlib.util.module_from_spec(DRIVER_SPEC)
DRIVER_SPEC.loader.exec_module(freecad_gears_driver)


class FreeCadGearsProviderTests(unittest.TestCase):
    def test_adapter_registers_inspection_only_provider(self):
        tool = helper_tool.get_tool("freecad_gears")
        self.assertEqual(tool["provider"]["kind"], "pixi_environment")
        self.assertEqual(tool["source"]["license"], "GPL-3.0-or-later")
        self.assertEqual(helper_tool.source_revision(tool), tool["source"]["pinned_revision"])
        self.assertFalse(tool["readiness"]["fabrication_approved"])
        self.assertIn("gear_inspection", tool["capabilities"])
        self.assertNotIn("fabrication-approved", tool["readiness"]["states"])

    def test_validate_reports_freecad_provider_adapter(self):
        result = subprocess.run(
            ["python3", "scripts/helper_tool.py", "validate"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        adapters = {item["id"]: item for item in json.loads(result.stdout)["adapters"]}
        self.assertEqual(adapters["freecad_gears"]["provider_kind"], "pixi_environment")

    def test_unsupported_requests_fail_closed(self):
        for request in [
            {"request_type": "fabricate", "gear_type": "involute_spur"},
            {"request_type": "inspection", "gear_type": "worm"},
        ]:
            with self.subTest(request=request):
                with self.assertRaises(freecad_gears_driver.FreeCadGearsError):
                    freecad_gears_driver.reject_unsupported(request)

    def test_inspection_script_preserves_non_authoritative_boundary(self):
        request = {
            "parameters": {
                "module": 2.0,
                "teeth": 18,
                "height": 3.0,
                "pressure_angle": 20.0,
                "bore_diameter": 5.0,
            }
        }
        script = freecad_gears_driver.inspection_script(
            request,
            REPO_ROOT / ".tmp" / "freecad_gears" / "test.json",
            REPO_ROOT / ".tmp" / "freecad_gears" / "test.step",
        )
        self.assertIn('"fabrication_approved": False', script)
        self.assertIn("CreateInvoluteGear.create()", script)


if __name__ == "__main__":
    unittest.main()
