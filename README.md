# vibe-cutting

A configuration-driven pipeline for designing, previewing, validating, and revising laser-cut and laser-engraved projects.

The current vector MVP uses one Python build entrypoint. Native stroke-font designs remain dependency-free; the default coin revisions use OpenSCAD to shape a pinned Liberation Sans Regular font. Specialized third-party helpers can be invoked as separate pinned tools for geometry the native backend does not provide. The pipeline generates fabrication artifacts but never connects to or controls a laser.

## Quick Start

Requires Python 3.11 or newer. The default coin revisions also require OpenSCAD 2021.01 or newer.

Initialize all pinned tools and references after cloning:

```bash
git submodule update --init --recursive
```

```bash
python3 scripts/laser_build.py --design shot_coins --validate-only
python3 scripts/laser_build.py --design shot_coins
python3 scripts/laser_build.py --design shot_coins --audit-only
```

The normal build creates `output/shot_coins/` with:

- `design.svg` and `preview.png`
- `job.gcode`
- `job_manifest.json` and `build_manifest.json`
- `operations.csv` and `material_setup.md`

Use `--new-revision` to create a new immutable design config and matching artifact snapshot. See `docs/build-script-reference.md` for all supported options.

## First Design

`shot_coins` lays out 30 mm coins engraved with “good for one free shot anywhere any time.” Revision `rev_0005` uses OpenSCAD-shaped Liberation Sans Regular with deterministic horizontal hatch engraving. Regular weight improves character separation without forcing the complete text block to shrink for added spacing. It rejects any engraving segment that crosses the configured 1 mm inset from the coin edge. The configured 300 x 300 x 3 mm basswood sheet is larger than the Falcon A1 Pro's provisional 268 mm short-axis work area, so the layout uses the safe 300 x 268 mm intersection. It fits 81 coins with the configured 2 mm margins and 1 mm spacing.

`hug_coins` revision `rev_0003` uses the same geometry, font, material, machine, layout, and containment rules while substituting “hug” for “shot”:

```bash
python3 scripts/laser_build.py --design hug_coins
```

Three reusable merit-badge sets use 72 x 42 mm rounded tokens, measured title/body wrapping, and deterministic 24-slot allocation:

```bash
python3 scripts/laser_build.py --design bwb_merit_badges
python3 scripts/laser_build.py --design queer_sex_party_merit_badges
python3 scripts/laser_build.py --design community_garden_merit_badges
```

Copy an existing merit-badge design and replace its `badges` list to create another set. See `docs/designs/merit-badge-sheets.md`.

## Helper Tools

Callable helper tools remain separate third-party repositories and run in subprocesses through a common host interface:

```bash
python3 scripts/helper_tool.py list
python3 scripts/helper_tool.py check boxes
python3 scripts/helper_tool.py setup boxes
python3 scripts/helper_tool.py run boxes -- --list
```

`setup` may download Python dependencies into `.tmp/helper-tools/`; it does not install into the host project or modify the submodule.

Boxes.py provides parametric boxes, trays, shelves, fitted panels, finger joints, living hinges, gears, and related laser-cut structures. Its SVG is an input to the host pipeline—not authoritative G-code. See `docs/helper-tools.md` and `docs/tools/boxes.md`.

## Safety

The included Falcon A1 Pro profile is provisional, and the basswood recipes are unverified manufacturer seed values. Generated jobs are calibration-only until machine limits, material settings, ventilation, focus, framing, and emergency procedures are physically verified.

Always inspect the preview and setup checklist, run non-emitting framing, and keep the machine actively supervised. See `docs/safety/material-safety.md`.

The 0.18 mm normal-font hatch spacing is also unverified. Calibrate filled engraving before running either normal-font coin sheet.

## Architecture

The native vector backend remains the dependency-free fallback. The OpenSCAD font adapter exports pinned-font contours, normalizes them into the framework coordinate system, and converts filled glyphs into deterministic engraving hatches. Callable helpers such as Boxes.py supply specialized source geometry through pinned subprocess adapters. LaserGRBL is the preferred open application for independently previewing and streaming the generated GRBL G-code.

The bundled Liberation Sans Regular and Bold files remain separately licensed under SIL OFL 1.1; see `assets/fonts/liberation-sans/`.

See `docs/architecture.md` and `plans/future/2026-06-30-12-38-13_build-portable-laser-fabrication-framework.md` for the architecture and longer-term roadmap.
