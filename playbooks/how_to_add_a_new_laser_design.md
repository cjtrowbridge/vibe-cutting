# Playbook: Add a New Laser Design

*Status: MVP*

## Objective

Create a parameterized design consumed by `scripts/laser_build.py`.

## Procedure

1. Create `designs/<name>/project.json`.
2. Create `designs/<name>/configs/rev_0001.json`.
3. Declare machine and material profile paths.
4. Keep geometry parameters separate from process recipes.
5. Add a design README with build and safety notes.
6. Add deterministic tests for layout, bounds, and expected operations.

## Verification

- `--validate-only`, normal build, and `--audit-only` pass.
- Generated files remain under `.tmp/`, `output/`, or `revisions/`.
- No hardware control occurs.
