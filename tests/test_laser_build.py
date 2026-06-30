import importlib.util
import math
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "laser_build.py"
SPEC = importlib.util.spec_from_file_location("laser_build", SCRIPT_PATH)
laser_build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(laser_build)


class LaserBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = laser_build.resolve_design("shot_coins")
        laser_build.validate_context(cls.context)

    def test_maximum_layout_is_in_bounds_and_separated(self):
        config = self.context["config"]
        layout = laser_build.compute_layout(config, self.context["machine"])
        radius = config["coin_diameter_mm"] / 2
        minimum_distance = config["coin_diameter_mm"] + config["coin_gap_mm"]

        self.assertEqual(layout["quantity"], 81)
        self.assertEqual(layout["maximum_quantity"], 81)
        self.assertEqual((layout["rows"], layout["columns"]), (9, 9))
        for center_x, center_y in layout["centers"]:
            self.assertGreaterEqual(center_x - radius, config["edge_margin_mm"])
            self.assertGreaterEqual(center_y - radius, config["edge_margin_mm"])
            self.assertLessEqual(
                center_x + radius,
                layout["effective_width_mm"] - config["edge_margin_mm"],
            )
            self.assertLessEqual(
                center_y + radius,
                layout["effective_height_mm"] - config["edge_margin_mm"],
            )

        for index, first in enumerate(layout["centers"]):
            for second in layout["centers"][index + 1 :]:
                self.assertGreaterEqual(
                    math.dist(first, second) + 1e-9,
                    minimum_distance,
                )

    def test_gcode_keeps_laser_off_during_rapid_moves(self):
        layout = laser_build.compute_layout(
            self.context["config"],
            self.context["machine"],
            quantity_override=1,
        )
        segments = laser_build.all_engraving_segments(self.context["config"], layout)
        gcode = laser_build.generate_gcode(
            self.context["config"],
            self.context["machine"],
            self.context["material"],
            layout,
            segments,
        )
        lines = gcode.splitlines()
        laser_on = False
        for line in lines:
            if line.startswith(("M3", "M4")):
                laser_on = True
            elif line == "M5":
                laser_on = False
            elif line.startswith("G0"):
                self.assertFalse(laser_on, line)
            if line.startswith(("G0", "G1")):
                coordinates = {
                    token[0]: float(token[1:])
                    for token in line.split()[1:]
                    if token.startswith(("X", "Y"))
                }
                if "X" in coordinates:
                    self.assertGreaterEqual(coordinates["X"], 0)
                    self.assertLessEqual(coordinates["X"], layout["effective_width_mm"])
                if "Y" in coordinates:
                    self.assertGreaterEqual(coordinates["Y"], 0)
                    self.assertLessEqual(coordinates["Y"], layout["effective_height_mm"])

        self.assertLess(lines.index("; vector_engrave"), lines.index("; through_cut"))
        self.assertEqual(lines[1:4], ["G21", "G90", "M5"])
        self.assertEqual(lines[-2:], ["M5", "; end"])

    def test_svg_uses_lower_left_coordinate_transform(self):
        layout = laser_build.compute_layout(
            self.context["config"],
            self.context["machine"],
            quantity_override=1,
        )
        segments = laser_build.all_engraving_segments(self.context["config"], layout)
        svg = laser_build.generate_svg(self.context["config"], layout, segments)

        self.assertIn(
            f'transform="translate(0 {layout["effective_height_mm"]:.3f}) scale(1 -1)"',
            svg,
        )

    def test_job_manifest_records_calibration_only_constraints(self):
        layout = laser_build.compute_layout(
            self.context["config"],
            self.context["machine"],
            quantity_override=1,
        )
        segments = laser_build.all_engraving_segments(self.context["config"], layout)
        manifest = laser_build.job_manifest(self.context, layout, len(segments))

        self.assertEqual(manifest["readiness"], "calibration_only")
        self.assertEqual(manifest["operation_order"], ["vector_engrave", "through_cut"])
        self.assertEqual(manifest["maximum_quantity"], 81)
        self.assertEqual(manifest["effective_work_area_mm"], [300.0, 268.0])
        self.assertEqual(len(manifest["warnings"]), 2)

    def test_build_manifest_supports_exact_artifact_audit(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            stage = Path(temporary_directory)
            for name in laser_build.ARTIFACT_NAMES:
                (stage / name).write_bytes(f"test:{name}\n".encode())
            manifest = laser_build.build_manifest(stage, self.context)
            laser_build.write_json(stage / "build_manifest.json", manifest)

            laser_build.audit(stage)
            self.assertEqual(
                {record["path"] for record in manifest["artifacts"]},
                laser_build.ARTIFACT_NAMES,
            )


if __name__ == "__main__":
    unittest.main()
