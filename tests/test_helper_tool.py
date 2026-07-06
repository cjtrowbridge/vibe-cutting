import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "helper_tool.py"
SPEC = importlib.util.spec_from_file_location("helper_tool", MODULE_PATH)
helper_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper_tool)


class HelperToolTests(unittest.TestCase):
    def test_boxes_manifest_loads(self):
        tool = helper_tool.get_tool("boxes")
        self.assertEqual(tool["tool_class"], "callable_helper")
        self.assertEqual(tool["runtime"]["module"], "boxes.scripts.boxes_main")
        self.assertEqual(tool["outputs"]["primary_format"], "svg")
        self.assertFalse(tool["safety"]["controls_hardware"])

    def test_boxes_pin_matches_submodule(self):
        tool = helper_tool.get_tool("boxes")
        self.assertEqual(helper_tool.source_revision(tool), tool["source"]["pinned_revision"])
        self.assertTrue(helper_tool.source_is_clean(tool))

    def test_environment_is_confined_to_tmp(self):
        tool = helper_tool.get_tool("boxes")
        expected_root = (REPO_ROOT / ".tmp" / "helper-tools").resolve()
        tool["_environment_path"].relative_to(expected_root)

    def test_repo_path_rejects_escape(self):
        with self.assertRaisesRegex(helper_tool.ToolError, "escapes the repository"):
            helper_tool.safe_repo_path("../outside", "Test path")

    def test_manifest_filename_must_match_id(self):
        manifest = json.loads((REPO_ROOT / "tool_adapters" / "boxes.json").read_text())
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp") as directory:
            path = Path(directory) / "wrong.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(helper_tool.ToolError, "filename must match"):
                helper_tool.validate_manifest(manifest, path)

    def test_manifest_source_must_be_third_party(self):
        manifest = json.loads((REPO_ROOT / "tool_adapters" / "boxes.json").read_text())
        manifest["source"]["path"] = "scripts"
        manifest["runtime"]["install_source"] = "scripts"
        with self.assertRaisesRegex(helper_tool.ToolError, "must be under third_party"):
            helper_tool.validate_manifest(manifest, REPO_ROOT / "tool_adapters" / "boxes.json")

    def test_readiness_fails_closed_without_environment(self):
        tool = helper_tool.get_tool("boxes")
        with mock.patch.object(helper_tool, "site_packages_path", return_value=Path("/missing/site-packages")):
            state = helper_tool.inspect_tool(tool)
        self.assertFalse(state["environment_present"])
        self.assertFalse(state["ready"])

    def test_run_requires_ready_environment(self):
        tool = helper_tool.get_tool("boxes")
        with mock.patch.object(helper_tool, "inspect_tool", return_value={"ready": False}):
            with self.assertRaisesRegex(helper_tool.ToolError, "is not ready"):
                helper_tool.run_tool(tool, ["--list"])

    def test_run_rejects_source_mutation(self):
        tool = helper_tool.get_tool("boxes")
        with mock.patch.object(helper_tool, "inspect_tool", return_value={"ready": True, "source_revision": "abc"}):
            with mock.patch.object(helper_tool.subprocess, "run", return_value=mock.Mock(returncode=0)):
                with mock.patch.object(helper_tool, "source_is_clean", return_value=False):
                    with self.assertRaisesRegex(helper_tool.ToolError, "modified its source"):
                        helper_tool.run_tool(tool, ["--list"])

    def test_public_manifest_omits_internal_paths(self):
        tool = helper_tool.get_tool("boxes")
        public = helper_tool.public_manifest(tool)
        self.assertFalse(any(key.startswith("_") for key in public))


if __name__ == "__main__":
    unittest.main()
