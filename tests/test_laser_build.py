import copy
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
        self.assertEqual(manifest["engraving_text"], "good for one free shot anywhere any time")
        self.assertEqual(manifest["engraving"]["backend"], "openscad_font")
        self.assertEqual(manifest["engraving"]["font_name"], "Liberation Sans:style=Regular")
        self.assertEqual(len(manifest["warnings"]), 3)

    def test_openscad_svg_parser_accepts_linear_closed_contours(self):
        contours = laser_build.parse_linear_svg_path(
            "M 0,0 L 4,0 L 4,4 L 0,4 z M 1,1 L 1,3 L 3,3 L 3,1 z"
        )

        self.assertEqual(len(contours), 2)
        self.assertEqual(contours[0][0], contours[0][-1])
        self.assertEqual(contours[1][0], contours[1][-1])
        with self.assertRaisesRegex(SystemExit, "Unsupported OpenSCAD SVG path commands"):
            laser_build.parse_linear_svg_path("M 0,0 C 1,1 2,2 3,3 z")

    def test_openscad_font_is_pinned_and_hatching_is_contained(self):
        config = self.context["config"]
        font_path = REPO_ROOT / config["font_file"]
        segments = laser_build.openscad_font_segments(config)
        usable_radius = config["coin_diameter_mm"] / 2 - config["engraving_inset_mm"]

        self.assertEqual(config["font_name"], "Liberation Sans:style=Regular")
        self.assertEqual(laser_build.sha256(font_path), config["font_sha256"])
        self.assertTrue(all(abs(start_y - end_y) <= 1e-12 for _, start_y, _, end_y in segments))
        laser_build.assert_segments_within_circle(segments, (0.0, 0.0), usable_radius)

        invalid_context = copy.deepcopy(self.context)
        invalid_context["config"]["font_sha256"] = "0" * 64
        with self.assertRaisesRegex(SystemExit, "font hash does not match"):
            laser_build.validate_context(invalid_context)

    def test_regular_default_preserves_valid_bold_revision(self):
        bold_context = laser_build.resolve_design(
            "shot_coins",
            "designs/shot_coins/configs/rev_0004.json",
        )
        laser_build.validate_context(bold_context)

        self.assertEqual(self.context["config"]["font_name"], "Liberation Sans:style=Regular")
        self.assertEqual(bold_context["config"]["font_name"], "Liberation Sans:style=Bold")
        self.assertNotEqual(
            self.context["config"]["font_sha256"],
            bold_context["config"]["font_sha256"],
        )

    def test_merit_badge_sets_use_reusable_24_token_layout(self):
        expected_counts = {
            "bwb_merit_badges": [3, 3, 3, 3, 3, 3, 2, 2, 2],
            "queer_sex_party_merit_badges": [4, 4, 4, 4, 4, 4],
            "community_garden_merit_badges": [3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2],
        }
        for design_name, counts in expected_counts.items():
            with self.subTest(design=design_name):
                context = laser_build.resolve_design(design_name)
                laser_build.validate_context(context)
                layout = laser_build.compute_layout(context["config"], context["machine"])
                paths = laser_build.cut_paths(context["config"], layout)

                self.assertEqual(layout["quantity"], 24)
                self.assertEqual((layout["columns"], layout["rows"]), (4, 6))
                self.assertEqual(list(layout["badge_counts"].values()), counts)
                self.assertEqual(sum(layout["badge_counts"].values()), 24)
                self.assertEqual(len(paths), 24)
                self.assertTrue(all(path[0] == path[-1] for path in paths))
                for path in paths:
                    self.assertTrue(
                        all(
                            0 <= point_x <= layout["effective_width_mm"]
                            and 0 <= point_y <= layout["effective_height_mm"]
                            for point_x, point_y in path
                        )
                    )
                width = context["config"]["token_width_mm"]
                height = context["config"]["token_height_mm"]
                gap = context["config"]["token_gap_mm"]
                for index, first in enumerate(layout["centers"]):
                    for second in layout["centers"][index + 1 :]:
                        self.assertTrue(
                            abs(first[0] - second[0]) >= width + gap - 1e-9
                            or abs(first[1] - second[1]) >= height + gap - 1e-9
                        )

    def test_merit_badge_text_wraps_and_stays_inside_rounded_tokens(self):
        context = laser_build.resolve_design("queer_sex_party_merit_badges")
        config = context["config"]
        badge = next(
            badge
            for badge in config["badges"]
            if badge["id"] == "lube_logistics_coordinator"
        )
        geometry = laser_build.merit_badge_relative_segments(config, badge)

        self.assertGreater(len(geometry["body_lines"]), 1)
        self.assertEqual(" ".join(geometry["body_lines"]), badge["description"])
        laser_build.assert_segments_within_rounded_rectangle(
            geometry["segments"],
            (0.0, 0.0),
            config["token_width_mm"],
            config["token_height_mm"],
            config["corner_radius_mm"],
            config["engraving_inset_mm"],
        )
        oversized = copy.deepcopy(config)
        oversized["body_font_size_mm"] = 20.0
        with self.assertRaisesRegex(SystemExit, "Merit badge"):
            laser_build.merit_badge_relative_segments(oversized, badge)

    def test_merit_badge_manifest_and_gcode_match_allocated_set(self):
        context = laser_build.resolve_design("community_garden_merit_badges")
        layout = laser_build.compute_layout(context["config"], context["machine"])
        segments = laser_build.all_engraving_segments(context["config"], layout)
        manifest = laser_build.job_manifest(context, layout, len(segments))
        gcode = laser_build.generate_gcode(
            context["config"],
            context["machine"],
            context["material"],
            layout,
            segments,
        )

        self.assertEqual(manifest["design_type"], "merit_badge_set")
        self.assertEqual(manifest["token"]["shape"], "rounded_rectangle")
        self.assertEqual(sum(badge["quantity"] for badge in manifest["badges"]), 24)
        self.assertIn("season’s abundance.", manifest["badges"][0]["description"])
        laser_on = False
        for line in gcode.splitlines():
            if line.startswith(("M3", "M4")):
                laser_on = True
            elif line == "M5":
                laser_on = False
            elif line.startswith("G0"):
                self.assertFalse(laser_on, line)

    def test_openscad_font_normalizes_svg_to_upright_y_axis(self):
        config = copy.deepcopy(self.context["config"])
        config["text_lines"] = ["F"]
        segments = laser_build.openscad_font_segments(config)
        upper_ink = sum(end_x - start_x for start_x, y, end_x, _ in segments if y > 0)
        lower_ink = sum(end_x - start_x for start_x, y, end_x, _ in segments if y < 0)

        self.assertGreater(upper_ink, lower_ink)

    def test_hug_variant_resolves_and_generates_contained_text(self):
        context = laser_build.resolve_design("hug_coins")
        laser_build.validate_context(context)
        layout = laser_build.compute_layout(context["config"], context["machine"])
        segments = laser_build.all_engraving_segments(context["config"], layout)
        manifest = laser_build.job_manifest(context, layout, len(segments))

        self.assertEqual(context["config"]["text_lines"][2], "HUG")
        self.assertEqual(layout["quantity"], 81)
        self.assertEqual(manifest["design"], "hug_coins")
        self.assertEqual(manifest["engraving_text"], "good for one free hug anywhere any time")
        self.assertGreater(len(laser_build.FONT["U"][0]), 2)

    def test_engraving_segments_stay_inside_configured_inset(self):
        config = self.context["config"]
        layout = laser_build.compute_layout(
            config,
            self.context["machine"],
            quantity_override=1,
        )
        center = layout["centers"][0]
        usable_radius = config["coin_diameter_mm"] / 2 - config["engraving_inset_mm"]
        segments = laser_build.text_segments(
            center,
            config["coin_diameter_mm"],
            config["text_lines"],
            config["engraving_inset_mm"],
        )

        laser_build.assert_segments_within_circle(segments, center, usable_radius)
        self.assertLessEqual(
            max(
                math.dist(center, point)
                for segment in segments
                for point in ((segment[0], segment[1]), (segment[2], segment[3]))
            ),
            usable_radius + 1e-9,
        )

    def test_out_of_bounds_engraving_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "Engraving geometry exceeds"):
            laser_build.assert_segments_within_circle(
                [(0.0, 0.0, 15.0, 0.0)],
                (0.0, 0.0),
                14.0,
            )

    def test_vector_text_is_upright_and_ordered_top_to_bottom(self):
        config = self.context["config"]
        center = (0.0, 0.0)
        segments = laser_build.text_segments(
            center,
            config["coin_diameter_mm"],
            config["text_lines"],
            config["engraving_inset_mm"],
        )

        def line_segment_count(text):
            return sum(
                len(polyline) - 1
                for character in text
                for polyline in laser_build.FONT[character]
            )

        top_count = line_segment_count(config["text_lines"][0])
        bottom_count = line_segment_count(config["text_lines"][-1])
        top_points = [
            point
            for segment in segments[:top_count]
            for point in ((segment[0], segment[1]), (segment[2], segment[3]))
        ]
        bottom_points = [
            point
            for segment in segments[-bottom_count:]
            for point in ((segment[0], segment[1]), (segment[2], segment[3]))
        ]
        self.assertGreater(min(point[1] for point in top_points), max(point[1] for point in bottom_points))
        self.assertTrue(any(abs(y2 - y1) > 1e-9 for _, y1, _, y2 in segments))

        letter_a = laser_build.text_segments(center, 30.0, ["A"], 1.0)
        highest_y = max(max(segment[1], segment[3]) for segment in letter_a)
        apex_y = max(
            point_y
            for segment in letter_a
            for point_x, point_y in ((segment[0], segment[1]), (segment[2], segment[3]))
            if abs(point_x - center[0]) < 1e-9
        )
        self.assertAlmostEqual(apex_y, highest_y)

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

    def test_mechanism_design_validates_and_records_manifest_fragment(self):
        context = laser_build.resolve_design("primitive_power_extender_laser_0_1")
        laser_build.validate_context(context)
        layout = laser_build.compute_layout(context["config"], context["machine"])
        report = laser_build.mechanism_validation_report(context["config"])
        segments = laser_build.all_engraving_segments(context["config"], layout)
        manifest = laser_build.job_manifest(context, layout, len(segments), report)
        cut_paths = laser_build.cut_paths(context["config"], layout)

        self.assertTrue(report["passed"])
        self.assertEqual(manifest["design_type"], "mechanism_sheet")
        self.assertEqual(manifest["mechanism"]["mechanism_id"], "primitive_power_extender_laser_0_1")
        self.assertTrue(manifest["mechanism"]["mechanism_validation_passed"])
        self.assertEqual(manifest["mechanism"]["validation_report"], "mechanism_validation.json")
        self.assertGreater(len(segments), 0)
        self.assertGreaterEqual(len(cut_paths), 8)


if __name__ == "__main__":
    unittest.main()
