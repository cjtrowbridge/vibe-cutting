# Playbook: Use CQ_Gears for Laser Mechanisms

*Status: Provider MVP*

## Objective

Use the CadQuery + CQ_Gears provider for planar involute gear source profiles while preserving host ownership of mechanism validation and fabrication artifacts.

## Use CQ_Gears When

- A design needs a spur gear, ring gear, rack, or simple planar meshing-pair source profile.
- Mechanism provenance benefits from a CadQuery-backed gear profile.
- The active plan includes downstream host validation for ratio, phase, clearances, collisions, bounds, and operation ordering.

Do not use it for helical, herringbone, bevel, worm, crossed-helical, hyperbolic, or fabrication-approved output.

## Commands

```bash
setup/bootstrap.sh run -- scripts/helper_tool.py validate
setup/bootstrap.sh run -- scripts/helper_tool.py check cq_gears
setup/bootstrap.sh run -- scripts/helper_tool.py setup cq_gears
setup/bootstrap.sh run -- setup/tools/cq_gears.py smoke --manifest tool_adapters/cq_gears.json
```

## Request Rules

- Use `schemas/cq_gears_request.schema.json`.
- Keep inputs and outputs repository-relative.
- Write generated source geometry under `.tmp/`, `output/`, or `revisions/`.
- Treat generated SVG and STEP as provenance until host mechanism validation imports them.
- Record module, teeth, pressure angle, width, bore, backlash, source pins, request hash, and output hashes.

## Verification

- `setup/bootstrap.sh run -- scripts/helper_tool.py check cq_gears` reports `ready: true`.
- Smoke output is deterministic.
- Gear metrics match request parameters.
- Source submodules remain clean.
- Host pipeline still owns machine/material recipes, cut ordering, G-code, and readiness claims.
