#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER_TOOL_PATH = REPO_ROOT / "scripts" / "helper_tool.py"
SPEC = importlib.util.spec_from_file_location("helper_tool", HELPER_TOOL_PATH)
assert SPEC and SPEC.loader
helper_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper_tool)

from setup.providers import provider_for_manifest


class BoxesDriverError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise BoxesDriverError(message)


def load_tool(manifest_path: Path) -> dict:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    tool = helper_tool.validate_manifest(data, manifest_path)
    if tool["id"] != "boxes":
        fail(f"Boxes driver received wrong adapter: {tool['id']}")
    return tool


def provider_paths(tool: dict):
    provider = provider_for_manifest(REPO_ROOT, tool)
    fingerprint = provider.environment_fingerprint()
    environment = tool["_environment_path"] / fingerprint
    return provider, fingerprint, environment, environment / "site-packages"


def python_environment(site_packages: Path | None = None) -> dict[str, str]:
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    if site_packages is not None:
        existing = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = str(site_packages) if not existing else os.pathsep.join([str(site_packages), existing])
    return environment


def run_capture(command: list[str], *, site_packages: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=python_environment(site_packages),
    )


def ensure_source_ready(tool: dict) -> None:
    state = helper_tool.inspect_provider_tool(tool)
    for key, message in [
        ("source_present", "source submodule is missing"),
        ("pin_matches", "source revision does not match the adapter pin"),
        ("source_clean", "source submodule has local modifications"),
        ("license_present", "declared license file is missing"),
    ]:
        if not state[key]:
            fail(f"Cannot set up boxes: {message}.")


def setup(tool: dict) -> dict:
    ensure_source_ready(tool)
    provider, fingerprint, environment, site_packages = provider_paths(tool)
    provider.cleanup_incomplete_staging()
    provider.cache_root().mkdir(parents=True, exist_ok=True)
    provider.temp_root().mkdir(parents=True, exist_ok=True)
    provider.log_root().mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="boxes-", dir=provider.staging_root()) as stage_text:
        stage = Path(stage_text)
        staged_site_packages = stage / "site-packages"
        staged_site_packages.mkdir()
        install_log = provider.log_root() / "install.log"
        command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--target",
            str(staged_site_packages),
            "--constraint",
            str(REPO_ROOT / "setup" / "tools" / "boxes-requirements.lock"),
            str(tool["_source_path"]),
        ]
        with install_log.open("w", encoding="utf-8") as log:
            result = subprocess.run(
                command,
                cwd=REPO_ROOT,
                check=False,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                env=python_environment(),
            )
        if result.returncode:
            fail(f"Boxes.py installation failed; see {install_log.relative_to(REPO_ROOT)}")
        import_result = run_capture(
            [sys.executable, "-c", "import boxes; import shapely"],
            site_packages=staged_site_packages,
        )
        if import_result.returncode:
            fail(import_result.stderr.strip() or import_result.stdout.strip() or "Boxes.py import failed")
        package_result = run_capture(
            [
                sys.executable,
                "-m",
                "pip",
                "list",
                "--path",
                str(staged_site_packages),
                "--format",
                "json",
                "--disable-pip-version-check",
            ]
        )
        if package_result.returncode:
            fail("Could not record installed Boxes.py package versions.")
        marker = {
            "schema_version": 1,
            "tool_id": "boxes",
            "provider_kind": "pixi_environment",
            "source_revision": tool["source"]["pinned_revision"],
            "adapter_sha256": helper_tool.manifest_sha256(tool),
            "environment_fingerprint": fingerprint,
            "lock_hashes": provider.lock_hashes(),
            "python_version": ".".join(map(str, sys.version_info[:3])),
            "packages": sorted(json.loads(package_result.stdout), key=lambda package: package["name"].lower()),
            "state": "invocation-ready",
        }
        (stage / "provider-ready.json").write_text(
            json.dumps(marker, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        environment.parent.mkdir(parents=True, exist_ok=True)
        if environment.exists():
            shutil.rmtree(environment)
        shutil.copytree(stage, environment)
    provider.cleanup_incomplete_staging()
    return marker


def validate_svg(path: Path, operation_colors: dict[str, str]) -> str:
    if path.suffix.lower() != ".svg":
        fail(f"Boxes.py output is not SVG: {path}")
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as error:
        fail(f"Boxes.py output is not parseable SVG: {path}: {error}")
    allowed = set(operation_colors)
    for element in root.iter():
        for key in ("stroke", "fill"):
            value = element.attrib.get(key)
            if value and value.startswith("rgb(") and value not in allowed and value != "none":
                fail(f"Boxes.py output uses undeclared {key} color {value}: {path}")
    return helper_tool.hashlib.sha256(path.read_bytes()).hexdigest()


def request_from_arguments(arguments: list[str]) -> dict:
    if len(arguments) != 2:
        fail("Boxes provider run expects: --multi-generator <generator.yml> <output-dir>")
    generator_yaml, output_directory = arguments
    output = Path(output_directory)
    expected = output / "smoke_0.svg"
    return {
        "schema_version": 1,
        "tool_id": "boxes",
        "request_type": "yaml_multi_generator",
        "generator_yaml": generator_yaml,
        "output_directory": output_directory,
        "expected_outputs": [{"path": str(expected), "format": "svg", "required": True}],
    }


def run_boxes(tool: dict, arguments: list[str]) -> int:
    if arguments and arguments[0] == "--multi-generator":
        request = request_from_arguments(arguments[1:])
        helper_tool.validate_helper_request(
            tool,
            {
                "schema_version": 1,
                "tool_id": "boxes",
                "request_type": "yaml_multi_generator",
                "inputs": [request["generator_yaml"]],
                "outputs": [item["path"] for item in request["expected_outputs"]],
            },
        )
    provider, _, environment, site_packages = provider_paths(tool)
    marker = json.loads((environment / "provider-ready.json").read_text(encoding="utf-8"))
    if marker.get("state") != "invocation-ready":
        fail("Boxes provider environment is not invocation-ready.")
    command = [sys.executable, "-m", tool["provider"]["invocation"]["module"], *arguments]
    result = subprocess.run(
        command,
        cwd=tool["_working_directory"],
        check=False,
        env=python_environment(site_packages),
    )
    if result.returncode:
        return result.returncode
    if not helper_tool.source_is_clean(tool):
        fail("Boxes.py modified its source submodule; output is rejected.")
    if arguments and arguments[0] == "--multi-generator":
        inventory = []
        for item in request["expected_outputs"]:
            path = helper_tool.safe_repo_path(item["path"], "Boxes expected output")
            inventory.append(
                {
                    "path": item["path"],
                    "format": "svg",
                    "sha256": validate_svg(path, tool["outputs"]["operation_colors"]),
                }
            )
        helper_tool.validate_output_inventory({**tool, "outputs": {**tool["outputs"], "inventory": request["expected_outputs"]}}, inventory)
    return 0


def smoke(tool: dict) -> dict:
    root = REPO_ROOT / ".tmp" / "boxes" / "provider-smoke"
    if root.exists():
        shutil.rmtree(root)
    output = root / "generated"
    output.mkdir(parents=True)
    generator = root / "generator.yml"
    generator.write_text(
        "Defaults:\n"
        "  reference: 0\n"
        "Boxes:\n"
        "  - box_type: RegularBox\n"
        "    name: smoke\n"
        "    args:\n"
        "      thickness: 3\n"
        "      burn: 0.1\n",
        encoding="utf-8",
    )
    code = run_boxes(tool, ["--multi-generator", str(generator.relative_to(REPO_ROOT)), str(output.relative_to(REPO_ROOT))])
    if code:
        fail(f"Boxes smoke generation failed with exit code {code}")
    artifact = output / "smoke_0.svg"
    return {"artifact": str(artifact.relative_to(REPO_ROOT)), "sha256": helper_tool.hashlib.sha256(artifact.read_bytes()).hexdigest()}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Boxes.py provider setup and invocation driver")
    subparsers = result.add_subparsers(dest="command", required=True)
    for name in ("setup", "smoke", "validate"):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--manifest", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--manifest", required=True)
    run.add_argument("arguments", nargs=argparse.REMAINDER)
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    tool = load_tool(Path(arguments.manifest))
    try:
        if arguments.command == "setup":
            print(json.dumps(setup(tool), indent=2, sort_keys=True))
            return 0
        if arguments.command == "smoke":
            print(json.dumps(smoke(tool), indent=2, sort_keys=True))
            return 0
        if arguments.command == "validate":
            print(json.dumps(helper_tool.inspect_tool(tool), indent=2, sort_keys=True))
            return 0
        if arguments.command == "run":
            delegated = arguments.arguments
            if delegated and delegated[0] == "--":
                delegated = delegated[1:]
            return run_boxes(tool, delegated)
    except BoxesDriverError as error:
        print(f"boxes provider: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
