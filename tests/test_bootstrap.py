from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SH = ROOT / "setup" / "bootstrap.sh"
HOST_PATH = ROOT / "setup" / "bootstrap_host.py"
SPEC = importlib.util.spec_from_file_location("bootstrap_host", HOST_PATH)
assert SPEC and SPEC.loader
bootstrap_host = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bootstrap_host)


class BootstrapTests(unittest.TestCase):
    def temporary_tools(self) -> tempfile.TemporaryDirectory[str]:
        (ROOT / ".tmp").mkdir(exist_ok=True)
        return tempfile.TemporaryDirectory(prefix="bootstrap-", dir=ROOT / ".tmp")

    def run_bootstrap(
        self,
        *arguments: str,
        tools_root: Path,
        path: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["VIBE_CUTTING_TOOLS_ROOT"] = str(tools_root)
        if path is not None:
            environment["PATH"] = path
        return subprocess.run(
            [str(BOOTSTRAP_SH), *arguments],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
        )

    def test_manifest_matches_checksum_inventory(self) -> None:
        manifest = json.loads((ROOT / "setup" / "toolchain-manifest.json").read_text())
        checksum_lines = (ROOT / "setup" / "checksums" / "pixi-v0.72.0.sha256").read_text().splitlines()
        checksums = dict(line.split(maxsplit=1)[::-1] for line in checksum_lines)
        artifacts = manifest["environment_manager"]["artifacts"]
        self.assertEqual(manifest["environment_manager"]["version"], "0.72.0")
        self.assertEqual(
            set(artifacts),
            {
                "linux-x86_64",
                "linux-aarch64",
                "macos-x86_64",
                "macos-aarch64",
                "windows-x86_64",
            },
        )
        for artifact in artifacts.values():
            self.assertEqual(checksums[artifact["name"]], artifact["sha256"])
            self.assertTrue(artifact["url"].startswith("https://github.com/prefix-dev/pixi/releases/download/v0.72.0/"))

    def test_doctor_does_not_create_missing_tools_root(self) -> None:
        with self.temporary_tools() as parent:
            tools = Path(parent) / "missing"
            result = self.run_bootstrap("doctor", tools_root=tools)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("pixi=missing", result.stdout)
            self.assertFalse(tools.exists())

    def test_setup_without_download_approval_fails_without_mutation(self) -> None:
        with self.temporary_tools() as parent:
            tools = Path(parent) / "missing"
            result = self.run_bootstrap("setup", tools_root=tools)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--allow-downloads", result.stderr)
            self.assertFalse(tools.exists())

    def test_setup_without_download_approval_preserves_incomplete_staging(self) -> None:
        with self.temporary_tools() as parent:
            tools = Path(parent)
            staged = tools / "staging" / "pixi-x86_64-unknown-linux-musl.part"
            staged.parent.mkdir(parents=True)
            staged.write_text("partial-download\n", encoding="utf-8")
            result = self.run_bootstrap("setup", tools_root=tools)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("--allow-downloads", result.stderr)
            self.assertEqual(staged.read_text(encoding="utf-8"), "partial-download\n")

    def test_tools_root_outside_repository_is_rejected(self) -> None:
        result = self.run_bootstrap("doctor", tools_root=Path("/tmp/vibe-cutting-outside"))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("inside the repository", result.stderr)

    def test_symlinked_tools_root_outside_repository_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory(dir="/tmp") as outside, self.temporary_tools() as parent:
            link = Path(parent) / "link"
            link.symlink_to(outside, target_is_directory=True)
            result = self.run_bootstrap("doctor", tools_root=link)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("resolves outside", result.stderr)

    def test_checksum_mismatch_is_rejected_without_replacement(self) -> None:
        with self.temporary_tools() as parent:
            tools = Path(parent)
            binary = tools / "bin" / "pixi"
            binary.parent.mkdir()
            binary.write_text("tampered\n", encoding="utf-8")
            binary.chmod(0o755)
            before = binary.read_bytes()
            result = self.run_bootstrap("doctor", tools_root=tools)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("checksum mismatch", result.stderr)
            self.assertEqual(binary.read_bytes(), before)

    def test_parse_submodule_status_rejects_uninitialized_and_mismatch(self) -> None:
        with self.assertRaisesRegex(bootstrap_host.BootstrapError, "uninitialized"):
            bootstrap_host.parse_submodule_status("-" + "a" * 40 + " third_party/tool\n")
        with self.assertRaisesRegex(bootstrap_host.BootstrapError, "does not match"):
            bootstrap_host.parse_submodule_status("+" + "a" * 40 + " third_party/tool\n")

    def test_parse_submodule_status_accepts_clean_gitlink(self) -> None:
        records = bootstrap_host.parse_submodule_status(" " + "a" * 40 + " third_party/tool (heads/main)\n")
        self.assertEqual(records, [(" ", "a" * 40, "third_party/tool")])

    def test_managed_run_preserves_exit_status(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as root_text:
            root = Path(root_text)
            tools = root / ".tools"
            scripts = root / "scripts"
            scripts.mkdir()
            marker = tools / "state" / "base-ready.json"
            marker.parent.mkdir(parents=True)
            marker.write_text("{}\n", encoding="utf-8")
            command = scripts / "exit_status.py"
            command.write_text("raise SystemExit(7)\n", encoding="utf-8")
            self.assertEqual(
                bootstrap_host.command_run(root, tools, ["scripts/exit_status.py"]),
                7,
            )

    def test_managed_run_preserves_arguments_and_streams(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as root_text:
            root = Path(root_text)
            tools = root / ".tools"
            scripts = root / "scripts"
            scripts.mkdir()
            marker = tools / "state" / "base-ready.json"
            marker.parent.mkdir(parents=True)
            marker.write_text("{}\n", encoding="utf-8")
            command = scripts / "echo_args.py"
            command.write_text(
                "import sys\n"
                "print('stdout:' + '|'.join(sys.argv[1:]))\n"
                "print('stderr:' + '|'.join(sys.argv[1:]), file=sys.stderr)\n",
                encoding="utf-8",
            )
            environment = os.environ.copy()
            environment["VIBE_CUTTING_REPO_ROOT"] = str(root)
            environment["VIBE_CUTTING_TOOLS_ROOT"] = str(tools)
            result = subprocess.run(
                [sys.executable, str(HOST_PATH), "run", "--", "scripts/echo_args.py", "one", "two words"],
                cwd=root,
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("stdout:one|two words", result.stdout)
            self.assertIn("stderr:one|two words", result.stderr)

    def test_managed_run_rejects_submodule_and_escape_paths(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as root_text:
            root = Path(root_text)
            (root / "third_party").mkdir()
            (root / "third_party" / "tool.py").write_text("", encoding="utf-8")
            with self.assertRaisesRegex(bootstrap_host.BootstrapError, "submodule"):
                bootstrap_host.resolve_repo_command(root, ["third_party/tool.py"])
            with self.assertRaisesRegex(bootstrap_host.BootstrapError, "escapes"):
                bootstrap_host.resolve_repo_command(root, ["../outside.py"])

    def test_shell_syntax(self) -> None:
        result = subprocess.run(["sh", "-n", str(BOOTSTRAP_SH)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell Core is unavailable")
    def test_powershell_syntax(self) -> None:
        result = subprocess.run(
            ["pwsh", "-NoProfile", "-Command", f"& {{ [scriptblock]::Create((Get-Content -Raw '{ROOT / 'setup' / 'bootstrap.ps1'}')) | Out-Null }}"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
