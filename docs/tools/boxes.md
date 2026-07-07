# Boxes.py Helper

Boxes.py is the first callable helper tool. It supplies mature parametric geometry for fitted laser-cut structures while the host remains responsible for validation and fabrication artifacts.

## Appropriate Uses

- Boxes, trays, shelves, enclosures, racks, and wall storage.
- Finger joints, dovetails, living hinges, tabs, gears, and related parts.
- Material-thickness-aware structural geometry represented by an existing generator.

Use native geometry for simple flat shapes and OpenSCAD for CSG or projected assemblies.

## Setup

Initialize submodules, then inspect readiness:

```bash
git submodule update --init --recursive
setup/bootstrap.sh run -- scripts/helper_tool.py check boxes
```

If the environment is missing:

```bash
setup/bootstrap.sh run -- scripts/helper_tool.py setup boxes
```

Setup may access Python package indexes. It installs under `.tools/environments/boxes/<fingerprint>/` and does not modify `third_party/boxes/`.

## Explore Generators

```bash
setup/bootstrap.sh run -- scripts/helper_tool.py run boxes -- --list
setup/bootstrap.sh run -- scripts/helper_tool.py run boxes -- RegularBox --help
```

## Generate Reproducibly

Single-generator CLI output includes a creation timestamp. Fabrication builds should use a committed or staged YAML generator specification through `--multi-generator`, which enables reproducible output:

```bash
setup/bootstrap.sh run -- scripts/helper_tool.py run boxes -- \
  --multi-generator .tmp/boxes/example/generator.yml \
  .tmp/boxes/example/generated
```

Only SVG is currently accepted for host ingestion.

## Operation Colors

| SVG color | Meaning |
|---|---|
| Black | Outer/release cut |
| Blue | Inner cut |
| Green | Vector engraving |
| Cyan | Deep vector engraving |
| Red | Non-fabricating annotation |

Unknown colors must be rejected until explicitly mapped.

## Kerf and Thickness

Boxes.py needs real material thickness for fitted geometry. For the first adapter version it also owns burn/kerf geometry compensation; the value must come from calibrated job/material data and must not be applied again downstream.

Unverified thickness or burn values produce calibration-only artifacts.

## Boundaries

- Pinned source: `third_party/boxes/`.
- Adapter: `tool_adapters/boxes.json`.
- License: GPL-3.0-or-later, retained in the submodule.
- Runtime: separate subprocess using a managed provider environment under `.tools/`.
- Accepted output: SVG geometry.
- Not accepted: authoritative Boxes.py G-code, direct hardware control, source modifications, or host-process imports.

See `playbooks/how_to_use_boxes_for_laser_geometry.md`.
