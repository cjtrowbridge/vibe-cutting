import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = REPO_ROOT / "scripts" / "helper_tool.py"
DRIVER_PATH = REPO_ROOT / "setup" / "tools" / "cq_gears.py"
SPEC = importlib.util.spec_from_file_location("helper_tool", HELPER_PATH)
helper_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper_tool)


class CqGearsProviderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root_record = REPO_ROOT / ".tmp" / "bootstrap-phase1-last-root"
        if not root_record.is_file():
            raise unittest.SkipTest("Managed bootstrap tools root is not installed.")
        cls.tools_root = root_record.read_text(encoding="utf-8").strip()
        result = cls.run_managed("scripts/helper_tool.py", "check", "cq_gears")
        if result.returncode:
            raise unittest.SkipTest("CQ_Gears provider environment is not installed.")

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

    def test_adapter_references_cadquery_and_cq_gears_pins(self):
        tool = helper_tool.get_tool("cq_gears")
        self.assertEqual(tool["provider"]["kind"], "pixi_environment")
        self.assertEqual(helper_tool.source_revision(tool), tool["source"]["pinned_revision"])
        secondary = tool["provider"]["setup"]["secondary_sources"][0]
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT / secondary["path"]), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.stdout.strip(), secondary["pinned_revision"])

    def test_smoke_profile_metrics_are_deterministic(self):
        first = self.run_managed("setup/tools/cq_gears.py", "smoke", "--manifest", "tool_adapters/cq_gears.json")
        second = self.run_managed("setup/tools/cq_gears.py", "smoke", "--manifest", "tool_adapters/cq_gears.json")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        first_payload = json.loads(first.stdout)
        second_payload = json.loads(second.stdout)
        self.assertEqual(first_payload["svg_sha256"], second_payload["svg_sha256"])
        metrics = first_payload["metrics"]
        self.assertEqual(metrics["tooth_count"], 18)
        self.assertEqual(metrics["pitch_diameter"], 36.0)
        self.assertEqual(metrics["outside_diameter"], 40.0)
        self.assertEqual(metrics["root_diameter"], 31.0)
        self.assertGreater(first_payload["point_count"], 1000)

    def run_request(self, name, gear_type, parameters):
        root = REPO_ROOT / ".tmp" / "cq_gears" / "test-requests"
        root.mkdir(parents=True, exist_ok=True)
        request = root / f"{name}.json"
        request.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "tool_id": "cq_gears",
                    "request_type": "planar_profile",
                    "gear_type": gear_type,
                    "parameters": parameters,
                    "outputs": {
                        "svg": f".tmp/cq_gears/test-requests/{name}.svg",
                        "manifest": f".tmp/cq_gears/test-requests/{name}.manifest.json",
                    },
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        result = self.run_managed("setup/tools/cq_gears.py", "run", "--manifest", "tool_adapters/cq_gears.json", str(request.relative_to(REPO_ROOT)))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_ring_rack_and_meshing_pair_profiles_generate(self):
        ring = self.run_request("ring", "ring", {"module": 1.5, "teeth": 32, "width": 3, "rim_width": 5})
        rack = self.run_request("rack", "rack", {"module": 2.0, "length": 80, "width": 3, "rack_height": 8})
        pair = self.run_request("pair", "meshing_pair", {"module": 2.0, "pinion_teeth": 16, "ring_teeth": 32, "width": 3})
        self.assertEqual(ring["metrics"]["tooth_count"], 32)
        self.assertGreater(rack["metrics"]["tooth_count"], 10)
        self.assertEqual(pair["metrics"]["center_distance"], 48.0)
        for payload in (ring, rack, pair):
            self.assertGreater(payload["point_count"], 10)
            self.assertRegex(payload["svg_sha256"], r"^[0-9a-f]{64}$")

    def test_non_planar_request_is_rejected(self):
        request = REPO_ROOT / ".tmp" / "cq_gears" / "bad-request.json"
        request.parent.mkdir(parents=True, exist_ok=True)
        request.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "tool_id": "cq_gears",
                    "request_type": "planar_profile",
                    "gear_type": "worm",
                    "parameters": {"module": 2.0, "teeth": 18},
                    "outputs": {
                        "svg": ".tmp/cq_gears/bad.svg",
                        "manifest": ".tmp/cq_gears/bad.json",
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        result = self.run_managed("setup/tools/cq_gears.py", "run", "--manifest", "tool_adapters/cq_gears.json", str(request.relative_to(REPO_ROOT)))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unsupported non-planar gear type", result.stderr)


if __name__ == "__main__":
    unittest.main()
