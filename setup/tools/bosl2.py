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


class Bosl2Error(RuntimeError):
    pass


def fail(message: str) -> None:
    raise Bosl2Error(message)


def load_tool(manifest_path: Path) -> dict:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    tool = helper_tool.validate_manifest(data, manifest_path)
    if tool["id"] != "bosl2":
        fail(f"BOSL2 driver received wrong adapter: {tool['id']}")
    return tool


def provider_paths(tool: dict):
    provider = provider_for_manifest(REPO_ROOT, tool)
    fingerprint = provider.environment_fingerprint()
    environment = tool["_environment_path"] / fingerprint
    return provider, fingerprint, environment


def run_capture(command: list[str], *, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def openscad_version(executable: str = "openscad") -> tuple[str, str]:
    result = run_capture([executable, "--version"])
    if result.returncode:
        fail(result.stderr.strip() or "OpenSCAD is not available.")
    text = (result.stdout or result.stderr).strip()
    return executable, text


def setup(tool: dict) -> dict:
    provider, fingerprint, environment = provider_paths(tool)
    executable, version = openscad_version(tool["provider"]["invocation"].get("executable", "openscad"))
    provider.cleanup_incomplete_staging()
    provider.cache_root().mkdir(parents=True, exist_ok=True)
    provider.temp_root().mkdir(parents=True, exist_ok=True)
    provider.log_root().mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="bosl2-", dir=provider.staging_root()) as stage_text:
        stage = Path(stage_text)
        marker = {
            "schema_version": 1,
            "tool_id": "bosl2",
            "provider_kind": "openscad_library",
            "source_revision": tool["source"]["pinned_revision"],
            "adapter_sha256": helper_tool.manifest_sha256(tool),
            "environment_fingerprint": fingerprint,
            "lock_hashes": provider.lock_hashes(),
            "openscad_executable": executable,
            "openscad_version": version,
            "packages": [],
            "state": "invocation-ready",
        }
        (stage / "provider-ready.json").write_text(json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        environment.parent.mkdir(parents=True, exist_ok=True)
        if environment.exists():
            shutil.rmtree(environment)
        shutil.copytree(stage, environment)
    provider.cleanup_incomplete_staging()
    return marker


def reject_unsupported(request: dict) -> None:
    if request.get("gear_type") not in {"spur", "ring", "rack"}:
        fail(f"Unsupported BOSL2 request type: {request.get('gear_type')}")


def scad_source(request: dict) -> str:
    params = request["parameters"]
    module = float(params["module"])
    teeth = int(params.get("teeth", 18))
    pressure = float(params.get("pressure_angle", 20))
    bosl = REPO_ROOT / "third_party" / "bosl2"
    header = (
        f'include <{bosl / "std.scad"}>\n'
        f'include <{bosl / "gears.scad"}>\n'
        "$fn=64;\n"
    )
    if request["gear_type"] == "spur":
        shaft = float(params.get("shaft_diam", 0))
        body = f"spur_gear2d(mod={module}, teeth={teeth}, pressure_angle={pressure}, shaft_diam={shaft});\n"
    elif request["gear_type"] == "ring":
        backing = float(params.get("backing", module * 3))
        body = f"ring_gear2d(mod={module}, teeth={teeth}, pressure_angle={pressure}, backing={backing});\n"
    else:
        bottom = float(params.get("bottom", module * 4))
        body = f"rack2d(mod={module}, teeth={teeth}, pressure_angle={pressure}, bottom={bottom});\n"
    return header + body


def validate_svg(path: Path) -> str:
    try:
        ET.parse(path)
    except ET.ParseError as error:
        fail(f"OpenSCAD output is not parseable SVG: {error}")
    return helper_tool.hashlib.sha256(path.read_bytes()).hexdigest()


def run_request(tool: dict, request_path: Path) -> dict:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    reject_unsupported(request)
    helper_tool.validate_helper_request(
        tool,
        {
            "schema_version": 1,
            "tool_id": "bosl2",
            "request_type": "openscad_svg",
            "inputs": [str(request_path.relative_to(REPO_ROOT))],
            "outputs": [request["outputs"]["svg"], request["outputs"]["manifest"]],
        },
    )
    provider, _, environment = provider_paths(tool)
    marker = environment / "provider-ready.json"
    if not marker.is_file():
        fail("BOSL2 provider environment is not invocation-ready.")
    source_path = provider.temp_root() / "request.scad"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    source_path.write_text(scad_source(request), encoding="utf-8")
    svg_path = helper_tool.safe_repo_path(request["outputs"]["svg"], "BOSL2 SVG output")
    manifest_path = helper_tool.safe_repo_path(request["outputs"]["manifest"], "BOSL2 manifest output")
    svg_path.parent.mkdir(parents=True, exist_ok=True)
    environment_vars = os.environ.copy()
    environment_vars["OPENSCADPATH"] = str(REPO_ROOT / "third_party")
    result = run_capture(["openscad", "-o", str(svg_path), str(source_path)], environment=environment_vars)
    if result.returncode:
        fail(result.stderr.strip() or result.stdout.strip() or "OpenSCAD export failed")
    svg_hash = validate_svg(svg_path)
    manifest = {
        "schema_version": 1,
        "tool_id": "bosl2",
        "request_sha256": helper_tool.hashlib.sha256(request_path.read_bytes()).hexdigest(),
        "source_revision": tool["source"]["pinned_revision"],
        "gear_type": request["gear_type"],
        "svg_sha256": svg_hash,
        "fabrication_approved": False,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def smoke(tool: dict) -> dict:
    root = REPO_ROOT / ".tmp" / "bosl2" / "provider-smoke"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    payloads = []
    for gear_type, params in [
        ("spur", {"module": 2.0, "teeth": 18, "shaft_diam": 5}),
        ("ring", {"module": 1.5, "teeth": 32, "backing": 5}),
        ("rack", {"module": 2.0, "teeth": 12, "bottom": 8}),
    ]:
        request = {
            "schema_version": 1,
            "tool_id": "bosl2",
            "request_type": "openscad_svg",
            "gear_type": gear_type,
            "parameters": params,
            "outputs": {
                "svg": f".tmp/bosl2/provider-smoke/{gear_type}.svg",
                "manifest": f".tmp/bosl2/provider-smoke/{gear_type}.json"
            }
        }
        path = root / f"{gear_type}.request.json"
        path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        payloads.append(run_request(tool, path))
    return {"outputs": payloads}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="BOSL2 OpenSCAD provider setup and invocation driver")
    subparsers = result.add_subparsers(dest="command", required=True)
    for name in ("setup", "smoke", "validate"):
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--manifest", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--manifest", required=True)
    run.add_argument("request")
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
            print(json.dumps(run_request(tool, helper_tool.safe_repo_path(arguments.request, "BOSL2 request")), indent=2, sort_keys=True))
            return 0
    except Bosl2Error as error:
        print(f"bosl2 provider: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
