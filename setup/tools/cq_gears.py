#!/usr/bin/env python3

from __future__ import annotations

import argparse
import importlib.util
import json
import math
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


class CqGearsError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise CqGearsError(message)


def load_tool(manifest_path: Path) -> dict:
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    tool = helper_tool.validate_manifest(data, manifest_path)
    if tool["id"] != "cq_gears":
        fail(f"CQ_Gears driver received wrong adapter: {tool['id']}")
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


def source_revision(path: Path) -> str | None:
    result = run_capture(["git", "-C", str(path), "rev-parse", "HEAD"])
    return result.stdout.strip() if result.returncode == 0 else None


def source_clean(path: Path) -> bool:
    result = run_capture(["git", "-C", str(path), "status", "--porcelain"])
    return result.returncode == 0 and not result.stdout.strip()


def ensure_sources_ready(tool: dict) -> None:
    primary = tool["_source_path"]
    if source_revision(primary) != tool["source"]["pinned_revision"]:
        fail("CQ_Gears source revision does not match the adapter pin.")
    if not source_clean(primary):
        fail("CQ_Gears source has local modifications.")
    for source in tool["provider"]["setup"].get("secondary_sources", []):
        path = REPO_ROOT / source["path"]
        if source_revision(path) != source["pinned_revision"]:
            fail(f"Secondary source revision mismatch: {source['path']}")
        if not source_clean(path):
            fail(f"Secondary source has local modifications: {source['path']}")
        if not (path / source["license_file"]).is_file():
            fail(f"Secondary source license is missing: {source['path']}/{source['license_file']}")


def setup(tool: dict) -> dict:
    ensure_sources_ready(tool)
    provider, fingerprint, environment, _ = provider_paths(tool)
    provider.cleanup_incomplete_staging()
    provider.cache_root().mkdir(parents=True, exist_ok=True)
    provider.temp_root().mkdir(parents=True, exist_ok=True)
    provider.log_root().mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="cq-gears-", dir=provider.staging_root()) as stage_text:
        stage = Path(stage_text)
        site_packages = stage / "site-packages"
        site_packages.mkdir()
        install_log = provider.log_root() / "install.log"
        dependency_command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--target",
            str(site_packages),
            "--requirement",
            str(REPO_ROOT / "setup" / "tools" / "cq-gears-requirements.lock"),
        ]
        local_command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--no-deps",
            "--target",
            str(site_packages),
            str(REPO_ROOT / "third_party" / "cadquery"),
            str(REPO_ROOT / "third_party" / "cq_gears"),
        ]
        with install_log.open("w", encoding="utf-8") as log:
            dependency_result = subprocess.run(
                dependency_command,
                cwd=REPO_ROOT,
                check=False,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                env=python_environment(),
            )
            if dependency_result.returncode == 0:
                local_result = subprocess.run(
                    local_command,
                    cwd=REPO_ROOT,
                    check=False,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True,
                    env=python_environment(),
                )
            else:
                local_result = dependency_result
        if dependency_result.returncode or local_result.returncode:
            fail(f"CadQuery/CQ_Gears installation failed; see {install_log.relative_to(REPO_ROOT)}")
        import_result = run_capture(
            [sys.executable, "-c", "import cadquery; import cq_gears; import numpy"],
            site_packages=site_packages,
        )
        if import_result.returncode:
            fail(import_result.stderr.strip() or import_result.stdout.strip() or "CadQuery/CQ_Gears import failed")
        package_result = run_capture(
            [
                sys.executable,
                "-m",
                "pip",
                "list",
                "--path",
                str(site_packages),
                "--format",
                "json",
                "--disable-pip-version-check",
            ]
        )
        if package_result.returncode:
            fail("Could not record CadQuery/CQ_Gears package versions.")
        marker = {
            "schema_version": 1,
            "tool_id": "cq_gears",
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


def reject_non_planar(request: dict) -> None:
    unsupported = {"helical", "herringbone", "bevel", "worm", "crossed_helical", "hyperbolic"}
    gear_type = request.get("gear_type")
    if gear_type in unsupported:
        fail(f"Unsupported non-planar gear type: {gear_type}")
    if gear_type not in {"spur", "ring", "rack", "meshing_pair"}:
        fail(f"Unsupported gear type: {gear_type}")


def gear_points(request: dict, site_packages: Path):
    sys.path.insert(0, str(site_packages))
    from cq_gears import RackGear, RingGear, SpurGear

    params = request["parameters"]
    module = float(params["module"])
    pressure_angle = float(params.get("pressure_angle", 20.0))
    backlash = float(params.get("backlash", 0.0))
    clearance = float(params.get("clearance", 0.0))
    width = float(params.get("width", 3.0))
    if request["gear_type"] == "spur":
        gear = SpurGear(
            module,
            int(params["teeth"]),
            width,
            pressure_angle=pressure_angle,
            backlash=backlash,
            clearance=clearance,
            addendum_coeff=params.get("addendum_coeff"),
            dedendum_coeff=params.get("dedendum_coeff"),
        )
        points = gear.gear_points()
        metrics = circular_metrics(module, int(params["teeth"]), float(params.get("bore", 0.0)))
    elif request["gear_type"] == "ring":
        teeth = int(params["teeth"])
        gear = RingGear(
            module,
            teeth,
            width,
            float(params.get("rim_width", module * 3.0)),
            pressure_angle=pressure_angle,
            backlash=backlash,
            clearance=clearance,
        )
        points = gear.gear_points()
        metrics = circular_metrics(module, teeth, float(params.get("bore", 0.0)))
        metrics["rim_width"] = float(params.get("rim_width", module * 3.0))
    elif request["gear_type"] == "rack":
        length = float(params["length"])
        gear = RackGear(
            module,
            length,
            width,
            float(params.get("rack_height", module * 4.0)),
            pressure_angle=pressure_angle,
            backlash=backlash,
            clearance=clearance,
        )
        points = gear.gear_points()
        metrics = {"length": length, "tooth_count": int(gear.z), "module": module}
    else:
        pinion = int(params["pinion_teeth"])
        ring = int(params.get("ring_teeth", pinion * 2))
        gear = SpurGear(module, pinion, width, pressure_angle=pressure_angle, backlash=backlash, clearance=clearance)
        points = gear.gear_points()
        metrics = circular_metrics(module, pinion, float(params.get("bore", 0.0)))
        metrics["mate_teeth"] = ring
        metrics["center_distance"] = module * (pinion + ring) / 2.0
    return [(float(x), float(y)) for x, y, *_ in points], metrics


def circular_metrics(module: float, teeth: int, bore: float) -> dict:
    pitch = module * teeth
    return {
        "module": module,
        "tooth_count": teeth,
        "pitch_diameter": pitch,
        "outside_diameter": pitch + 2.0 * module,
        "root_diameter": pitch - 2.5 * module,
        "bore": bore,
    }


def write_svg(points: list[tuple[float, float]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    min_x = min(x for x, _ in points)
    min_y = min(y for _, y in points)
    max_x = max(x for x, _ in points)
    max_y = max(y for _, y in points)
    width = max_x - min_x
    height = max_y - min_y
    shifted = [(x - min_x, max_y - y) for x, y in points]
    payload = " ".join(f"{x:.6f},{y:.6f}" for x, y in shifted)
    path.write_text(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.6f}mm" height="{height:.6f}mm" '
        f'viewBox="0 0 {width:.6f} {height:.6f}">\n'
        f'  <polyline points="{payload}" fill="none" stroke="rgb(0,0,0)" stroke-width="0.01"/>\n'
        "</svg>\n",
        encoding="utf-8",
    )


def run_request(tool: dict, request_path: Path) -> dict:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    reject_non_planar(request)
    helper_tool.validate_helper_request(
        tool,
        {
            "schema_version": 1,
            "tool_id": "cq_gears",
            "request_type": "planar_profile",
            "inputs": [str(request_path.relative_to(REPO_ROOT))],
            "outputs": [request["outputs"]["svg"], request["outputs"]["manifest"]],
        },
    )
    _, _, environment, site_packages = provider_paths(tool)
    if not (environment / "provider-ready.json").is_file():
        fail("CQ_Gears provider environment is not invocation-ready.")
    points, metrics = gear_points(request, site_packages)
    if len(points) < 4:
        fail("Generated profile has too few points.")
    svg_path = helper_tool.safe_repo_path(request["outputs"]["svg"], "CQ_Gears SVG output")
    manifest_path = helper_tool.safe_repo_path(request["outputs"]["manifest"], "CQ_Gears manifest output")
    write_svg(points, svg_path)
    manifest = {
        "schema_version": 1,
        "tool_id": "cq_gears",
        "request_sha256": helper_tool.hashlib.sha256(request_path.read_bytes()).hexdigest(),
        "source_revision": tool["source"]["pinned_revision"],
        "metrics": metrics,
        "point_count": len(points),
        "svg_sha256": helper_tool.hashlib.sha256(svg_path.read_bytes()).hexdigest(),
        "fabrication_approved": False,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def smoke(tool: dict) -> dict:
    provider, _, _, _ = provider_paths(tool)
    root = REPO_ROOT / ".tmp" / "cq_gears" / "provider-smoke"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    request = {
        "schema_version": 1,
        "tool_id": "cq_gears",
        "request_type": "planar_profile",
        "gear_type": "spur",
        "parameters": {"module": 2.0, "teeth": 18, "width": 3.0, "bore": 5.0, "backlash": 0.05},
        "outputs": {
            "svg": ".tmp/cq_gears/provider-smoke/spur.svg",
            "manifest": ".tmp/cq_gears/provider-smoke/spur.json"
        }
    }
    request_path = root / "request.json"
    request_path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return run_request(tool, request_path)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="CadQuery/CQ_Gears provider setup and invocation driver")
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
            print(json.dumps(run_request(tool, helper_tool.safe_repo_path(arguments.request, "CQ_Gears request")), indent=2, sort_keys=True))
            return 0
    except CqGearsError as error:
        print(f"cq_gears provider: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
