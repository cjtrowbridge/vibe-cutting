import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "scripts" / "helper_tool.py"
SPEC = importlib.util.spec_from_file_location("helper_tool", MODULE_PATH)
helper_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper_tool)

from setup.providers import ProviderError, provider_for_manifest


class HelperToolTests(unittest.TestCase):
    def provider_manifest(self, tool_id="sample_provider"):
        return {
            "schema_version": 2,
            "id": tool_id,
            "display_name": "Sample Provider",
            "tool_class": "callable_helper",
            "source": {
                "type": "git_submodule",
                "path": "third_party/boxes",
                "upstream": "https://github.com/florianfesti/boxes",
                "pinned_revision": "836f5f72bedb33ac4262ed925545eacb31e926a8",
                "license": "GPL-3.0-or-later",
                "license_file": "LICENSE.txt",
            },
            "capabilities": ["svg_geometry"],
            "routing": {
                "use_for": ["Provider contract tests"],
                "avoid_for": ["Fabrication approval"],
            },
            "provider": {
                "kind": "pixi_environment",
                "environment_path": ".tools/environments/sample_provider",
                "working_directory": ".",
                "setup": {"lock_file": "setup/pixi.lock"},
                "invocation": {"driver": "setup/tools/sample_provider.py"},
                "version": {"minimum": "0.1"},
            },
            "outputs": {
                "accepted_formats": ["svg"],
                "primary_format": "svg",
                "operation_colors": {},
                "inventory": [{"path": "output/sample_provider/source.svg", "format": "svg", "required": True}],
            },
            "safety": {
                "controls_hardware": False,
                "setup_may_use_network": False,
                "may_modify_source": False,
                "allowed_input_roots": ["designs", ".tmp"],
                "allowed_output_roots": [".tmp", "output", "revisions"],
            },
            "readiness": {
                "states": ["registered"],
                "fabrication_approved": False,
            },
        }

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

    def test_provider_manifest_loads_without_migrating_boxes(self):
        manifest = self.provider_manifest()
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp") as directory:
            path = Path(directory) / "sample_provider.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            tool = helper_tool.validate_manifest(manifest, path)
        self.assertEqual(tool["_adapter_model"], "provider")
        self.assertEqual(tool["_provider_report"]["kind"], "pixi_environment")
        self.assertFalse(helper_tool.inspect_tool(tool)["ready"])

    def test_provider_manifest_rejects_unknown_provider(self):
        manifest = self.provider_manifest()
        manifest["provider"]["kind"] = "mystery_provider"
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp") as directory:
            path = Path(directory) / "sample_provider.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(helper_tool.ToolError, "unsupported helper provider"):
                helper_tool.validate_manifest(manifest, path)

    def test_provider_environment_must_stay_in_declared_roots(self):
        manifest = self.provider_manifest()
        manifest["provider"]["environment_path"] = ".tmp/helper-tools/sample_provider"
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp") as directory:
            path = Path(directory) / "sample_provider.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(helper_tool.ToolError, "environment path must be under"):
                helper_tool.validate_manifest(manifest, path)

    def test_helper_request_enforces_input_and_output_roots(self):
        manifest = self.provider_manifest()
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp") as directory:
            path = Path(directory) / "sample_provider.json"
            tool = helper_tool.validate_manifest(manifest, path)
            valid = {
                "schema_version": 1,
                "tool_id": "sample_provider",
                "request_type": "generate",
                "inputs": [".tmp/input.json"],
                "outputs": ["output/sample_provider/source.svg"],
            }
            result = helper_tool.validate_helper_request(tool, valid)
            self.assertEqual(result["input_count"], 1)
            invalid = dict(valid)
            invalid["outputs"] = ["docs/source.svg"]
            with self.assertRaisesRegex(helper_tool.ToolError, "outside allowed output roots"):
                helper_tool.validate_helper_request(tool, invalid)

    def test_output_inventory_requires_declared_outputs(self):
        manifest = self.provider_manifest()
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp") as directory:
            path = Path(directory) / "sample_provider.json"
            tool = helper_tool.validate_manifest(manifest, path)
            with self.assertRaisesRegex(helper_tool.ToolError, "missing required outputs"):
                helper_tool.validate_output_inventory(tool, [])
            inventory = [
                {
                    "path": "output/sample_provider/source.svg",
                    "format": "svg",
                    "sha256": "a" * 64,
                }
            ]
            self.assertEqual(helper_tool.validate_output_inventory(tool, inventory)[0]["format"], "svg")

    def test_output_preservation_restores_failed_operation(self):
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp") as directory:
            output = Path(directory) / "artifact.txt"
            output.write_text("previous\n", encoding="utf-8")

            def failing_operation():
                output.write_text("partial\n", encoding="utf-8")
                raise helper_tool.ToolError("boom")

            with self.assertRaisesRegex(helper_tool.ToolError, "boom"):
                helper_tool.run_with_output_preservation([str(output.relative_to(REPO_ROOT))], failing_operation)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous\n")

    def test_provider_prepare_scaffold_creates_fingerprinted_marker(self):
        manifest = self.provider_manifest()
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp") as root_text:
            root = Path(root_text)
            provider = provider_for_manifest(root, manifest)
            marker = provider.prepare_scaffold()
            environment = root / manifest["provider"]["environment_path"]
            marker_path = environment / marker["environment_fingerprint"] / "provider-ready.json"
            self.assertTrue(marker_path.is_file())
            self.assertEqual(json.loads(marker_path.read_text())["state"], "registered")
            self.assertEqual(list((root / ".tools" / "staging" / "helpers" / "sample_provider").iterdir()), [])

    def test_provider_prepare_rejects_unsupported_platform(self):
        manifest = self.provider_manifest()
        manifest["provider"]["platforms"] = ["not-this-platform"]
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / ".tmp") as root_text:
            provider = provider_for_manifest(Path(root_text), manifest)
            with self.assertRaisesRegex(ProviderError, "unsupported"):
                provider.prepare_scaffold()

    def test_validate_command_reports_legacy_adapter(self):
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "validate"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["adapters"][0]["adapter_model"], "legacy_python_module")


if __name__ == "__main__":
    unittest.main()
