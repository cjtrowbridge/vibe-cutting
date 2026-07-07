# Primitive Power Extender Laser 0.1

This is the first laser-native mechanism prototype. It models a two-gear 1:1 phase-transfer mechanism on 3 mm basswood and remains calibration-only.

## Build

```bash
python3 scripts/laser_build.py --design primitive_power_extender_laser_0_1
python3 scripts/laser_build.py --audit-only --design primitive_power_extender_laser_0_1
```

## Validation

The design references `mechanisms/primitive_power_extender.mechanism.json`. The build pipeline validates that graph with `scripts/mechanism_validate.py` before writing laser artifacts and stores the report as `mechanism_validation.json`.

CQ_Gears and BOSL2 request files under `helper_requests/` document the primary and comparison gear provenance used to seed this prototype. The committed laser geometry remains host-owned and calibration-only.
