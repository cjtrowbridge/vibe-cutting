# vibe-cutting

A configuration-driven pipeline for designing, previewing, validating, and revising laser-cut and laser-engraved projects.

The current vector MVP uses one dependency-free Python entrypoint. It generates fabrication artifacts but never connects to or controls a laser.

## Quick Start

Requires Python 3.11 or newer.

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

`shot_coins` lays out 30 mm coins engraved with “good for one free shot anywhere any time.” Revision `rev_0003` uses upright continuous-line vector lettering and rejects any engraving segment that crosses the configured 1 mm inset from the coin edge. The configured 300 x 300 x 3 mm basswood sheet is larger than the Falcon A1 Pro's provisional 268 mm short-axis work area, so the layout uses the safe 300 x 268 mm intersection. It fits 81 coins with the configured 2 mm margins and 1 mm spacing.

## Safety

The included Falcon A1 Pro profile is provisional, and the basswood recipes are unverified manufacturer seed values. Generated jobs are calibration-only until machine limits, material settings, ventilation, focus, framing, and emergency procedures are physically verified.

Always inspect the preview and setup checklist, run non-emitting framing, and keep the machine actively supervised. See `docs/safety/material-safety.md`.

## Architecture

The native vector backend is the dependency-free baseline. OpenSCAD remains a planned optional parametric geometry adapter; it is not required to build the current design. LaserGRBL is the preferred open application for independently previewing and streaming the generated GRBL G-code.

See `docs/architecture.md` and `plans/future/2026-06-30-12-38-13_build-portable-laser-fabrication-framework.md` for the architecture and longer-term roadmap.
