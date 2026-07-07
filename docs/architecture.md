# Architecture

`scripts/laser_build.py` is the single design-build entrypoint. On a prepared development host it can be run directly with Python 3.11+, and on a portable clean host it should be invoked through `setup/bootstrap.sh run -- scripts/laser_build.py ...` or `setup/bootstrap.ps1 run -- scripts/laser_build.py ...`. The current dependency-free vector backend loads a design configuration, machine profile, and material profile; creates deterministic geometry and layout; validates bounds and recipes; generates SVG, PNG preview, GRBL G-code, setup documents, and manifests; stages the complete artifact set; then atomically installs `output/<design>/` or an immutable revision.

The script never connects to a machine. LaserGRBL is used separately to preview and stream generated G-code.

Third-party repositories have explicit roles. `vibe-modeling` and LaserGRBL are read-only behavioral references. Boxes.py is a callable helper invoked in a separate process through `scripts/helper_tool.py`; it is never imported into the host process and its output remains untrusted until host validation.

## Bootstrap Boundary

`setup/bootstrap.sh` and `setup/bootstrap.ps1` are native launchers for hosts that have Git but may not have Python or CAD/CAM tools. They verify the host platform and Git version, download only pinned checksum-verified Pixi artifacts after an explicit approval flag, create a locked repository-local Python runtime, initialize submodules through host Git, and write readiness reports beneath `.tools/`.

The managed `run` command dispatches approved repository Python scripts through the locked runtime rather than the host Python installation. Phase 1 qualifies this path on Linux x86-64; other pinned platforms remain pending clean-host qualification.

## Helper-Tool Boundary

`tool_adapters/*.json` declares each callable helper’s source pin, license, capabilities, invocation, accepted outputs, and safety boundaries. `scripts/helper_tool.py` currently verifies the clean submodule pin and installs dependencies into a disposable `.tmp/helper-tools/<id>/` target before invocation. That direct Python helper path is transitional until later provider phases migrate helpers behind the managed bootstrap.

The dependency direction is:

```text
design intent -> callable helper -> source geometry
                                      |
                                      v
                         host operation model
                                      |
                                      v
             layout -> preflight -> artifacts -> G-code
```

Helpers cannot own machine/material recipes, bounds acceptance, operation ordering, authoritative manifests, G-code, readiness claims, or hardware control.

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

The native vector backend proves the pipeline without external runtime dependencies. The implemented OpenSCAD font adapter exports pinned-font SVG contours, accepts only linear path commands, converts SVG Y-down coordinates to the canonical Y-up system, scales multiline text inside its owning circle, and creates deterministic horizontal hatch engraving. Parameterized parts and projected assemblies remain future OpenSCAD adapter work.

The current design schema and geometry implementation are intentionally narrow. Future design types should add replaceable native, OpenSCAD, or callable-helper geometry adapters rather than embedding machine-specific behavior in design files.

## Merit Badge Sets

`merit_badge_set` configs provide a reusable mixed-type sheet mode. The layout engine fills a deterministic rectangular grid and evenly distributes available positions across declared badge types. OpenSCAD measures title and description widths for word wrapping; the pipeline then validates line-box height, text-safe rectangle bounds, rounded-token containment, cut bounds, and non-overlap before artifact installation.

Liberation Sans Bold titles and Regular descriptions are independently pinned and hashed. Rounded-rectangle cut paths and hatch engraving feed the same SVG, PNG, G-code, manifest, staging, and audit pipeline as coin designs.
