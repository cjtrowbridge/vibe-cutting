---
plan_id: 2026-07-09-10-30-00_add-png-svg-build-artifacts
title: "Generate Operation-Specific PNG and SVG Artifacts"
summary: "Augment the build pipeline to produce .png files for engraving operations and .svg files for cutting operations, in addition to existing G-code artifacts."
status: future
created_at: 2026-07-09-10-30-00
---

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

### Plan

**Phase 1: Investigation and Discovery (Read-Only)**

- `[ ]` Analyze `scripts/laser_build.py` to identify the operation processing loop and existing artifact generation logic.
- `[ ]` Analyze a sample design configuration to determine how engraving and cutting operations are defined and differentiated.
- `[ ]` Review `setup/pixi.toml` to list current SVG/image libraries and identify any missing dependencies for SVG-to-PNG conversion.

**Phase 2: Implementation**

- `[ ]` Propose and receive approval for adding any new dependencies (e.g., `cairosvg`) to `setup/pixi.toml`.
- `[ ]` In `scripts/laser_build.py`, add conditional logic within the main operation loop to distinguish between engraving, cutting, and other operations.
- `[ ]` For engraving operations, implement the logic to isolate the operation's geometry and render it as a `.png` file in the `operations` output directory.
- `[ ]` For cutting operations, implement the logic to isolate the operation's geometry and save it as a new `.svg` file in the `operations` output directory.
- `[ ]` Add a new test case to `tests/test_laser_build.py` that runs a build and asserts that the expected `.png` and `.svg` files are created in the output directory.

**Phase 3: Verification**

- `[ ]` Run the modified build script for the `shot_coins` design.
- `[ ]` Verify that the `output/shot_coins/operations/` directory contains the expected `.png`, `.svg`, and `.gcode` files.
- `[ ]` Manually inspect the generated image artifacts to confirm they are correct (e.g., transparency on PNGs, correct paths in SVGs).
- `[ ]` Run the entire test suite, including the new test case, to ensure no regressions were introduced.

**Phase 4: Documentation**

- `[ ]` Update `README.md` to list the `.png` and `.svg` files as part of the standard build output.
- `[ ]` Update `docs/build-script-reference.md` with a more detailed description of the new artifacts.
- `[ ]` Review `playbooks/how_to_build_and_audit_a_laser_job.md` and update it to include checking the new image files as part of the audit process.
