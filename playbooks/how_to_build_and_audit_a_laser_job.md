# Playbook: Build and Audit a Laser Job

*Status: MVP*

## Objective

Generate a complete, deterministic artifact set without controlling hardware.

## Procedure

1. Confirm the active plan approves the design and build scope.
2. Run `python3 scripts/laser_build.py --design <name> --validate-only`.
3. Run the normal build.
4. Inspect `preview.png`, `design.svg`, `operations.csv`, and `material_setup.md`.
5. Run `python3 scripts/laser_build.py --design <name> --audit-only`.
6. Do not stream `job.gcode` until machine and material acceptance gates pass.

## Verification

- Exact artifact inventory and hashes pass.
- Bounds stay inside the effective machine/stock area.
- Engraving precedes cutting.
- Rapid moves occur with the laser off.
- The build manifest reports readiness honestly.

## Failure

Do not install partial outputs. Preserve the staged failure evidence and follow `playbooks/debugging_changes_that_lead_to_errors.md`.
