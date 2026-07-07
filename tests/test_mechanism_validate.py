import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "mechanism_validate.py"
SPEC = importlib.util.spec_from_file_location("mechanism_validate", VALIDATOR_PATH)
mechanism_validate = importlib.util.module_from_spec(SPEC)
sys.modules["mechanism_validate"] = mechanism_validate
SPEC.loader.exec_module(mechanism_validate)


def valid_model():
    return {
        "schema_version": 1,
        "mechanism_id": "test_mechanism",
        "constraints": {
            "mesh_tolerance_mm": 0.1,
            "ratio_tolerance": 0.001,
            "phase_tolerance_deg": 0.5,
            "min_backlash_mm": 0.05,
            "min_bore_clearance_mm": 0.1,
            "min_tooth_root_mm": 0.8,
            "min_web_mm": 1.2,
            "min_rotating_clearance_mm": 0.5,
        },
        "parts": [
            {
                "id": "gear_a",
                "kind": "gear",
                "layer": "drive",
                "center": [0, 0],
                "module_mm": 2.0,
                "teeth": 20,
                "bore_diameter_mm": 5.2,
                "axle": "axle_a",
            },
            {
                "id": "gear_b",
                "kind": "gear",
                "layer": "drive",
                "center": [50, 0],
                "module_mm": 2.0,
                "teeth": 30,
                "bore_diameter_mm": 5.2,
                "axle": "axle_b",
            },
            {
                "id": "rotor_c",
                "kind": "rotor",
                "layer": "drive",
                "center": [100, 0],
                "radius_mm": 8,
                "root_diameter_mm": 16,
                "bore_diameter_mm": 5.2,
                "axle": "axle_c",
            },
            {"id": "axle_a", "kind": "axle", "layer": "drive", "center": [0, 0], "axle_diameter_mm": 5.0},
            {"id": "axle_b", "kind": "axle", "layer": "drive", "center": [50, 0], "axle_diameter_mm": 5.0},
            {"id": "axle_c", "kind": "axle", "layer": "drive", "center": [100, 0], "axle_diameter_mm": 5.0},
            {"id": "reg_1", "kind": "registration_feature", "layer": "drive", "center": [5, 5], "radius_mm": 1.5},
            {"id": "reg_2", "kind": "registration_feature", "layer": "cover", "center": [95, 5], "radius_mm": 1.5},
        ],
        "stackup": {
            "layers": [
                {"id": "drive", "material": "basswood", "thickness_mm": 3.0, "registration_ids": ["reg_1", "reg_2"]},
                {"id": "cover", "material": "basswood", "thickness_mm": 3.0, "registration_ids": ["reg_1", "reg_2"]},
            ],
            "fasteners": [{"id": "m3_1", "diameter_mm": 3.0, "layers": ["drive", "cover"]}],
            "bearings": [],
            "bushings": [],
        },
        "meshes": [
            {
                "id": "mesh_ab",
                "driver": "gear_a",
                "driven": "gear_b",
                "center_distance_mm": 50.0,
                "ratio": -0.6666667,
                "backlash_mm": 0.08,
                "phase_transfer_deg": 180.0,
            }
        ],
        "phases": [{"part": "gear_a", "phase_deg": 0.0}, {"part": "gear_b", "phase_deg": 180.0}],
        "channels": [{"id": "power_main", "kind": "power", "key": "round"}],
        "interfaces": [{"id": "iface_a", "part": "gear_a", "channel": "power_main", "key": "round"}],
        "operations": [
            {"id": "cut_a", "operation": "cut", "source_path": "output/test/a.svg"},
            {"id": "engrave_a", "operation": "engrave", "source_path": "output/test/a.svg"},
        ],
        "helper_geometry": [
            {
                "tool_id": "cq_gears",
                "request_sha256": "a" * 64,
                "artifact": ".tmp/cq_gears/provider-smoke/spur.svg",
                "source_revision": "e73874cf17a25447a99b1e7c22a4d5af38560e9c",
            }
        ],
    }


class MechanismValidateTests(unittest.TestCase):
    def assert_fails_check(self, model, check_name):
        report = mechanism_validate.validation_report(model)
        self.assertFalse(report["passed"])
        self.assertIn(check_name, [check["name"] for check in report["checks"] if not check["passed"]])

    def test_valid_model_passes_and_exports_manifest_fragment(self):
        report = mechanism_validate.validation_report(valid_model())
        self.assertTrue(report["passed"])
        self.assertEqual(report["job_manifest_fragment"]["mechanism_id"], "test_mechanism")
        self.assertEqual(report["job_manifest_fragment"]["mechanism_check_count"], len(report["checks"]))

    def test_cli_writes_report(self):
        root = REPO_ROOT / ".tmp" / "mechanism_validate"
        root.mkdir(parents=True, exist_ok=True)
        model_path = root / "valid.json"
        report_path = root / "report.json"
        model_path.write_text(json.dumps(valid_model(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result = subprocess.run(
            ["python3", "scripts/mechanism_validate.py", str(model_path.relative_to(REPO_ROOT)), "--output", str(report_path.relative_to(REPO_ROOT))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(report_path.read_text(encoding="utf-8"))["passed"])

    def test_mesh_distance_failure(self):
        model = valid_model()
        model["meshes"][0]["center_distance_mm"] = 48.0
        self.assert_fails_check(model, "mesh_distance")

    def test_ratio_failure(self):
        model = valid_model()
        model["meshes"][0]["ratio"] = 1.0
        self.assert_fails_check(model, "mesh_ratio")

    def test_phase_failure(self):
        model = valid_model()
        model["phases"][1]["phase_deg"] = 90.0
        self.assert_fails_check(model, "phase_transfer")

    def test_backlash_failure(self):
        model = valid_model()
        model["meshes"][0]["backlash_mm"] = 0.0
        self.assert_fails_check(model, "mesh_backlash")

    def test_bore_clearance_failure(self):
        model = valid_model()
        model["parts"][0]["bore_diameter_mm"] = 5.0
        self.assert_fails_check(model, "bore_clearance")

    def test_web_failure(self):
        model = valid_model()
        model["parts"][0]["bore_diameter_mm"] = 35.0
        self.assert_fails_check(model, "web_thickness")

    def test_collision_failure(self):
        model = valid_model()
        model["parts"][2]["center"] = [60, 0]
        self.assert_fails_check(model, "rotating_collision")

    def test_stack_registration_failure(self):
        model = valid_model()
        model["stackup"]["layers"][0]["registration_ids"].append("missing_reg")
        self.assert_fails_check(model, "stack_registration")

    def test_channel_key_failure(self):
        model = valid_model()
        model["interfaces"][0]["key"] = "square"
        self.assert_fails_check(model, "channel_key")

    def test_duplicate_cut_failure(self):
        model = valid_model()
        model["operations"].append({"id": "cut_dup", "operation": "cut", "source_path": "output/test/a.svg"})
        self.assert_fails_check(model, "duplicate_cut_paths")

    def test_helper_provenance_failure(self):
        model = valid_model()
        model["helper_geometry"][0]["request_sha256"] = "not-a-hash"
        self.assert_fails_check(model, "helper_geometry_provenance")


if __name__ == "__main__":
    unittest.main()
