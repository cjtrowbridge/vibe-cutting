# Playbook: Author and Validate Laser Mechanisms

## Objective

Create a laser-native mechanism design that uses helper geometry only as provenance/source evidence while the host model owns validation and fabrication artifacts.

## Procedure

1. Define the design directory under `designs/<id>/`.
2. Create a mechanism graph under `mechanisms/`.
3. Declare parts, layers, meshes, phases, channels, interfaces, operations, and helper provenance.
4. Run `scripts/mechanism_validate.py` and fix every failing check.
5. Add or update a `mechanism_sheet` design config.
6. Generate helper provenance through typed requests when CQ_Gears, BOSL2, FreeCAD Gears, or another helper influenced geometry.
7. Build with `scripts/laser_build.py --design <id>`.
8. Audit with `scripts/laser_build.py --audit-only --design <id>`.
9. Confirm `job_manifest.json` includes the mechanism validation fragment.
10. Keep readiness `calibration_only` until physical coupons validate fit, kerf, backlash, material settings, and safety procedures.

## Failure Handling

- Stop on failed mechanism validation.
- Stop on dirty helper submodules.
- Stop when helper provenance hashes do not match request files.
- Stop when generated artifacts fail audit.
