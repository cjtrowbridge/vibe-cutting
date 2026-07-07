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
6. Inspect `preview.png`, `design.svg`, `operations.csv`, and `material_setup.md`.
7. Confirm manifests include helper ID, revision, invocation/config hash, and source-output hash when applicable.
8. Run `setup/bootstrap.sh run -- scripts/laser_build.py --design <name> --audit-only`.
9. Do not stream `job.gcode` until machine and material acceptance gates pass.

## Verification

- Exact artifact inventory and hashes pass.
- Helper provenance matches the adapter manifest and checked-out submodule.
- Bounds stay inside the effective machine/stock area.
- Engraving precedes cutting.
- Rapid moves occur with the laser off.
- The build manifest reports readiness honestly.

## Failure

Do not install partial outputs. Preserve the staged failure evidence and follow `playbooks/debugging_changes_that_lead_to_errors.md`.
