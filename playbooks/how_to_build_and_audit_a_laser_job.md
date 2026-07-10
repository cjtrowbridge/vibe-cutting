# Playbook: Build and Audit a Laser Job

*Status: MVP*

## Objective

Generate a complete, deterministic artifact set without controlling hardware.

## Procedure

1. Confirm the active plan approves the design and build scope.
2. For helper-backed designs, run `setup/bootstrap.sh run -- scripts/helper_tool.py check <id>` and verify the expected pin, clean source, install marker, and readiness.
3. Generate helper geometry through its tool-specific playbook and verify deterministic source output.
4. Run `setup/bootstrap.sh run -- scripts/laser_build.py --design <name> --validate-only`.
5. Run the normal build.
6. Inspect `preview.png`, `design.svg`, `operations.csv`, `job_plan.json`, `operations/*.gcode`, `operations/*.png`, `operations/*.svg`, and `material_setup.md`.
7. Confirm manifests include helper ID, revision, invocation/config hash, source-output hash when applicable, operation G-code hashes, sidecar artifact hashes, and pass counts.
8. Run `setup/bootstrap.sh run -- scripts/laser_build.py --design <name> --audit-only`.
9. Do not stream `job.gcode` or any `operations/*.gcode` artifact until machine and material acceptance gates pass.
10. When rerunning an operation artifact, remember it repeats the full pass count listed in its filename and `job_plan.json`.

## Verification

- Exact artifact inventory and hashes pass.
- Helper provenance matches the adapter manifest and checked-out submodule.
- Bounds stay inside the effective machine/stock area.
- Engraving precedes cutting.
- Operation artifacts include operation, material ID, and pass count in filenames.
- Engraving PNG sidecars have transparent backgrounds and contain only engraving geometry.
- Cut SVG sidecars contain only cut geometry.
- `job_plan.json` records rerun semantics for every operation artifact.
- Rapid moves occur with the laser off.
- The build manifest reports readiness honestly.

## Failure

Do not install partial outputs. Preserve the staged failure evidence and follow `playbooks/debugging_changes_that_lead_to_errors.md`.
