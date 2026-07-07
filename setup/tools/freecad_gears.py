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


REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER_TOOL_PATH = REPO_ROOT / "scripts" / "helper_tool.py"
SPEC = importlib.util.spec_from_file_location("helper_tool", HELPER_TOOL_PATH)
assert SPEC and SPEC.loader
helper_tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper_tool)

from setup.providers import provider_for_manifest


class FreeCadGearsError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise FreeCadGearsError(message)


def load_tool(manifest_path: Path) -> dict:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    tool = helper_tool.validate_manifest(data, manifest_path)
    if tool["id"] != "freecad_gears":
        fail(f"FreeCAD Gears driver received wrong adapter: {tool['id']}")
    return tool


def provider_paths(tool: dict):
    provider = provider_for_manifest(REPO_ROOT, tool)
    fingerprint = provider.environment_fingerprint()
    environment = tool["_environment_path"] / fingerprint
    return provider, fingerprint, environment


def tools_root() -> Path:
    configured = os.environ.get("VIBE_CUTTING_TOOLS_ROOT")
    return Path(configured).resolve() if configured else (REPO_ROOT / ".tools").resolve()


def pixi_bin() -> Path:
    executable = tools_root() / "bin" / "pixi"
    if not executable.is_file():
        fail("Managed Pixi is unavailable; run setup/bootstrap.sh --allow-downloads setup first.")
    return executable


def managed_environment(provider) -> dict[str, str]:
    root = tools_root()
    home = provider.cache_root() / "freecad-home"
    environment = {
        **os.environ,
        "PIXI_HOME": str(root / "pixi-home"),
        "PIXI_CACHE_DIR": str(root / "cache" / "pixi"),
        "PIXI_CONFIG_FILE": str(root / "config" / "pixi.toml"),
        "PIXI_CACHE_DETACHED_ENVIRONMENTS_DIR": str(root / "environments"),
        "PIXI_CACHE_NETFS_REDIRECT": "never",
        "HOME": str(home),
        "XDG_CACHE_HOME": str(provider.cache_root() / "xdg-cache"),
        "XDG_CONFIG_HOME": str(provider.cache_root() / "xdg-config"),
        "XDG_DATA_HOME": str(provider.cache_root() / "xdg-data"),
        "TMPDIR": str(provider.temp_root()),
    }
    for key in ("HOME", "XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "TMPDIR"):
        Path(environment[key]).mkdir(parents=True, exist_ok=True)
    return environment


def run_capture(command: list[str], *, environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def upstream_manifest(tool: dict) -> Path:
    setup = tool["provider"]["setup"]
    return helper_tool.safe_repo_path(setup["upstream_manifest"], "FreeCAD Gears upstream Pixi manifest")


def pixi_command(tool: dict, provider, *arguments: str) -> list[str]:
    return [
        str(pixi_bin()),
        "run",
        "--manifest-path",
        str(upstream_manifest(tool)),
        "--as-is",
        "--",
        *arguments,
    ]


def write_log(provider, name: str, result: subprocess.CompletedProcess[str]) -> Path:
    log_path = provider.log_root() / name
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text((result.stdout or "") + (result.stderr or ""), encoding="utf-8")
    return log_path


def install_environment(tool: dict, provider) -> None:
    result = run_capture(
        [str(pixi_bin()), "install", "--manifest-path", str(upstream_manifest(tool)), "--locked"],
        environment=managed_environment(provider),
    )
    if result.returncode:
        log_path = provider.log_root() / "pixi-install.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text((result.stdout or "") + (result.stderr or ""), encoding="utf-8")
        fail(f"Pixi could not provision FreeCAD Gears; see {log_path.relative_to(REPO_ROOT)}")


def freecad_executable(tool: dict, provider) -> str:
    candidates = tool["provider"]["invocation"].get("executable_candidates") or [
        tool["provider"]["invocation"].get("executable", "FreeCADCmd")
    ]
    errors = []
    for executable in candidates:
        result = run_capture(pixi_command(tool, provider, executable, "--version"), environment=managed_environment(provider))
        if result.returncode == 0:
            return executable
        errors.append((result.stderr or result.stdout or "").strip())
    fail("FreeCADCmd/freecadcmd is not available in the managed environment: " + " | ".join(error for error in errors if error))


def freecad_version(tool: dict, provider) -> tuple[str, str]:
    executable = freecad_executable(tool, provider)
    result = run_capture(pixi_command(tool, provider, executable, "--version"), environment=managed_environment(provider))
    if result.returncode:
        fail(result.stderr.strip() or result.stdout.strip() or "FreeCAD command is not available in the managed environment.")
    return executable, (result.stdout or result.stderr).strip()


def setup(tool: dict) -> dict:
    provider, fingerprint, environment = provider_paths(tool)
    provider.cleanup_incomplete_staging()
    provider.cache_root().mkdir(parents=True, exist_ok=True)
    provider.temp_root().mkdir(parents=True, exist_ok=True)
    provider.log_root().mkdir(parents=True, exist_ok=True)
    install_environment(tool, provider)
    executable, version = freecad_version(tool, provider)
    with tempfile.TemporaryDirectory(prefix="freecad-gears-", dir=provider.staging_root()) as stage_text:
        stage = Path(stage_text)
        marker = {
            "schema_version": 1,
            "tool_id": "freecad_gears",
            "provider_kind": "pixi_environment",
            "source_revision": tool["source"]["pinned_revision"],
            "adapter_sha256": helper_tool.manifest_sha256(tool),
            "environment_fingerprint": fingerprint,
            "lock_hashes": provider.lock_hashes(),
            "freecad_executable": executable,
            "freecad_version": version,
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
    if request.get("request_type") != "inspection":
        fail(f"Unsupported FreeCAD Gears request type: {request.get('request_type')}")
    if request.get("gear_type") != "involute_spur":
        fail(f"Unsupported FreeCAD Gears gear type: {request.get('gear_type')}")


def inspection_script(request: dict, output_manifest: Path, output_step: Path | None) -> str:
    params = request["parameters"]
    return f"""
import json
from pathlib import Path
from freecad import app
import freecad.gears.commands

doc = app.newDocument("vibe_cutting_freecad_gears_inspection")
gear = freecad.gears.commands.CreateInvoluteGear.create()
gear.num_teeth = {int(params["teeth"])}
gear.module = "{float(params["module"])} mm"
gear.height = "{float(params["height"])} mm"
gear.pressure_angle = "{float(params.get("pressure_angle", 20.0))} deg"
bore_diameter = {float(params.get("bore_diameter", 0.0))}
if bore_diameter > 0:
    gear.axle_hole = True
    gear.axle_holesize = f"{{bore_diameter}} mm"
doc.recompute()
shape = gear.Shape
metrics = {{
    "schema_version": 1,
    "tool_id": "freecad_gears",
    "gear_type": "involute_spur",
    "fabrication_approved": False,
    "teeth": int(gear.num_teeth),
    "module_mm": float(gear.module.Value),
    "height_mm": float(gear.height.Value),
    "pressure_angle_deg": float(gear.pressure_angle.Value),
    "bound_box": {{
        "x_length": float(shape.BoundBox.XLength),
        "y_length": float(shape.BoundBox.YLength),
        "z_length": float(shape.BoundBox.ZLength),
    }},
    "volume": float(shape.Volume),
}}
step_path = {str(output_step)!r}
if step_path:
    shape.exportStep(step_path)
    metrics["step"] = step_path
Path({str(output_manifest)!r}).write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
"""


def run_request(tool: dict, request_path: Path) -> dict:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    reject_unsupported(request)
    outputs = [request["outputs"]["manifest"]]
    if request["outputs"].get("step"):
        outputs.append(request["outputs"]["step"])
    helper_tool.validate_helper_request(
        tool,
        {
            "schema_version": 1,
            "tool_id": "freecad_gears",
            "request_type": "inspection",
            "inputs": [str(request_path.relative_to(REPO_ROOT))],
            "outputs": outputs,
        },
    )
    provider, _, environment = provider_paths(tool)
    marker = environment / "provider-ready.json"
    if not marker.is_file():
        fail("FreeCAD Gears provider environment is not invocation-ready.")
    manifest_path = helper_tool.safe_repo_path(request["outputs"]["manifest"], "FreeCAD Gears manifest output")
    step_path = None
    if request["outputs"].get("step"):
        step_path = helper_tool.safe_repo_path(request["outputs"]["step"], "FreeCAD Gears STEP output")
        step_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    script_path = provider.temp_root() / "inspection.py"
    script_path.write_text(inspection_script(request, manifest_path, step_path), encoding="utf-8")
    executable = freecad_executable(tool, provider)
    result = run_capture(pixi_command(tool, provider, executable, str(script_path)), environment=managed_environment(provider))
    invocation_method = executable
    fallback_log = None
    if result.returncode or not manifest_path.is_file():
        fallback_log = write_log(provider, "inspection-freecadcmd.log", result)
        result = run_capture(pixi_command(tool, provider, "python", str(script_path)), environment=managed_environment(provider))
        invocation_method = "python_freecad_module"
    if result.returncode or not manifest_path.is_file():
        log_path = write_log(provider, "inspection.log", result)
        fail(f"FreeCAD inspection failed; see {log_path.relative_to(REPO_ROOT)}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["request_sha256"] = helper_tool.hashlib.sha256(request_path.read_bytes()).hexdigest()
    manifest["source_revision"] = tool["source"]["pinned_revision"]
    manifest["invocation_method"] = invocation_method
    if fallback_log:
        manifest["freecadcmd_fallback_log"] = str(fallback_log.relative_to(REPO_ROOT))
    if step_path and step_path.is_file():
        manifest["step_sha256"] = helper_tool.hashlib.sha256(step_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def smoke(tool: dict) -> dict:
    root = REPO_ROOT / ".tmp" / "freecad_gears" / "provider-smoke"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    request = {
        "schema_version": 1,
        "tool_id": "freecad_gears",
        "request_type": "inspection",
        "gear_type": "involute_spur",
        "parameters": {
            "module": 2.0,
            "teeth": 18,
            "height": 3.0,
            "pressure_angle": 20.0,
            "bore_diameter": 5.0
        },
        "outputs": {
            "manifest": ".tmp/freecad_gears/provider-smoke/involute_spur.json",
            "step": ".tmp/freecad_gears/provider-smoke/involute_spur.step"
        }
    }
    path = root / "involute_spur.request.json"
    path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return run_request(tool, path)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="FreeCAD Gears provider setup and inspection driver")
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
            print(json.dumps(run_request(tool, helper_tool.safe_repo_path(arguments.request, "FreeCAD Gears request")), indent=2, sort_keys=True))
            return 0
    except FreeCadGearsError as error:
        print(f"freecad_gears provider: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
