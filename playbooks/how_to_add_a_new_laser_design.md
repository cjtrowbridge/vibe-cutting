# Playbook: Add a New Laser Design

*Status: MVP*

## Objective

Create a parameterized design consumed by `scripts/laser_build.py`.

## Procedure

1. Review `references/geometry-backend-selection.md` and record the selected backend in the active plan.
2. Run `python3 scripts/helper_tool.py list` when a callable helper may match the required capability.
3. Use `playbooks/how_to_use_boxes_for_laser_geometry.md` for fitted panel assemblies, boxes, trays, shelves, joints, living hinges, and other declared Boxes.py capabilities.
4. Create `designs/<name>/project.json`.
5. Create `designs/<name>/configs/rev_0001.json`.
6. Declare machine, material, geometry backend, and helper-tool bindings.
7. Keep geometry parameters separate from process recipes.
8. Add a design README with build, helper provenance, and safety notes.
9. Add deterministic tests for helper output, operation mapping, layout, bounds, and expected operations.

## Verification

- `--validate-only`, normal build, and `--audit-only` pass.
- Generated files remain under `.tmp/`, `output/`, or `revisions/`.
- Helper-backed designs record tool ID, pinned revision, invocation/config hash, and source-output hash.
- No hardware control occurs.
