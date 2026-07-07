#!/usr/bin/env python3

import argparse
import csv
import hashlib
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ElementTree
import zlib
from pathlib import Path
import importlib.util


REPO_ROOT = Path(__file__).resolve().parent.parent
MECHANISM_VALIDATE_SOURCE = REPO_ROOT / "scripts" / "mechanism_validate.py"
MECHANISM_VALIDATE_SPEC = importlib.util.spec_from_file_location("mechanism_validate", MECHANISM_VALIDATE_SOURCE)
mechanism_validate = importlib.util.module_from_spec(MECHANISM_VALIDATE_SPEC)
sys.modules["mechanism_validate"] = mechanism_validate
MECHANISM_VALIDATE_SPEC.loader.exec_module(mechanism_validate)
OPENSCAD_TEXT_SOURCE = REPO_ROOT / "openscad" / "text_geometry.scad"
OPENSCAD_CONTOUR_CACHE = {}
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


def repo_relative_path(path, label):
    resolved = path.resolve()
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError:
        fail(f"{label} must remain inside the repository: {path}")
    return resolved


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


def openscad_version():
    executable = shutil.which("openscad")
    if executable is None:
        fail("OpenSCAD is required by this design but was not found.")
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        fail(f"Could not determine OpenSCAD version: {exc}")
    output = "\n".join(part for part in (result.stdout, result.stderr) if part)
    match = re.search(r"OpenSCAD version\s+([0-9.]+)", output)
    if result.returncode != 0 or not match:
        fail(f"Could not determine OpenSCAD version: {output.strip()}")
    return match.group(1)


def version_tuple(version):
    try:
        return tuple(int(part) for part in version.split("."))
    except ValueError:
        fail(f"Invalid dotted version: {version}")


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
    config = load_json(config_path)
    config["_design_root"] = str(design_root.relative_to(REPO_ROOT))
    return {
        "root": design_root,
        "project_path": project_path,
        "project": project,
        "config_path": config_path,
        "config": config,
        "machine_path": machine_path,
        "machine": load_json(machine_path),
        "material_path": material_path,
        "material": load_json(material_path),
    }


def validate_pinned_font(config, name_key, file_key, hash_key, label):
    require(config, [name_key, file_key, hash_key], label)
    font_path = (REPO_ROOT / config[file_key]).resolve()
    try:
        font_path.relative_to(REPO_ROOT)
    except ValueError:
        fail(f"{label} file must remain inside the repository.")
    if not font_path.is_file():
        fail(f"Missing {label.lower()} file: {font_path}")
    if sha256(font_path) != config[hash_key]:
        fail(f"Configured {label.lower()} hash does not match: {font_path}")


def validate_context(context):
    config = context["config"]
    machine = context["machine"]
    material = context["material"]
    require(
        config,
        [
            "revision",
            "sheet_width_mm",
            "sheet_height_mm",
            "edge_margin_mm",
            "layout",
            "quantity",
        ],
        "Design config",
    )
    require(machine, ["id", "work_area_mm", "power_scale", "modules", "grbl"], "Machine profile")
    require(material, ["id", "composition_known", "thickness_mm", "compatible_modules", "recipes"], "Material profile")
    if not material["composition_known"]:
        fail("Material composition must be known.")
    design_type = config.get("design_type", "coin_sheet")
    if config["edge_margin_mm"] < 0:
        fail("Sheet edge margin cannot be negative.")
    if design_type == "coin_sheet":
        require(
            config,
            ["coin_diameter_mm", "coin_gap_mm", "engraving_inset_mm", "text_lines"],
            "Coin config",
        )
        if config["layout"] != "hex_max":
            fail(f"Unsupported coin layout: {config['layout']}")
        if config["coin_diameter_mm"] <= 0 or config["coin_gap_mm"] < 0:
            fail("Coin diameter and gap values are invalid.")
        if not 0 < config["engraving_inset_mm"] < config["coin_diameter_mm"] / 2:
            fail("Engraving inset must be greater than zero and smaller than the coin radius.")
        if not config["text_lines"] or any(not isinstance(line, str) for line in config["text_lines"]):
            fail("text_lines must contain strings.")
    elif design_type == "merit_badge_set":
        require(
            config,
            [
                "set_name",
                "token_width_mm",
                "token_height_mm",
                "corner_radius_mm",
                "token_gap_mm",
                "engraving_inset_mm",
                "text_padding_mm",
                "title_font_name",
                "title_font_file",
                "title_font_sha256",
                "title_font_size_mm",
                "title_line_height_mm",
                "body_font_size_mm",
                "body_line_height_mm",
                "section_gap_mm",
                "badges",
            ],
            "Merit badge config",
        )
        if config["layout"] != "grid_fill":
            fail(f"Unsupported merit badge layout: {config['layout']}")
        if config["token_width_mm"] <= 0 or config["token_height_mm"] <= 0 or config["token_gap_mm"] < 0:
            fail("Merit badge token dimensions and gap are invalid.")
        if not 0 <= config["corner_radius_mm"] <= min(config["token_width_mm"], config["token_height_mm"]) / 2:
            fail("Merit badge corner radius is invalid.")
        if not 0 < config["engraving_inset_mm"] < min(config["token_width_mm"], config["token_height_mm"]) / 2:
            fail("Merit badge engraving inset is invalid.")
        if config["text_padding_mm"] < config["corner_radius_mm"]:
            fail("Merit badge text padding must be at least the corner radius.")
        if not config["badges"]:
            fail("Merit badge set must contain at least one badge type.")
        for badge in config["badges"]:
            require(badge, ["id", "title", "description"], "Merit badge")
            if not all(isinstance(badge[key], str) and badge[key].strip() for key in ("id", "title", "description")):
                fail("Merit badge id, title, and description must be non-empty strings.")
        badge_ids = [badge["id"] for badge in config["badges"]]
        if len(set(badge_ids)) != len(badge_ids):
            fail("Merit badge ids must be unique.")
        for key in (
            "title_font_size_mm",
            "title_line_height_mm",
            "body_font_size_mm",
            "body_line_height_mm",
            "section_gap_mm",
        ):
            if config[key] <= 0:
                fail(f"Merit badge typography value must be greater than zero: {key}")
        validate_pinned_font(
            config,
            "title_font_name",
            "title_font_file",
            "title_font_sha256",
            "Title font",
        )
    elif design_type == "mechanism_sheet":
        require(
            config,
            [
                "mechanism_file",
                "mechanism_label",
                "sheet_width_mm",
                "sheet_height_mm",
                "edge_margin_mm",
                "layout",
                "quantity",
                "engraving_inset_mm",
            ],
            "Mechanism config",
        )
        if config["layout"] != "absolute_mechanism":
            fail(f"Unsupported mechanism layout: {config['layout']}")
        mechanism_path = repo_relative_path((context["root"] / config["mechanism_file"]), "Mechanism file")
        mechanism_report = mechanism_validate.validation_report(
            mechanism_validate.load_json(mechanism_path),
            mechanism_path.relative_to(REPO_ROOT),
        )
        if not mechanism_report["passed"]:
            failed = ", ".join(check["name"] for check in mechanism_report["checks"] if not check["passed"])
            fail(f"Mechanism validation failed: {failed}")
    else:
        fail(f"Unsupported design type: {design_type}")
    text_backend = config.get("text_backend", "native_stroke")
    if design_type == "mechanism_sheet":
        pass
    elif text_backend == "native_stroke":
        unsupported = sorted({char for line in config["text_lines"] for char in line.upper()} - set(FONT))
        if unsupported:
            fail(f"Unsupported engraving characters: {''.join(unsupported)}")
    elif text_backend == "openscad_font":
        require(
            config,
            [
                "font_name",
                "font_file",
                "font_sha256",
                "font_fill",
                "hatch_spacing_mm",
                "font_line_gap_ratio",
                "openscad_curve_segments",
                "openscad_minimum_version",
            ],
            "OpenSCAD font config",
        )
        if config["font_fill"] != "horizontal_hatch":
            fail(f"Unsupported font fill: {config['font_fill']}")
        if config["hatch_spacing_mm"] <= 0:
            fail("Font hatch spacing must be greater than zero.")
        if config["font_line_gap_ratio"] < 0:
            fail("Font line gap ratio cannot be negative.")
        if config["openscad_curve_segments"] < 8:
            fail("OpenSCAD curve segments must be at least 8.")
        validate_pinned_font(config, "font_name", "font_file", "font_sha256", "Body font")
        if shutil.which("openscad") is None:
            fail("OpenSCAD is required by this design but was not found.")
        installed_version = openscad_version()
        if version_tuple(installed_version) < version_tuple(config["openscad_minimum_version"]):
            fail(
                f"OpenSCAD {config['openscad_minimum_version']} or newer is required; "
                f"found {installed_version}."
            )
        if not OPENSCAD_TEXT_SOURCE.is_file():
            fail(f"Missing OpenSCAD text source: {OPENSCAD_TEXT_SOURCE}")
    else:
        fail(f"Unsupported text backend: {text_backend}")
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


def compute_coin_layout(config, machine, quantity_override=None):
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
        "placements": [{"center": center} for center in centers[:requested]],
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


def allocate_badge_counts(badges, quantity):
    if quantity < len(badges):
        fail(
            f"Requested quantity {quantity} cannot include all {len(badges)} merit badge types."
        )
    base, remainder = divmod(quantity, len(badges))
    return {
        badge["id"]: base + (1 if index < remainder else 0)
        for index, badge in enumerate(badges)
    }


def compute_merit_badge_layout(config, machine, quantity_override=None):
    token_width = float(config["token_width_mm"])
    token_height = float(config["token_height_mm"])
    gap = float(config["token_gap_mm"])
    margin = float(config["edge_margin_mm"])
    effective_width = min(float(config["sheet_width_mm"]), float(machine["work_area_mm"]["width"]))
    effective_height = min(float(config["sheet_height_mm"]), float(machine["work_area_mm"]["height"]))
    usable_width = effective_width - 2 * margin
    usable_height = effective_height - 2 * margin
    columns = math.floor((usable_width + gap) / (token_width + gap))
    rows = math.floor((usable_height + gap) / (token_height + gap))
    if rows < 1 or columns < 1:
        fail("No merit badge token fits inside the effective work area.")
    maximum = rows * columns
    requested = maximum if quantity_override is None else int(quantity_override)
    if requested < 1 or requested > maximum:
        fail(f"Requested quantity {requested} is outside the supported range 1-{maximum}.")
    badge_counts = allocate_badge_counts(config["badges"], requested)
    envelope_width = columns * token_width + (columns - 1) * gap
    envelope_height = rows * token_height + (rows - 1) * gap
    x_origin = margin + (usable_width - envelope_width) / 2
    y_origin = margin + (usable_height - envelope_height) / 2
    centers = [
        (
            x_origin + token_width / 2 + column * (token_width + gap),
            y_origin + token_height / 2 + row * (token_height + gap),
        )
        for row in range(rows)
        for column in range(columns)
    ][:requested]
    badge_by_id = {badge["id"]: badge for badge in config["badges"]}
    allocated_badges = [
        badge_by_id[badge_id]
        for badge_id, count in badge_counts.items()
        for _ in range(count)
    ]
    placements = [
        {
            "center": center,
            "badge": badge,
            "copy_index": index + 1,
        }
        for badge in config["badges"]
        for index, center in enumerate(
            [
                centers[position]
                for position, allocated_badge in enumerate(allocated_badges)
                if allocated_badge["id"] == badge["id"]
            ]
        )
    ]
    placements.sort(key=lambda placement: centers.index(placement["center"]))
    return {
        "centers": centers,
        "placements": placements,
        "badge_counts": badge_counts,
        "maximum_quantity": maximum,
        "quantity": requested,
        "rows": rows,
        "columns": columns,
        "pitch_x_mm": token_width + gap,
        "pitch_y_mm": token_height + gap,
        "effective_width_mm": effective_width,
        "effective_height_mm": effective_height,
        "envelope_width_mm": envelope_width,
        "envelope_height_mm": envelope_height,
    }


def compute_layout(config, machine, quantity_override=None):
    if config.get("design_type", "coin_sheet") == "mechanism_sheet":
        effective_width = min(float(config["sheet_width_mm"]), float(machine["work_area_mm"]["width"]))
        effective_height = min(float(config["sheet_height_mm"]), float(machine["work_area_mm"]["height"]))
        mechanism = load_json(REPO_ROOT / config["_design_root"] / config["mechanism_file"]) if "_design_root" in config else None
        quantity = len(mechanism.get("parts", [])) if mechanism else int(config.get("quantity", 1))
        return {
            "centers": [],
            "placements": [],
            "maximum_quantity": quantity,
            "quantity": quantity,
            "rows": 1,
            "columns": 1,
            "pitch_x_mm": 0,
            "pitch_y_mm": 0,
            "effective_width_mm": effective_width,
            "effective_height_mm": effective_height,
            "envelope_width_mm": effective_width - 2 * float(config["edge_margin_mm"]),
            "envelope_height_mm": effective_height - 2 * float(config["edge_margin_mm"]),
        }
    if config.get("design_type", "coin_sheet") == "merit_badge_set":
        return compute_merit_badge_layout(config, machine, quantity_override)
    return compute_coin_layout(config, machine, quantity_override)


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


def parse_linear_svg_path(path_data):
    unsupported = sorted(set(re.findall(r"[A-DF-Za-df-z]", path_data)) - set("MLZmlz"))
    if unsupported:
        fail(f"Unsupported OpenSCAD SVG path commands: {''.join(unsupported)}")
    tokens = re.findall(
        r"[MLZmlz]|[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?",
        path_data.replace(",", " "),
    )
    contours = []
    contour = []
    command = None
    index = 0

    def close_contour():
        nonlocal contour
        if not contour:
            return
        if len(contour) < 3:
            fail("OpenSCAD SVG contour has fewer than three points.")
        if contour[-1] != contour[0]:
            contour.append(contour[0])
        contours.append(contour)
        contour = []

    while index < len(tokens):
        token = tokens[index]
        if token.isalpha():
            command = token.upper()
            index += 1
            if command == "Z":
                close_contour()
                command = None
            continue
        if command not in {"M", "L"} or index + 1 >= len(tokens) or tokens[index + 1].isalpha():
            fail("Malformed OpenSCAD SVG path data.")
        point = (float(token), float(tokens[index + 1]))
        index += 2
        if command == "M":
            close_contour()
            contour = [point]
            command = "L"
        else:
            contour.append(point)
    close_contour()
    if not contours:
        fail("OpenSCAD SVG path did not contain any contours.")
    return contours


def render_openscad_text(text, config, font_name=None):
    executable = shutil.which("openscad")
    if executable is None:
        fail("OpenSCAD is required by this design but was not found.")
    selected_font = font_name or config["font_name"]
    cache_key = (text, selected_font, int(config["openscad_curve_segments"]))
    if cache_key in OPENSCAD_CONTOUR_CACHE:
        return OPENSCAD_CONTOUR_CACHE[cache_key]
    with tempfile.TemporaryDirectory(prefix="vibe-cutting-openscad-") as temporary_directory:
        svg_path = Path(temporary_directory) / "text.svg"
        command = [
            executable,
            "-o",
            str(svg_path),
            "-D",
            f"text_value={json.dumps(text)}",
            "-D",
            f"font_name={json.dumps(selected_font)}",
            "-D",
            "font_size=100",
            "-D",
            f"curve_segments={int(config['openscad_curve_segments'])}",
            str(OPENSCAD_TEXT_SOURCE),
        ]
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            fail(f"OpenSCAD text export failed: {exc}")
        diagnostics = "\n".join(part for part in (result.stdout, result.stderr) if part)
        if result.returncode != 0:
            fail(f"OpenSCAD text export failed for {text!r}: {diagnostics.strip()}")
        if "can't find font" in diagnostics.lower():
            fail(f"OpenSCAD could not find configured font: {selected_font}")
        try:
            root = ElementTree.parse(svg_path).getroot()
        except (ElementTree.ParseError, FileNotFoundError) as exc:
            fail(f"OpenSCAD produced invalid SVG for {text!r}: {exc}")
        path_elements = [element for element in root.iter() if element.tag.rsplit("}", 1)[-1] == "path"]
        contours = []
        for element in path_elements:
            path_data = element.get("d")
            if path_data:
                contours.extend(parse_linear_svg_path(path_data))
        if not contours:
            fail(f"OpenSCAD produced no text contours for {text!r}.")
        OPENSCAD_CONTOUR_CACHE[cache_key] = contours
        return contours


def contour_bounds(contours):
    points = [point for contour in contours for point in contour]
    if not points:
        fail("Cannot calculate bounds for empty contours.")
    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]
    return min(x_values), min(y_values), max(x_values), max(y_values)


def hatch_contours(contours, spacing):
    _, minimum_y, _, maximum_y = contour_bounds(contours)
    scanline = (math.floor(minimum_y / spacing) + 1) * spacing
    segments = []
    while scanline < maximum_y - 1e-9:
        intersections = []
        for contour in contours:
            for (start_x, start_y), (end_x, end_y) in zip(contour, contour[1:]):
                if abs(end_y - start_y) <= 1e-12:
                    continue
                crosses = (start_y <= scanline < end_y) or (end_y <= scanline < start_y)
                if crosses:
                    ratio = (scanline - start_y) / (end_y - start_y)
                    intersections.append(start_x + ratio * (end_x - start_x))
        intersections.sort()
        if len(intersections) % 2:
            fail(f"OpenSCAD hatch topology produced an odd intersection count at Y={scanline:.4f}.")
        for start_x, end_x in zip(intersections[::2], intersections[1::2]):
            if end_x - start_x > 1e-9:
                segments.append((start_x, scanline, end_x, scanline))
        scanline += spacing
    if not segments:
        fail("OpenSCAD text hatching produced no engraving segments.")
    return segments


def openscad_font_segments(config):
    shaped_lines = []
    maximum_height = 0.0
    for text in config["text_lines"]:
        contours = render_openscad_text(text, config)
        minimum_x, minimum_y, maximum_x, maximum_y = contour_bounds(contours)
        maximum_height = max(maximum_height, maximum_y - minimum_y)
        shaped_lines.append(
            {
                "contours": contours,
                "center_x": (minimum_x + maximum_x) / 2,
                "center_y": (minimum_y + maximum_y) / 2,
            }
        )
    line_gap = maximum_height * float(config["font_line_gap_ratio"])
    total_height = len(shaped_lines) * maximum_height + (len(shaped_lines) - 1) * line_gap
    combined = []
    for line_index, shaped in enumerate(shaped_lines):
        line_center_y = total_height / 2 - maximum_height / 2 - line_index * (maximum_height + line_gap)
        combined.extend(
            [
                (
                    point_x - shaped["center_x"],
                    shaped["center_y"] - point_y + line_center_y,
                )
                for point_x, point_y in contour
            ]
            for contour in shaped["contours"]
        )
    maximum_radius = max(math.hypot(point_x, point_y) for contour in combined for point_x, point_y in contour)
    usable_radius = float(config["coin_diameter_mm"]) / 2 - float(config["engraving_inset_mm"])
    if maximum_radius <= 0:
        fail("OpenSCAD text geometry has an invalid radius.")
    scale = usable_radius / maximum_radius
    scaled = [
        [(point_x * scale, point_y * scale) for point_x, point_y in contour]
        for contour in combined
    ]
    return hatch_contours(scaled, float(config["hatch_spacing_mm"]))


def centered_scaled_contours(text, config, font_name, font_size_mm):
    contours = render_openscad_text(text, config, font_name)
    minimum_x, minimum_y, maximum_x, maximum_y = contour_bounds(contours)
    center_x = (minimum_x + maximum_x) / 2
    center_y = (minimum_y + maximum_y) / 2
    scale = float(font_size_mm) / 100
    return [
        [
            (
                (point_x - center_x) * scale,
                (center_y - point_y) * scale,
            )
            for point_x, point_y in contour
        ]
        for contour in contours
    ]


def measured_text_width(text, config, font_name, font_size_mm):
    contours = centered_scaled_contours(text, config, font_name, font_size_mm)
    minimum_x, _, maximum_x, _ = contour_bounds(contours)
    return maximum_x - minimum_x


def wrap_measured_text(text, maximum_width, config, font_name, font_size_mm):
    words = text.split()
    if not words:
        fail("Cannot wrap empty merit badge text.")
    lines = []
    current = words[0]
    if measured_text_width(current, config, font_name, font_size_mm) > maximum_width + 1e-9:
        fail(f"Merit badge word is too wide for its token: {current}")
    for word in words[1:]:
        candidate = f"{current} {word}"
        if measured_text_width(candidate, config, font_name, font_size_mm) <= maximum_width + 1e-9:
            current = candidate
            continue
        lines.append(current)
        current = word
        if measured_text_width(current, config, font_name, font_size_mm) > maximum_width + 1e-9:
            fail(f"Merit badge word is too wide for its token: {current}")
    lines.append(current)
    return lines


def merit_badge_relative_segments(config, badge):
    inner_width = float(config["token_width_mm"]) - 2 * float(config["text_padding_mm"])
    inner_height = float(config["token_height_mm"]) - 2 * float(config["text_padding_mm"])
    title_lines = wrap_measured_text(
        badge["title"],
        inner_width,
        config,
        config["title_font_name"],
        config["title_font_size_mm"],
    )
    body_lines = wrap_measured_text(
        badge["description"],
        inner_width,
        config,
        config["font_name"],
        config["body_font_size_mm"],
    )
    title_block_height = len(title_lines) * float(config["title_line_height_mm"])
    body_block_height = len(body_lines) * float(config["body_line_height_mm"])
    total_height = title_block_height + float(config["section_gap_mm"]) + body_block_height
    if total_height > inner_height + 1e-9:
        fail(
            f"Merit badge text does not fit token height: {badge['id']} "
            f"needs {total_height:.3f}mm, has {inner_height:.3f}mm"
        )
    contours = []
    cursor = total_height / 2
    for text in title_lines:
        line_contours = centered_scaled_contours(
            text,
            config,
            config["title_font_name"],
            config["title_font_size_mm"],
        )
        _, minimum_y, _, maximum_y = contour_bounds(line_contours)
        if maximum_y - minimum_y > config["title_line_height_mm"] + 1e-9:
            fail(f"Merit badge title line height is too small: {badge['id']}")
        line_center_y = cursor - float(config["title_line_height_mm"]) / 2
        contours.extend(
            [[(point_x, point_y + line_center_y) for point_x, point_y in contour] for contour in line_contours]
        )
        cursor -= float(config["title_line_height_mm"])
    cursor -= float(config["section_gap_mm"])
    for text in body_lines:
        line_contours = centered_scaled_contours(
            text,
            config,
            config["font_name"],
            config["body_font_size_mm"],
        )
        _, minimum_y, _, maximum_y = contour_bounds(line_contours)
        if maximum_y - minimum_y > config["body_line_height_mm"] + 1e-9:
            fail(f"Merit badge body line height is too small: {badge['id']}")
        line_center_y = cursor - float(config["body_line_height_mm"]) / 2
        contours.extend(
            [[(point_x, point_y + line_center_y) for point_x, point_y in contour] for contour in line_contours]
        )
        cursor -= float(config["body_line_height_mm"])
    segments = hatch_contours(contours, float(config["hatch_spacing_mm"]))
    for segment in segments:
        for point_x, point_y in ((segment[0], segment[1]), (segment[2], segment[3])):
            if abs(point_x) > inner_width / 2 + 1e-9 or abs(point_y) > inner_height / 2 + 1e-9:
                fail(f"Merit badge engraving exceeds its text-safe rectangle: {badge['id']}")
    return {
        "segments": segments,
        "title_lines": title_lines,
        "body_lines": body_lines,
    }


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


def point_inside_rounded_rectangle(point, center, width, height, radius, inset):
    point_x, point_y = point
    center_x, center_y = center
    half_width = width / 2 - inset
    half_height = height / 2 - inset
    inner_radius = max(0.0, radius - inset)
    delta_x = abs(point_x - center_x)
    delta_y = abs(point_y - center_y)
    if delta_x > half_width + 1e-9 or delta_y > half_height + 1e-9:
        return False
    if inner_radius == 0 or delta_x <= half_width - inner_radius or delta_y <= half_height - inner_radius:
        return True
    return (
        math.hypot(
            delta_x - (half_width - inner_radius),
            delta_y - (half_height - inner_radius),
        )
        <= inner_radius + 1e-9
    )


def assert_segments_within_rounded_rectangle(segments, center, width, height, radius, inset):
    for segment_index, segment in enumerate(segments):
        for endpoint_index, point in enumerate(
            ((segment[0], segment[1]), (segment[2], segment[3]))
        ):
            if not point_inside_rounded_rectangle(point, center, width, height, radius, inset):
                fail(
                    "Engraving geometry exceeds its rounded token boundary: "
                    f"segment={segment_index} endpoint={endpoint_index}"
                )


def mechanism_path(config):
    return REPO_ROOT / config["_design_root"] / config["mechanism_file"]


def mechanism_model(config):
    return load_json(mechanism_path(config))


def mechanism_validation_report(config):
    path = mechanism_path(config)
    return mechanism_validate.validation_report(
        mechanism_validate.load_json(path),
        path.relative_to(REPO_ROOT),
    )


def mechanism_part_label_segments(part):
    preferred = {
        "input_rotor": "IN",
        "output_rotor": "OUT",
    }.get(part["id"], part["kind"])
    label = "".join(character for character in preferred.replace("_", " ").upper() if character in FONT)
    if not label.strip():
        return []
    diameter = float(part.get("outer_diameter_mm", part.get("radius_mm", 6) * 2))
    return text_segments(tuple(part["center"]), diameter, [label[:12]], 1.5)


def mechanism_engraving_segments(config, layout):
    model = mechanism_model(config)
    segments = []
    for part in model["parts"]:
        if part["kind"] in {"gear", "rotor", "cam", "ratchet"}:
            segments.extend(mechanism_part_label_segments(part))
    return segments


def all_engraving_segments(config, layout, relative_segments=None):
    if config.get("design_type", "coin_sheet") == "mechanism_sheet":
        return mechanism_engraving_segments(config, layout)
    if config.get("design_type", "coin_sheet") == "merit_badge_set":
        segments = []
        badge_geometry = {}
        for placement in layout["placements"]:
            badge = placement["badge"]
            if badge["id"] not in badge_geometry:
                badge_geometry[badge["id"]] = merit_badge_relative_segments(config, badge)
            center_x, center_y = placement["center"]
            token_segments = [
                (
                    segment[0] + center_x,
                    segment[1] + center_y,
                    segment[2] + center_x,
                    segment[3] + center_y,
                )
                for segment in badge_geometry[badge["id"]]["segments"]
            ]
            assert_segments_within_rounded_rectangle(
                token_segments,
                placement["center"],
                float(config["token_width_mm"]),
                float(config["token_height_mm"]),
                float(config["corner_radius_mm"]),
                float(config["engraving_inset_mm"]),
            )
            segments.extend(token_segments)
        return segments
    diameter = float(config["coin_diameter_mm"])
    inset = float(config["engraving_inset_mm"])
    usable_radius = diameter / 2 - inset
    segments = []
    text_backend = config.get("text_backend", "native_stroke")
    if text_backend == "openscad_font" and relative_segments is None:
        relative_segments = openscad_font_segments(config)
    for center in layout["centers"]:
        if text_backend == "openscad_font":
            coin_segments = [
                (
                    segment[0] + center[0],
                    segment[1] + center[1],
                    segment[2] + center[0],
                    segment[3] + center[1],
                )
                for segment in relative_segments
            ]
        else:
            coin_segments = text_segments(center, diameter, config["text_lines"], inset)
        assert_segments_within_circle(coin_segments, center, usable_radius)
        segments.extend(coin_segments)
    return segments


def circle_path(center, radius, segments):
    center_x, center_y = center
    return [
        (
            center_x + radius * math.cos(2 * math.pi * index / segments),
            center_y + radius * math.sin(2 * math.pi * index / segments),
        )
        for index in range(segments + 1)
    ]


def rounded_rectangle_path(center, width, height, radius, corner_segments):
    center_x, center_y = center
    half_width = width / 2
    half_height = height / 2
    corners = (
        (center_x + half_width - radius, center_y + half_height - radius, 0),
        (center_x - half_width + radius, center_y + half_height - radius, 90),
        (center_x - half_width + radius, center_y - half_height + radius, 180),
        (center_x + half_width - radius, center_y - half_height + radius, 270),
    )
    points = []
    for corner_x, corner_y, start_angle in corners:
        points.extend(
            (
                corner_x + radius * math.cos(math.radians(start_angle + 90 * index / corner_segments)),
                corner_y + radius * math.sin(math.radians(start_angle + 90 * index / corner_segments)),
            )
            for index in range(corner_segments + 1)
        )
    if points[-1] != points[0]:
        points.append(points[0])
    return points


def gear_profile_path(part):
    teeth = int(part.get("teeth", 24))
    outer_radius = float(part.get("outer_diameter_mm", float(part.get("module_mm", 2)) * (teeth + 2))) / 2
    root_radius = float(part.get("root_diameter_mm", max(outer_radius - 2.5 * float(part.get("module_mm", 1)), outer_radius * 0.8))) / 2
    center_x, center_y = part["center"]
    points = []
    for index in range(teeth * 2 + 1):
        radius = outer_radius if index % 2 == 0 else root_radius
        angle = 2 * math.pi * index / (teeth * 2)
        points.append((center_x + radius * math.cos(angle), center_y + radius * math.sin(angle)))
    return points


def mechanism_cut_paths(config):
    model = mechanism_model(config)
    paths = []
    for part in model["parts"]:
        kind = part["kind"]
        if kind == "gear":
            paths.append(gear_profile_path(part))
        elif kind in {"rotor", "cam", "ratchet", "axle", "spacer", "washer", "registration_feature"}:
            radius = float(part.get("radius_mm", part.get("outer_diameter_mm", 3) / 2))
            paths.append(circle_path(tuple(part["center"]), radius, 96))
        bore = float(part.get("bore_diameter_mm", 0))
        if bore > 0:
            paths.append(circle_path(tuple(part["center"]), bore / 2, 64))
    return paths


def cut_paths(config, layout, circle_segments=96, corner_segments=8):
    if config.get("design_type", "coin_sheet") == "merit_badge_set":
        paths = [
            rounded_rectangle_path(
                placement["center"],
                float(config["token_width_mm"]),
                float(config["token_height_mm"]),
                float(config["corner_radius_mm"]),
                corner_segments,
            )
            for placement in layout["placements"]
        ]
    elif config.get("design_type", "coin_sheet") == "mechanism_sheet":
        paths = mechanism_cut_paths(config)
    else:
        radius = float(config["coin_diameter_mm"]) / 2
        paths = [circle_path(center, radius, circle_segments) for center in layout["centers"]]
    for path in paths:
        for point_x, point_y in path:
            if not (
                -1e-9 <= point_x <= layout["effective_width_mm"] + 1e-9
                and -1e-9 <= point_y <= layout["effective_height_mm"] + 1e-9
            ):
                fail(f"Cut geometry exceeds the effective work area at ({point_x:.4f}, {point_y:.4f}).")
    return paths


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
        '<path d="'
        + " ".join(
            [f"M {path[0][0]:.3f},{path[0][1]:.3f}"]
            + [f"L {point_x:.3f},{point_y:.3f}" for point_x, point_y in path[1:]]
            + ["Z"]
        )
        + '"/>'
        for path in cut_paths(config, layout, circle_segments=144, corner_segments=12)
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
    for path in cut_paths(config, layout, circle_segments=96, corner_segments=8):
        lines.extend(["M5", f"G0 X{path[0][0]:.3f} Y{path[0][1]:.3f}", f"M4 S{cut_power}"])
        for point_x, point_y in path[1:]:
            lines.append(f"G1 X{point_x:.3f} Y{point_y:.3f}")
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
    for path in cut_paths(config, layout, circle_segments=144, corner_segments=12):
        previous = None
        for point_x, point_y in path:
            point = (
                round(point_x * pixels_per_mm),
                height - 1 - round(point_y * pixels_per_mm),
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


def job_manifest(context, layout, segment_count, mechanism_report=None):
    config = context["config"]
    warnings = []
    if config["sheet_width_mm"] > layout["effective_width_mm"] or config["sheet_height_mm"] > layout["effective_height_mm"]:
        warnings.append("Stock exceeds the machine work area; geometry is constrained to the effective intersection.")
    if context["material"]["profile_status"] != "verified":
        warnings.append("Material recipes are unverified manufacturer seed values; calibration is required.")
    if config.get("text_backend") == "openscad_font":
        warnings.append("Normal-font hatch spacing is unverified; run an engraving calibration before fabrication.")
    manifest = {
        "schema_version": 1,
        "design": context["project"]["id"],
        "design_type": config.get("design_type", "coin_sheet"),
        "revision": config["revision"],
        "machine_profile": context["machine"]["id"],
        "machine_profile_status": context["machine"]["profile_status"],
        "material_profile": context["material"]["id"],
        "material_profile_status": context["material"]["profile_status"],
        "readiness": "calibration_only",
        "stock_mm": [config["sheet_width_mm"], config["sheet_height_mm"], context["material"]["thickness_mm"]],
        "effective_work_area_mm": [layout["effective_width_mm"], layout["effective_height_mm"]],
        "engraving_inset_mm": config["engraving_inset_mm"],
        "quantity": layout["quantity"],
        "maximum_quantity": layout["maximum_quantity"],
        "layout": {
            "type": config["layout"],
            "rows": layout["rows"],
            "columns": layout["columns"],
            "gap_mm": config.get("coin_gap_mm", config.get("token_gap_mm")),
            "edge_margin_mm": config["edge_margin_mm"],
            "envelope_mm": [layout["envelope_width_mm"], layout["envelope_height_mm"]],
        },
        "engraving_segment_count": segment_count,
        "engraving": {
            "backend": config.get("text_backend", "native_stroke"),
            "font_name": config.get("font_name"),
            "font_file": config.get("font_file"),
            "font_sha256": config.get("font_sha256"),
            "fill": config.get("font_fill", "single_line"),
            "hatch_spacing_mm": config.get("hatch_spacing_mm"),
            "line_gap_ratio": config.get("font_line_gap_ratio"),
            "openscad_version": openscad_version() if config.get("text_backend") == "openscad_font" else None,
            "openscad_minimum_version": config.get("openscad_minimum_version"),
        },
        "operation_order": ["vector_engrave", "through_cut"],
        "recipes": context["material"]["recipes"],
        "warnings": warnings,
    }
    if config.get("design_type", "coin_sheet") == "mechanism_sheet":
        if mechanism_report is None:
            mechanism_report = mechanism_validation_report(config)
        manifest["mechanism"] = mechanism_report["job_manifest_fragment"]
        manifest["mechanism"]["validation_report"] = "mechanism_validation.json"
        manifest["mechanism_label"] = config["mechanism_label"]
        manifest["engraving"]["backend"] = "native_stroke_labels"
    elif config.get("design_type", "coin_sheet") == "merit_badge_set":
        manifest["set_name"] = config["set_name"]
        manifest["token"] = {
            "shape": "rounded_rectangle",
            "width_mm": config["token_width_mm"],
            "height_mm": config["token_height_mm"],
            "corner_radius_mm": config["corner_radius_mm"],
            "text_padding_mm": config["text_padding_mm"],
        }
        manifest["badges"] = [
            {
                "id": badge["id"],
                "title": badge["title"],
                "description": badge["description"],
                "quantity": layout["badge_counts"][badge["id"]],
            }
            for badge in config["badges"]
        ]
        manifest["engraving"]["title_font_name"] = config["title_font_name"]
        manifest["engraving"]["title_font_file"] = config["title_font_file"]
        manifest["engraving"]["title_font_sha256"] = config["title_font_sha256"]
        manifest["engraving"]["title_font_size_mm"] = config["title_font_size_mm"]
        manifest["engraving"]["body_font_size_mm"] = config["body_font_size_mm"]
    else:
        manifest["coin_diameter_mm"] = config["coin_diameter_mm"]
        manifest["engraving_text"] = " ".join(config["text_lines"]).lower()
    return manifest


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
                f"- Token quantity: {layout['quantity']}",
                f"- Engraving backend: {context['config'].get('text_backend', 'native_stroke')}",
                f"- Engraving font: {context['config'].get('font_name', 'built-in continuous-line vector font')}",
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
    if context["config"].get("text_backend") == "openscad_font":
        paths.append(OPENSCAD_TEXT_SOURCE)
        paths.append((REPO_ROOT / context["config"]["font_file"]).resolve())
        if context["config"].get("design_type") == "merit_badge_set":
            paths.append((REPO_ROOT / context["config"]["title_font_file"]).resolve())
    if context["config"].get("design_type") == "mechanism_sheet":
        paths.append(mechanism_path(context["config"]))
    return [{"path": str(path.relative_to(REPO_ROOT)), "sha256": sha256(path)} for path in paths]


def artifact_names(context):
    names = set(ARTIFACT_NAMES)
    if context["config"].get("design_type") == "mechanism_sheet":
        names.add("mechanism_validation.json")
    return names


def build_manifest(stage, context):
    records = []
    for name in sorted(artifact_names(context)):
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
    payload.pop("_design_root", None)
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
    relative_segments = None
    segments = None
    mechanism_report = None
    if context["config"].get("design_type") == "mechanism_sheet":
        mechanism_report = mechanism_validation_report(context["config"])
    if context["config"].get("design_type") == "merit_badge_set":
        segments = all_engraving_segments(context["config"], layout)
    elif context["config"].get("text_backend") == "openscad_font":
        relative_segments = openscad_font_segments(context["config"])
    if args.dry_run or args.validate_only:
        print(f"[laser] {'Dry run' if args.dry_run else 'Validation'} passed; no artifacts installed.")
        return
    if segments is None:
        segments = all_engraving_segments(context["config"], layout, relative_segments)
    temp_parent = REPO_ROOT / ".tmp" / "laser" / args.design
    temp_parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f"{revision}_", dir=temp_parent))
    (stage / "design.svg").write_text(generate_svg(context["config"], layout, segments), encoding="utf-8")
    (stage / "preview.png").write_bytes(generate_preview_png(context["config"], layout, segments))
    (stage / "job.gcode").write_text(
        generate_gcode(context["config"], context["machine"], context["material"], layout, segments),
        encoding="utf-8",
    )
    if mechanism_report is not None:
        write_json(stage / "mechanism_validation.json", mechanism_report)
    write_json(stage / "job_manifest.json", job_manifest(context, layout, len(segments), mechanism_report))
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
