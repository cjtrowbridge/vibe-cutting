#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import math
import shutil
import struct
import tempfile
import zlib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT_NAMES = {
    "design.svg",
    "preview.png",
    "job.gcode",
    "job_manifest.json",
    "operations.csv",
    "material_setup.md",
}
FONT = {
    "A": (((0, 0), (0, 4), (2, 6), (4, 4), (4, 0)), ((0, 3), (4, 3))),
    "D": (((0, 0), (0, 6), (2.8, 6), (4, 5), (4, 1), (2.8, 0), (0, 0)),),
    "E": (((4, 6), (0, 6), (0, 0), (4, 0)), ((0, 3), (3.2, 3))),
    "F": (((4, 6), (0, 6), (0, 0)), ((0, 3), (3.2, 3))),
    "G": (((4, 5), (3, 6), (1, 6), (0, 5), (0, 1), (1, 0), (4, 0), (4, 3), (2.5, 3)),),
    "H": (((0, 0), (0, 6)), ((4, 0), (4, 6)), ((0, 3), (4, 3))),
    "I": (((0, 6), (4, 6)), ((2, 6), (2, 0)), ((0, 0), (4, 0))),
    "M": (((0, 0), (0, 6), (2, 3), (4, 6), (4, 0)),),
    "N": (((0, 0), (0, 6), (4, 0), (4, 6)),),
    "O": (((1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5), (4, 1), (3, 0), (1, 0)),),
    "R": (((0, 0), (0, 6), (3, 6), (4, 5), (4, 4), (3, 3), (0, 3)), ((2.5, 3), (4, 0))),
    "S": (((4, 5), (3, 6), (1, 6), (0, 5), (0, 4), (1, 3), (3, 3), (4, 2), (4, 1), (3, 0), (1, 0), (0, 1)),),
    "T": (((0, 6), (4, 6)), ((2, 6), (2, 0))),
    "U": (((0, 6), (0, 1), (1, 0), (3, 0), (4, 1), (4, 6)),),
    "W": (((0, 6), (1, 0), (2, 3), (3, 0), (4, 6)),),
    "Y": (((0, 6), (2, 3), (4, 6)), ((2, 3), (2, 0))),
    " ": (),
}


def fail(message):
    raise SystemExit(message)


def load_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"Missing JSON file: {path}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON file {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"JSON root must be an object: {path}")
    return data


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(data, keys, label):
    missing = [key for key in keys if key not in data]
    if missing:
        fail(f"{label} missing required fields: {', '.join(missing)}")


def resolve_design(design_name, config_arg=None):
    design_root = REPO_ROOT / "designs" / design_name
    project_path = design_root / "project.json"
    project = load_json(project_path)
    require(project, ["id", "default_config", "machine_profile", "material_profile"], "Project")
    config_path = Path(config_arg) if config_arg else design_root / project["default_config"]
    if not config_path.is_absolute():
        config_path = (REPO_ROOT / config_path).resolve()
    machine_path = (design_root / project["machine_profile"]).resolve()
    material_path = (design_root / project["material_profile"]).resolve()
    return {
        "root": design_root,
        "project_path": project_path,
        "project": project,
        "config_path": config_path,
        "config": load_json(config_path),
        "machine_path": machine_path,
        "machine": load_json(machine_path),
        "material_path": material_path,
        "material": load_json(material_path),
    }


def validate_context(context):
    config = context["config"]
    machine = context["machine"]
    material = context["material"]
    require(
        config,
        [
            "revision",
            "coin_diameter_mm",
            "sheet_width_mm",
            "sheet_height_mm",
            "edge_margin_mm",
            "coin_gap_mm",
            "engraving_inset_mm",
            "layout",
            "quantity",
            "text_lines",
        ],
        "Design config",
    )
    require(machine, ["id", "work_area_mm", "power_scale", "modules", "grbl"], "Machine profile")
    require(material, ["id", "composition_known", "thickness_mm", "compatible_modules", "recipes"], "Material profile")
    if not material["composition_known"]:
        fail("Material composition must be known.")
    if config["layout"] != "hex_max":
        fail(f"Unsupported layout: {config['layout']}")
    if config["coin_diameter_mm"] <= 0 or config["coin_gap_mm"] < 0 or config["edge_margin_mm"] < 0:
        fail("Coin diameter, gap, and margin values are invalid.")
    if not 0 < config["engraving_inset_mm"] < config["coin_diameter_mm"] / 2:
        fail("Engraving inset must be greater than zero and smaller than the coin radius.")
    if not config["text_lines"] or any(not isinstance(line, str) for line in config["text_lines"]):
        fail("text_lines must contain strings.")
    unsupported = sorted({char for line in config["text_lines"] for char in line.upper()} - set(FONT))
    if unsupported:
        fail(f"Unsupported engraving characters: {''.join(unsupported)}")
    module = "blue_20w"
    if module not in machine["modules"] or module not in material["compatible_modules"]:
        fail("The selected machine module and material profile are incompatible.")
    for operation in ("vector_engrave", "through_cut"):
        if operation not in material["recipes"]:
            fail(f"Material profile lacks required recipe: {operation}")
        recipe = material["recipes"][operation]
        if recipe["speed_mm_per_min"] > machine["maximum_speed_mm_per_min"]:
            fail(f"{operation} speed exceeds the machine maximum.")
        if not 0 <= recipe["power_percent"] <= 100:
            fail(f"{operation} power percentage is invalid.")


def compute_layout(config, machine, quantity_override=None):
    diameter = float(config["coin_diameter_mm"])
    gap = float(config["coin_gap_mm"])
    margin = float(config["edge_margin_mm"])
    effective_width = min(float(config["sheet_width_mm"]), float(machine["work_area_mm"]["width"]))
    effective_height = min(float(config["sheet_height_mm"]), float(machine["work_area_mm"]["height"]))
    usable_width = effective_width - 2 * margin
    usable_height = effective_height - 2 * margin
    pitch_x = diameter + gap
    pitch_y = math.sqrt(pitch_x * pitch_x - (pitch_x / 2) ** 2)
    rows = 1 + math.floor((usable_height - diameter) / pitch_y)
    columns = 0
    for candidate in range(1, 10000):
        row_span = diameter + (candidate - 1) * pitch_x
        envelope = row_span + (pitch_x / 2 if rows > 1 else 0)
        if envelope <= usable_width + 1e-9:
            columns = candidate
        else:
            break
    if rows < 1 or columns < 1:
        fail("No coin fits inside the effective work area.")
    row_span = diameter + (columns - 1) * pitch_x
    envelope_width = row_span + (pitch_x / 2 if rows > 1 else 0)
    envelope_height = diameter + (rows - 1) * pitch_y
    x_origin = margin + (usable_width - envelope_width) / 2
    y_origin = margin + (usable_height - envelope_height) / 2
    centers = []
    for row in range(rows):
        offset = pitch_x / 2 if row % 2 else 0
        for column in range(columns):
            centers.append(
                (
                    x_origin + offset + diameter / 2 + column * pitch_x,
                    y_origin + diameter / 2 + row * pitch_y,
                )
            )
    maximum = len(centers)
    requested = maximum if quantity_override is None else int(quantity_override)
    if requested < 1 or requested > maximum:
        fail(f"Requested quantity {requested} is outside the supported range 1-{maximum}.")
    return {
        "centers": centers[:requested],
        "maximum_quantity": maximum,
        "quantity": requested,
        "rows": rows,
        "columns": columns,
        "pitch_x_mm": pitch_x,
        "pitch_y_mm": pitch_y,
        "effective_width_mm": effective_width,
        "effective_height_mm": effective_height,
        "envelope_width_mm": envelope_width,
        "envelope_height_mm": envelope_height,
    }


def text_scale(diameter, lines, inset):
    maximum_units = max((len(line) - 1) * 6 + 4 for line in lines)
    usable_radius = diameter / 2 - inset
    line_gap = 0.75
    low = 0.0
    high = 0.52
    for _ in range(64):
        scale = (low + high) / 2
        width = maximum_units * scale
        height = len(lines) * 6 * scale + (len(lines) - 1) * line_gap
        if math.hypot(width / 2, height / 2) <= usable_radius:
            low = scale
        else:
            high = scale
    if low <= 0:
        fail("Engraving text cannot fit inside the configured coin inset.")
    return low


def text_segments(center, diameter, lines, inset):
    scale = text_scale(diameter, lines, inset)
    line_height = 6 * scale
    line_gap = 0.75
    total_height = len(lines) * line_height + (len(lines) - 1) * line_gap
    top = center[1] + total_height / 2
    segments = []
    for line_index, text in enumerate(lines):
        text = text.upper()
        width = ((len(text) - 1) * 6 + 4) * scale
        left = center[0] - width / 2
        line_top = top - line_index * (line_height + line_gap)
        for character_index, character in enumerate(text):
            character_left = left + character_index * 6 * scale
            for polyline in FONT[character]:
                points = [
                    (
                        character_left + point_x * scale,
                        line_top - (6 - point_y) * scale,
                    )
                    for point_x, point_y in polyline
                ]
                segments.extend(
                    (start_x, start_y, end_x, end_y)
                    for (start_x, start_y), (end_x, end_y) in zip(points, points[1:])
                )
    return segments


def assert_segments_within_circle(segments, center, usable_radius):
    center_x, center_y = center
    for segment_index, segment in enumerate(segments):
        for endpoint_index, (point_x, point_y) in enumerate(
            ((segment[0], segment[1]), (segment[2], segment[3]))
        ):
            distance = math.hypot(point_x - center_x, point_y - center_y)
            if distance > usable_radius + 1e-9:
                fail(
                    "Engraving geometry exceeds its coin boundary: "
                    f"segment={segment_index} endpoint={endpoint_index} "
                    f"distance={distance:.4f}mm limit={usable_radius:.4f}mm"
                )


def all_engraving_segments(config, layout):
    diameter = float(config["coin_diameter_mm"])
    inset = float(config["engraving_inset_mm"])
    usable_radius = diameter / 2 - inset
    segments = []
    for center in layout["centers"]:
        coin_segments = text_segments(center, diameter, config["text_lines"], inset)
        assert_segments_within_circle(coin_segments, center, usable_radius)
        segments.extend(coin_segments)
    return segments


def generate_svg(config, layout, segments):
    width = layout["effective_width_mm"]
    height = layout["effective_height_mm"]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}mm" height="{height:.3f}mm" viewBox="0 0 {width:.3f} {height:.3f}">',
        "<metadata>Engraving first; through cuts second. Units: millimeters.</metadata>",
        f'<g transform="translate(0 {height:.3f}) scale(1 -1)">',
        '<g id="vector_engrave" fill="none" stroke="#0000ff" stroke-width="0.12">',
    ]
    lines.extend(
        f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}"/>'
        for x1, y1, x2, y2 in segments
    )
    lines.append("</g>")
    lines.append('<g id="through_cut" fill="none" stroke="#ff0000" stroke-width="0.12">')
    lines.extend(
        f'<circle cx="{x:.3f}" cy="{y:.3f}" r="{float(config["coin_diameter_mm"]) / 2:.3f}"/>'
        for x, y in layout["centers"]
    )
    lines.extend(["</g>", "</g>", "</svg>"])
    return "\n".join(lines) + "\n"


def power_value(machine, percent):
    scale = machine["power_scale"]
    return round(scale["minimum"] + (scale["maximum"] - scale["minimum"]) * percent / 100)


def generate_gcode(config, machine, material, layout, segments):
    engrave = material["recipes"]["vector_engrave"]
    cut = material["recipes"]["through_cut"]
    engrave_power = power_value(machine, engrave["power_percent"])
    cut_power = power_value(machine, cut["power_percent"])
    lines = [
        "; vibe-cutting deterministic GRBL artifact",
        "G21",
        "G90",
        "M5",
        "; vector_engrave",
        f"F{engrave['speed_mm_per_min']}",
    ]
    for x1, y1, x2, y2 in segments:
        lines.extend(
            [
                "M5",
                f"G0 X{x1:.3f} Y{y1:.3f}",
                f"M4 S{engrave_power}",
                f"G1 X{x2:.3f} Y{y2:.3f}",
                "M5",
            ]
        )
    lines.extend(["; through_cut", f"F{cut['speed_mm_per_min']}"])
    radius = float(config["coin_diameter_mm"]) / 2
    segment_count = 96
    for center_x, center_y in layout["centers"]:
        start_x = center_x + radius
        lines.extend(["M5", f"G0 X{start_x:.3f} Y{center_y:.3f}", f"M4 S{cut_power}"])
        for index in range(1, segment_count + 1):
            angle = 2 * math.pi * index / segment_count
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            lines.append(f"G1 X{x:.3f} Y{y:.3f}")
        lines.append("M5")
    lines.extend(["M5", "G0 X0.000 Y0.000", "M5", "; end"])
    return "\n".join(lines) + "\n"


def set_pixel(image, width, height, x, y, color):
    if 0 <= x < width and 0 <= y < height:
        index = (y * width + x) * 3
        image[index : index + 3] = bytes(color)


def draw_line(image, width, height, x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    sx = 1 if x0 < x1 else -1
    dy = -abs(y1 - y0)
    sy = 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        set_pixel(image, width, height, x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        doubled = 2 * error
        if doubled >= dy:
            error += dy
            x0 += sx
        if doubled <= dx:
            error += dx
            y0 += sy


def png_chunk(chunk_type, payload):
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", zlib.crc32(chunk_type + payload) & 0xFFFFFFFF)


def generate_preview_png(config, layout, segments):
    pixels_per_mm = 3
    width = round(layout["effective_width_mm"] * pixels_per_mm)
    height = round(layout["effective_height_mm"] * pixels_per_mm)
    image = bytearray([255] * width * height * 3)
    for x1, y1, x2, y2 in segments:
        draw_line(
            image,
            width,
            height,
            round(x1 * pixels_per_mm),
            height - 1 - round(y1 * pixels_per_mm),
            round(x2 * pixels_per_mm),
            height - 1 - round(y2 * pixels_per_mm),
            (30, 80, 220),
        )
    radius = float(config["coin_diameter_mm"]) / 2
    for center_x, center_y in layout["centers"]:
        previous = None
        for index in range(145):
            angle = 2 * math.pi * index / 144
            point = (
                round((center_x + radius * math.cos(angle)) * pixels_per_mm),
                height - 1 - round((center_y + radius * math.sin(angle)) * pixels_per_mm),
            )
            if previous:
                draw_line(image, width, height, previous[0], previous[1], point[0], point[1], (220, 30, 30))
            previous = point
    raw = b"".join(b"\x00" + bytes(image[row * width * 3 : (row + 1) * width * 3]) for row in range(height))
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )


def job_manifest(context, layout, segment_count):
    config = context["config"]
    warnings = []
    if config["sheet_width_mm"] > layout["effective_width_mm"] or config["sheet_height_mm"] > layout["effective_height_mm"]:
        warnings.append("Stock exceeds the machine work area; geometry is constrained to the effective intersection.")
    if context["material"]["profile_status"] != "verified":
        warnings.append("Material recipes are unverified manufacturer seed values; calibration is required.")
    return {
        "schema_version": 1,
        "design": context["project"]["id"],
        "revision": config["revision"],
        "machine_profile": context["machine"]["id"],
        "machine_profile_status": context["machine"]["profile_status"],
        "material_profile": context["material"]["id"],
        "material_profile_status": context["material"]["profile_status"],
        "readiness": "calibration_only",
        "stock_mm": [config["sheet_width_mm"], config["sheet_height_mm"], context["material"]["thickness_mm"]],
        "effective_work_area_mm": [layout["effective_width_mm"], layout["effective_height_mm"]],
        "coin_diameter_mm": config["coin_diameter_mm"],
        "engraving_inset_mm": config["engraving_inset_mm"],
        "quantity": layout["quantity"],
        "maximum_quantity": layout["maximum_quantity"],
        "layout": {
            "type": config["layout"],
            "rows": layout["rows"],
            "columns": layout["columns"],
            "gap_mm": config["coin_gap_mm"],
            "edge_margin_mm": config["edge_margin_mm"],
            "envelope_mm": [layout["envelope_width_mm"], layout["envelope_height_mm"]],
        },
        "engraving_text": " ".join(config["text_lines"]).lower(),
        "engraving_segment_count": segment_count,
        "operation_order": ["vector_engrave", "through_cut"],
        "recipes": context["material"]["recipes"],
        "warnings": warnings,
    }


def write_operations(path, material):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["order", "operation", "speed_mm_per_min", "power_percent", "passes", "air_assist"])
        for order, operation in enumerate(("vector_engrave", "through_cut"), 1):
            recipe = material["recipes"][operation]
            writer.writerow(
                [
                    order,
                    operation,
                    recipe["speed_mm_per_min"],
                    recipe["power_percent"],
                    recipe["passes"],
                    recipe["air_assist"],
                ]
            )


def write_setup(path, context, layout):
    path.write_text(
        "\n".join(
            [
                "# Material Setup",
                "",
                f"- Machine: {context['machine']['name']} ({context['machine']['profile_status']})",
                f"- Material: {context['material']['name']} ({context['material']['profile_status']})",
                f"- Stock: {context['config']['sheet_width_mm']} x {context['config']['sheet_height_mm']} x {context['material']['thickness_mm']} mm",
                f"- Effective work area: {layout['effective_width_mm']} x {layout['effective_height_mm']} mm",
                f"- Coin quantity: {layout['quantity']}",
                "- Confirm ventilation, air assist, lens condition, focus, enclosure, emergency stop, and fire response equipment.",
                "- Run a non-emitting frame before fabrication.",
                "- Do not fabricate with these recipes until calibration coupons pass.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def source_records(context):
    paths = [
        Path(__file__).resolve(),
        context["project_path"],
        context["config_path"],
        context["machine_path"],
        context["material_path"],
    ]
    return [{"path": str(path.relative_to(REPO_ROOT)), "sha256": sha256(path)} for path in paths]


def build_manifest(stage, context):
    records = []
    for name in sorted(ARTIFACT_NAMES):
        path = stage / name
        records.append({"path": name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    return {
        "schema_version": 1,
        "build_scope": "complete",
        "design": context["project"]["id"],
        "revision": context["config"]["revision"],
        "sources": source_records(context),
        "artifacts": records,
    }


def audit(directory):
    manifest_path = directory / "build_manifest.json"
    manifest = load_json(manifest_path)
    expected = {"build_manifest.json"} | {record["path"] for record in manifest.get("artifacts", [])}
    actual = {path.name for path in directory.iterdir() if path.is_file()}
    if actual != expected:
        fail(f"Artifact inventory mismatch in {directory}: expected {sorted(expected)}, found {sorted(actual)}")
    for record in manifest["artifacts"]:
        path = directory / record["path"]
        if path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
            fail(f"Artifact audit failed: {path}")
    print(f"[laser] Audit passed: {directory} ({len(expected)} files)")


def install(stage, destination, immutable):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if immutable:
        if destination.exists():
            fail(f"Revision is immutable and already exists: {destination}")
        stage.rename(destination)
        return
    backup = destination.parent / f".{destination.name}.previous"
    if backup.exists():
        shutil.rmtree(backup)
    if destination.exists():
        destination.rename(backup)
    try:
        stage.rename(destination)
    except Exception:
        if backup.exists() and not destination.exists():
            backup.rename(destination)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def next_revision(context):
    configs_dir = context["root"] / "configs"
    maximum = 0
    for path in configs_dir.glob("rev_*.json"):
        try:
            maximum = max(maximum, int(path.stem.split("_")[1]))
        except (IndexError, ValueError):
            continue
    revision = f"rev_{maximum + 1:04d}"
    config_path = configs_dir / f"{revision}.json"
    payload = dict(context["config"])
    payload["revision"] = revision
    write_json(config_path, payload)
    context["config_path"] = config_path
    context["config"] = payload
    return revision


def execute(args):
    context = resolve_design(args.design, args.config)
    if args.new_revision:
        revision = next_revision(context)
    else:
        revision = context["config"]["revision"]
    validate_context(context)
    layout = compute_layout(context["config"], context["machine"], args.quantity)
    print(
        f"[laser] Design={args.design} Revision={revision} Quantity={layout['quantity']} "
        f"Maximum={layout['maximum_quantity']} Area={layout['effective_width_mm']:.1f}x{layout['effective_height_mm']:.1f}mm"
    )
    if args.audit_only:
        audit(REPO_ROOT / "output" / args.design)
        return
    if args.dry_run or args.validate_only:
        print(f"[laser] {'Dry run' if args.dry_run else 'Validation'} passed; no artifacts installed.")
        return
    segments = all_engraving_segments(context["config"], layout)
    temp_parent = REPO_ROOT / ".tmp" / "laser" / args.design
    temp_parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f"{revision}_", dir=temp_parent))
    (stage / "design.svg").write_text(generate_svg(context["config"], layout, segments), encoding="utf-8")
    (stage / "preview.png").write_bytes(generate_preview_png(context["config"], layout, segments))
    (stage / "job.gcode").write_text(
        generate_gcode(context["config"], context["machine"], context["material"], layout, segments),
        encoding="utf-8",
    )
    write_json(stage / "job_manifest.json", job_manifest(context, layout, len(segments)))
    write_operations(stage / "operations.csv", context["material"])
    write_setup(stage / "material_setup.md", context, layout)
    write_json(stage / "build_manifest.json", build_manifest(stage, context))
    audit(stage)
    immutable = bool(args.new_revision)
    destination = (
        REPO_ROOT / "revisions" / args.design / revision
        if immutable
        else REPO_ROOT / "output" / args.design
    )
    install(stage, destination, immutable)
    audit(destination)
    print(f"[laser] Installed complete build: {destination}")


def parse_args():
    parser = argparse.ArgumentParser(description="Build deterministic laser fabrication artifacts.")
    parser.add_argument("--design", required=True)
    parser.add_argument("--config")
    parser.add_argument("--quantity", type=int)
    parser.add_argument("--new-revision", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    modes = sum(bool(value) for value in (args.new_revision, args.validate_only, args.audit_only, args.dry_run))
    if modes > 1:
        parser.error("Select at most one of --new-revision, --validate-only, --audit-only, or --dry-run.")
    return args


if __name__ == "__main__":
    execute(parse_args())
