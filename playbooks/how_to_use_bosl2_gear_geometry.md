# Playbook: Use BOSL2 Gear Geometry

*Status: Provider MVP*

## Objective

Use BOSL2 as an OpenSCAD comparison provider for planar gear profiles without treating its output as fabrication-ready.

## Use BOSL2 When

- You need an independent OpenSCAD comparison profile for a spur gear, ring gear, or rack.
- You are validating another backend’s gear shape at the source-geometry level.
- The active plan explicitly calls for comparison or fallback geometry.

Do not use BOSL2 output as authoritative G-code, machine recipes, material settings, or fabrication approval.

## Commands

```bash
setup/bootstrap.sh run -- scripts/helper_tool.py validate
setup/bootstrap.sh run -- scripts/helper_tool.py check bosl2
setup/bootstrap.sh run -- scripts/helper_tool.py setup bosl2
setup/bootstrap.sh run -- setup/tools/bosl2.py smoke --manifest tool_adapters/bosl2.json
```

## Request Rules

- Use `schemas/bosl2_gear_request.schema.json`.
- Keep inputs and outputs repository-relative.
- Write generated source geometry under `.tmp/`, `output/`, or `revisions/`.
- Preserve `OPENSCADPATH` as a per-process setting; never write user-global OpenSCAD configuration.
- Record BOSL2 source pin, OpenSCAD version, request hash, and SVG hash.

## Verification

- `setup/bootstrap.sh run -- scripts/helper_tool.py check bosl2` reports `ready: true`.
- Smoke output is deterministic.
- The BOSL2 submodule remains clean.
- Host pipeline still owns mechanism validation, operation mapping, material recipes, G-code, and readiness claims.
