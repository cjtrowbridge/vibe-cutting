# Architecture

`scripts/laser_build.py` is the single user-facing entrypoint. The current dependency-free vector backend loads a design configuration, machine profile, and material profile; creates deterministic geometry and layout; validates bounds and recipes; generates SVG, PNG preview, GRBL G-code, setup documents, and manifests; stages the complete artifact set; then atomically installs `output/<design>/` or an immutable revision.

The script never connects to a machine. LaserGRBL is used separately to preview and stream generated G-code.

The `third_party/` submodules are read-only behavioral references and are never imported or required at runtime.

## Coordinate Contract

- Canonical units are millimeters.
- Design and G-code coordinates are absolute, positive-X/right and positive-Y/up, with the origin at the lower-left of the effective work area.
- PNG previews invert Y only for raster display.
- SVG is an interchange and inspection artifact; generated G-code is the canonical machine handoff.
- Effective work area is the intersection of stock dimensions and conservative machine limits.

## Build Lifecycle

1. Resolve `designs/<name>/project.json` and its default numbered config.
2. Load referenced machine and material profiles.
3. Fail closed on missing fields, unsupported characters, incompatible modules, invalid recipes, impossible layouts, or engraving geometry outside its owning shape.
4. Generate geometry and perform deterministic bounded layout.
5. Generate engraving before through-cut operations.
6. Stage the exact artifact set under `.tmp/laser/<design>/`.
7. Hash sources and artifacts, then audit the staged inventory.
8. Atomically replace `output/<design>/` or install an immutable `revisions/<design>/<revision>/`.
9. Audit the installed files.

## Backend Boundary

The native vector backend proves the pipeline without external runtime dependencies. OpenSCAD remains an optional future geometry frontend for parameterized parts and projected assemblies. An OpenSCAD adapter will export operation geometry into the same validation, layout, manifest, and G-code stages rather than owning process recipes or machine control.

The current design schema and geometry implementation are intentionally narrow. Future design types should add replaceable geometry adapters rather than embedding machine-specific behavior in design files.
