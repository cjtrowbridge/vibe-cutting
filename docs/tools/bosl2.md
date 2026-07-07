# BOSL2 OpenSCAD Provider

BOSL2 is a pinned OpenSCAD library provider for comparison gear profiles. It is useful as an independent OpenSCAD geometry source, but it is not the mechanism validator and does not produce fabrication-ready artifacts by itself.

## Supported Phase 5 Subset

- `spur_gear2d()` comparison profiles.
- `ring_gear2d()` comparison profiles.
- `rack2d()` comparison profiles.

Unsupported requests fail closed. Use CQ_Gears for the current primary planar involute gear source profiles.

## Setup

```bash
setup/bootstrap.sh run -- scripts/helper_tool.py setup bosl2
setup/bootstrap.sh run -- scripts/helper_tool.py check bosl2
```

Setup detects the host `openscad` executable and records its version in `.tools/environments/bosl2/<fingerprint>/provider-ready.json`. It does not change user-global OpenSCAD configuration.

## Smoke Test

```bash
setup/bootstrap.sh run -- setup/tools/bosl2.py smoke --manifest tool_adapters/bosl2.json
```

The smoke test writes deterministic SVG comparison profiles under `.tmp/bosl2/provider-smoke/`.

## Boundary

BOSL2-generated SVG is source geometry for comparison and inspection. The host must still normalize operations, validate mechanism constraints, attach material and machine recipes, generate previews and G-code, and audit artifacts before fabrication.
