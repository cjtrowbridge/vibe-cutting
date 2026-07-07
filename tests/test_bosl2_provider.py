import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = REPO_ROOT / "scripts" / "helper_tool.py"
SPEC = importlib.util.spec_from_file_location("helper_tool", HELPER_PATH)
helper_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper_tool)


class Bosl2ProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root_record = REPO_ROOT / ".tmp" / "bootstrap-phase1-last-root"
        if not root_record.is_file():
            raise unittest.SkipTest("Managed bootstrap tools root is not installed.")
        cls.tools_root = root_record.read_text(encoding="utf-8").strip()
        result = cls.run_managed("scripts/helper_tool.py", "check", "bosl2")
        if result.returncode:
            raise unittest.SkipTest("BOSL2 provider environment is not installed.")

    @classmethod
    def run_managed(cls, *arguments):
        environment = os.environ.copy()
        environment["VIBE_CUTTING_TOOLS_ROOT"] = cls.tools_root
        return subprocess.run(
            ["setup/bootstrap.sh", "run", "--", *arguments],
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )

    def test_adapter_pin_and_openscad_provider(self):
        tool = helper_tool.get_tool("bosl2")
        self.assertEqual(tool["provider"]["kind"], "openscad_library")
        self.assertEqual(helper_tool.source_revision(tool), tool["source"]["pinned_revision"])
        self.assertTrue(helper_tool.source_is_clean(tool))

    def test_smoke_generates_spur_ring_and_rack_svg(self):
        first = self.run_managed("setup/tools/bosl2.py", "smoke", "--manifest", "tool_adapters/bosl2.json")
        second = self.run_managed("setup/tools/bosl2.py", "smoke", "--manifest", "tool_adapters/bosl2.json")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        first_payload = json.loads(first.stdout)["outputs"]
        second_payload = json.loads(second.stdout)["outputs"]
        self.assertEqual(
            [item["svg_sha256"] for item in first_payload],
            [item["svg_sha256"] for item in second_payload],
        )
        self.assertEqual([item["gear_type"] for item in first_payload], ["spur", "ring", "rack"])

    def test_unsupported_request_is_rejected(self):
        request = REPO_ROOT / ".tmp" / "bosl2" / "bad-request.json"
        request.parent.mkdir(parents=True, exist_ok=True)
        request.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "tool_id": "bosl2",
                    "request_type": "openscad_svg",
                    "gear_type": "worm",
                    "parameters": {"module": 2.0, "teeth": 18},
                    "outputs": {
                        "svg": ".tmp/bosl2/bad.svg",
                        "manifest": ".tmp/bosl2/bad.json",
                    },
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        result = self.run_managed("setup/tools/bosl2.py", "run", "--manifest", "tool_adapters/bosl2.json", str(request.relative_to(REPO_ROOT)))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsupported BOSL2 request type", result.stderr)


if __name__ == "__main__":
    unittest.main()
