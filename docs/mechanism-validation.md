# Mechanism Validation

`scripts/mechanism_validate.py` validates host-owned laser mechanism graphs. It should run before mechanism designs are built and again whenever helper geometry, stackup, or part relationships change.

## Command

```bash
setup/bootstrap.sh run -- scripts/mechanism_validate.py designs/primitive_power_extender_laser_0_1/mechanisms/primitive_power_extender.mechanism.json --output .tmp/primitive_power_extender/mechanism-validation.json
```

## Checks

- Mesh center distance matches pitch diameters.
- Mesh ratio matches driver/driven tooth counts.
- Phase transfer matches declared phases.
- Backlash meets minimum tolerance.
- Bore clears declared axle diameter.
- Tooth-root and web estimates meet minimums.
- Same-layer rotating parts avoid unintended collisions.
- Parts reference declared stack layers.
- Stack layers reference existing registration features.
- Interfaces use declared channel keys.
- Duplicate cut paths are rejected as overburn risks.
- Helper geometry includes request hashes and source revisions.

## Build Integration

`mechanism_sheet` designs run this validation during `scripts/laser_build.py`. Passing reports are written as `mechanism_validation.json`, and `job_manifest.json` records the validation fragment.

## Boundary

Validation is necessary but not sufficient for fabrication. It does not prove material settings, kerf, backlash, tooth durability, or safe machine operation.
