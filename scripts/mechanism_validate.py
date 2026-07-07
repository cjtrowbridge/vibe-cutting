#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]


class MechanismValidationError(RuntimeError):
    pass


@dataclass
class Check:
    name: str
    passed: bool
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "passed": self.passed, "message": self.message}


DEFAULT_CONSTRAINTS = {
    "mesh_tolerance_mm": 0.15,
    "ratio_tolerance": 0.001,
    "phase_tolerance_deg": 0.5,
    "min_backlash_mm": 0.05,
    "min_bore_clearance_mm": 0.1,
    "min_tooth_root_mm": 0.8,
    "min_web_mm": 1.2,
    "min_rotating_clearance_mm": 0.5,
}


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise MechanismValidationError(f"missing mechanism file: {path}") from error
    except json.JSONDecodeError as error:
        raise MechanismValidationError(f"invalid mechanism JSON: {error}") from error


def constraints(model: dict[str, Any]) -> dict[str, float]:
    configured = model.get("constraints", {})
    return {key: float(configured.get(key, value)) for key, value in DEFAULT_CONSTRAINTS.items()}


def part_index(model: dict[str, Any]) -> dict[str, dict[str, Any]]:
    parts = model.get("parts", [])
    index = {}
    for part in parts:
        part_id = part.get("id")
        if not part_id:
            raise MechanismValidationError("every mechanism part requires an id")
        if part_id in index:
            raise MechanismValidationError(f"duplicate part id: {part_id}")
        index[part_id] = part
    return index


def require(condition: bool, checks: list[Check], name: str, message: str) -> None:
    checks.append(Check(name, condition, message))


def center(part: dict[str, Any]) -> tuple[float, float]:
    value = part.get("center", [0, 0])
    return float(value[0]), float(value[1])


def distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    ax, ay = center(a)
    bx, by = center(b)
    return math.hypot(ax - bx, ay - by)


def pitch_diameter(part: dict[str, Any]) -> float:
    if "pitch_diameter_mm" in part:
        return float(part["pitch_diameter_mm"])
    if "module_mm" in part and "teeth" in part:
        return float(part["module_mm"]) * int(part["teeth"])
    raise MechanismValidationError(f"part {part.get('id')} lacks pitch diameter data")


def outer_diameter(part: dict[str, Any]) -> float:
    if "outer_diameter_mm" in part:
        return float(part["outer_diameter_mm"])
    if "radius_mm" in part:
        return float(part["radius_mm"]) * 2
    if "module_mm" in part and "teeth" in part:
        return float(part["module_mm"]) * (int(part["teeth"]) + 2)
    raise MechanismValidationError(f"part {part.get('id')} lacks outer diameter data")


def root_diameter(part: dict[str, Any]) -> float:
    if "root_diameter_mm" in part:
        return float(part["root_diameter_mm"])
    if "module_mm" in part and "teeth" in part:
        return max(0.0, float(part["module_mm"]) * (int(part["teeth"]) - 2.5))
    raise MechanismValidationError(f"part {part.get('id')} lacks root diameter data")


def normalize_angle(value: float) -> float:
    return value % 360.0


def angle_delta(a: float, b: float) -> float:
    return abs((a - b + 180.0) % 360.0 - 180.0)


def validate_meshes(model: dict[str, Any], parts: dict[str, dict[str, Any]], checks: list[Check]) -> None:
    config = constraints(model)
    phases = {item["part"]: float(item["phase_deg"]) for item in model.get("phases", [])}
    for mesh in model.get("meshes", []):
        driver = parts.get(mesh["driver"])
        driven = parts.get(mesh["driven"])
        if not driver or not driven:
            require(False, checks, "mesh_parts", f"mesh {mesh['id']} references missing parts")
            continue
        expected_distance = (pitch_diameter(driver) + pitch_diameter(driven)) / 2.0
        actual_distance = float(mesh["center_distance_mm"])
        measured_distance = distance(driver, driven)
        require(
            abs(actual_distance - expected_distance) <= config["mesh_tolerance_mm"]
            and abs(measured_distance - expected_distance) <= config["mesh_tolerance_mm"],
            checks,
            "mesh_distance",
            f"mesh {mesh['id']} expected {expected_distance:.3f} mm, declared {actual_distance:.3f} mm, measured {measured_distance:.3f} mm",
        )
        expected_ratio = -float(driver["teeth"]) / float(driven["teeth"])
        require(
            abs(float(mesh["ratio"]) - expected_ratio) <= config["ratio_tolerance"],
            checks,
            "mesh_ratio",
            f"mesh {mesh['id']} expected ratio {expected_ratio:.6f}, declared {float(mesh['ratio']):.6f}",
        )
        require(
            float(mesh["backlash_mm"]) >= config["min_backlash_mm"],
            checks,
            "mesh_backlash",
            f"mesh {mesh['id']} backlash {float(mesh['backlash_mm']):.3f} mm >= {config['min_backlash_mm']:.3f} mm",
        )
        if "phase_transfer_deg" in mesh and driver["id"] in phases and driven["id"] in phases:
            expected_phase = normalize_angle(phases[driver["id"]] + float(mesh["phase_transfer_deg"]))
            actual_phase = normalize_angle(phases[driven["id"]])
            require(
                angle_delta(expected_phase, actual_phase) <= config["phase_tolerance_deg"],
                checks,
                "phase_transfer",
                f"mesh {mesh['id']} expected driven phase {expected_phase:.3f} deg, declared {actual_phase:.3f} deg",
            )


def validate_clearances(model: dict[str, Any], parts: dict[str, dict[str, Any]], checks: list[Check]) -> None:
    config = constraints(model)
    axles = {part["id"]: part for part in parts.values() if part.get("kind") == "axle"}
    for part in parts.values():
        if part.get("kind") not in {"gear", "rotor", "cam", "ratchet"}:
            continue
        bore = float(part.get("bore_diameter_mm", 0))
        axle_id = part.get("axle")
        if bore and axle_id in axles:
            axle = float(axles[axle_id].get("axle_diameter_mm", 0))
            require(
                bore - axle >= config["min_bore_clearance_mm"],
                checks,
                "bore_clearance",
                f"part {part['id']} bore {bore:.3f} mm clears axle {axle_id} by {bore - axle:.3f} mm",
            )
        web = (root_diameter(part) - bore) / 2.0 if bore else root_diameter(part) / 2.0
        tooth_root = math.pi * float(part.get("module_mm", 1.0)) / 2.0
        require(
            tooth_root >= config["min_tooth_root_mm"],
            checks,
            "tooth_root",
            f"part {part['id']} tooth-root estimate {tooth_root:.3f} mm >= {config['min_tooth_root_mm']:.3f} mm",
        )
        require(
            web >= config["min_web_mm"],
            checks,
            "web_thickness",
            f"part {part['id']} web estimate {web:.3f} mm >= {config['min_web_mm']:.3f} mm",
        )


def validate_collisions(model: dict[str, Any], parts: dict[str, dict[str, Any]], checks: list[Check]) -> None:
    config = constraints(model)
    meshed_pairs = {frozenset((mesh["driver"], mesh["driven"])) for mesh in model.get("meshes", [])}
    rotating = [part for part in parts.values() if part.get("kind") in {"gear", "rotor", "cam", "ratchet"}]
    for index, first in enumerate(rotating):
        for second in rotating[index + 1:]:
            if first.get("layer") != second.get("layer"):
                continue
            if frozenset((first["id"], second["id"])) in meshed_pairs:
                continue
            clearance = distance(first, second) - (outer_diameter(first) + outer_diameter(second)) / 2.0
            require(
                clearance >= config["min_rotating_clearance_mm"],
                checks,
                "rotating_collision",
                f"parts {first['id']} and {second['id']} clearance {clearance:.3f} mm >= {config['min_rotating_clearance_mm']:.3f} mm",
            )


def validate_stackup(model: dict[str, Any], parts: dict[str, dict[str, Any]], checks: list[Check]) -> None:
    layers = {layer["id"]: layer for layer in model["stackup"].get("layers", [])}
    registrations = {part["id"] for part in parts.values() if part.get("kind") == "registration_feature"}
    for part in parts.values():
        require(part.get("layer") in layers, checks, "part_layer", f"part {part['id']} is assigned to layer {part.get('layer')}")
    for layer in layers.values():
        missing = sorted(set(layer.get("registration_ids", [])) - registrations)
        require(not missing, checks, "stack_registration", f"layer {layer['id']} registration ids exist: {', '.join(missing) or 'ok'}")


def validate_channels(model: dict[str, Any], parts: dict[str, dict[str, Any]], checks: list[Check]) -> None:
    channels = {channel["id"]: channel for channel in model.get("channels", [])}
    for interface in model.get("interfaces", []):
        channel = channels.get(interface["channel"])
        part = parts.get(interface["part"])
        require(part is not None, checks, "interface_part", f"interface {interface['id']} references part {interface['part']}")
        require(channel is not None, checks, "interface_channel", f"interface {interface['id']} references channel {interface['channel']}")
        if channel:
            require(
                interface["key"] == channel["key"],
                checks,
                "channel_key",
                f"interface {interface['id']} key matches {interface['channel']}",
            )


def validate_operations(model: dict[str, Any], checks: list[Check]) -> None:
    cut_paths = {}
    for operation in model.get("operations", []):
        if operation["operation"] != "cut":
            continue
        path = operation["source_path"]
        cut_paths.setdefault(path, []).append(operation["id"])
    duplicates = {path: ids for path, ids in cut_paths.items() if len(ids) > 1}
    require(not duplicates, checks, "duplicate_cut_paths", f"duplicate cut paths: {json.dumps(duplicates, sort_keys=True)}")


def validate_helper_geometry(model: dict[str, Any], checks: list[Check]) -> None:
    for item in model.get("helper_geometry", []):
        digest = item.get("request_sha256", "")
        require(
            len(digest) == 64 and all(char in "0123456789abcdef" for char in digest),
            checks,
            "helper_geometry_provenance",
            f"helper artifact {item.get('artifact')} records request hash",
        )


def validation_report(model: dict[str, Any], source_path: Path | None = None) -> dict[str, Any]:
    if model.get("schema_version") != 1:
        raise MechanismValidationError("mechanism schema_version must be 1")
    parts = part_index(model)
    checks: list[Check] = []
    validate_meshes(model, parts, checks)
    validate_clearances(model, parts, checks)
    validate_collisions(model, parts, checks)
    validate_stackup(model, parts, checks)
    validate_channels(model, parts, checks)
    validate_operations(model, checks)
    validate_helper_geometry(model, checks)
    payload = json.dumps(model, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        "schema_version": 1,
        "mechanism_id": model["mechanism_id"],
        "source": str(source_path) if source_path else None,
        "model_sha256": hashlib.sha256(payload).hexdigest(),
        "passed": all(check.passed for check in checks),
        "checks": [check.as_dict() for check in checks],
        "job_manifest_fragment": {
            "mechanism_id": model["mechanism_id"],
            "mechanism_validation_passed": all(check.passed for check in checks),
            "mechanism_check_count": len(checks),
        },
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Validate host-owned laser mechanism models.")
    result.add_argument("mechanism")
    result.add_argument("--output")
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    source = Path(arguments.mechanism)
    if not source.is_absolute():
        source = REPO_ROOT / source
    try:
        report = validation_report(load_json(source), source.relative_to(REPO_ROOT))
    except MechanismValidationError as error:
        print(f"mechanism_validate: {error}", file=sys.stderr)
        return 2
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if arguments.output:
        output = Path(arguments.output)
        if not output.is_absolute():
            output = REPO_ROOT / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
