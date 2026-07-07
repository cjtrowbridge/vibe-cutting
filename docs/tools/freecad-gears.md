# FreeCAD Gears Provider

FreeCAD Gears is an inspection-only provider for checking FreeCAD workbench behavior and producing non-authoritative provenance artifacts.

## Supported Phase 6 Subset

- Headless `FreeCADCmd` detection inside a managed Pixi environment.
- Headless Python-module fallback when `freecadcmd` is present but cannot execute scripts on the host.
- Isolated FreeCAD user, cache, temp, and log directories under `.tools/`.
- One involute spur gear inspection request.
- JSON inspection manifests and optional STEP provenance.

The provider must not produce authoritative cut geometry, G-code, recipes, or fabrication approval.

## Setup

```bash
setup/bootstrap.sh --allow-downloads setup
setup/bootstrap.sh run -- scripts/helper_tool.py setup freecad_gears
setup/bootstrap.sh run -- scripts/helper_tool.py check freecad_gears
```

Setup may download FreeCAD and Python dependencies into repository-local managed Pixi storage. It uses the pinned `third_party/freecad-gears` source and must not modify the submodule.

## Smoke Test

```bash
setup/bootstrap.sh run -- setup/tools/freecad_gears.py smoke --manifest tool_adapters/freecad_gears.json
```

The smoke test writes `.tmp/freecad_gears/provider-smoke/involute_spur.json` and, when FreeCAD export succeeds, `.tmp/freecad_gears/provider-smoke/involute_spur.step`. The manifest records whether the run used `freecadcmd` directly or the `python_freecad_module` fallback.

## Boundary

FreeCAD Gears is a reference and inspection backend. Host-owned mechanism validation, normalized laser geometry, artifact audit, and G-code generation remain authoritative.
