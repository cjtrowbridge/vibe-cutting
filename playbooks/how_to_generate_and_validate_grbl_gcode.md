# Playbook: Generate and Validate GRBL G-code

*Status: MVP*

## Objective

Generate deterministic, bounded GRBL artifacts with provable laser state.

## Procedure

1. Pin machine, material, module, and recipe revisions.
2. Emit `G21`, `G90`, and `M5` before motion.
3. Keep every rapid move laser-off.
4. Emit engraving before release cuts.
5. Emit `M5` after every path and at program end.
6. Parse generated bounds and compare them with the manifest.
7. Preview the file in LaserGRBL before supervised hardware use.

## Verification

- No unsupported command exists.
- Power and feed remain within profile limits.
- Final state is laser-off.
- All coordinates remain in bounds.
