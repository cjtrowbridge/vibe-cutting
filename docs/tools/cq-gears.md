# CadQuery + CQ_Gears Provider

CadQuery + CQ_Gears supplies source geometry for planar involute mechanism parts. It is a provider helper, not a fabrication authority.

## Supported Phase 4 Subset

- Spur gears with zero helix angle.
- Ring gears with zero helix angle.
- Racks with zero helix angle.
- Simple meshing-pair metrics for planar mechanism planning.

Unsupported requests fail closed: helical, herringbone, bevel, worm, crossed-helical, hyperbolic, and other non-planar gear classes.

## Setup

```bash
setup/bootstrap.sh run -- scripts/helper_tool.py setup cq_gears
setup/bootstrap.sh run -- scripts/helper_tool.py check cq_gears
```

Setup may download CadQuery/OCP dependencies into `.tools/environments/cq_gears/<fingerprint>/`. It installs the pinned local `third_party/cadquery` and `third_party/cq_gears` sources without modifying either submodule.

## Smoke Test

```bash
setup/bootstrap.sh run -- setup/tools/cq_gears.py smoke --manifest tool_adapters/cq_gears.json
```

The smoke test generates `.tmp/cq_gears/provider-smoke/spur.svg` and a JSON manifest with pitch diameter, outside diameter, root diameter, bore, point count, request hash, and output hash.

## Boundary

CQ_Gears outputs are source geometry and provenance only. The host must still normalize operations, validate clearances, attach material and machine recipes, generate previews and G-code, and audit artifacts before any fabrication use.
