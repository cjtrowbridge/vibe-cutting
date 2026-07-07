# How to Use FreeCAD Gears for Inspection

Use this playbook before invoking `freecad_gears` or interpreting its outputs.

## Procedure

1. Confirm `tool_adapters/freecad_gears.json` is registered and points at the current `third_party/freecad-gears` gitlink.
2. Run `setup/bootstrap.sh --allow-downloads setup` when the managed base runtime is missing or stale.
3. Run `setup/bootstrap.sh run -- scripts/helper_tool.py setup freecad_gears`.
4. Run `setup/bootstrap.sh run -- scripts/helper_tool.py check freecad_gears`.
5. Submit only `inspection` requests matching `schemas/freecad_gears_inspection_request.schema.json`.
6. Keep request inputs under `.tmp/` or `designs/` and outputs under `.tmp/`, `output/`, or `revisions/`.
7. Treat JSON and STEP outputs as inspection evidence only.
8. Do not use FreeCAD Gears outputs as authoritative laser cut geometry, toolpaths, recipes, or fabrication approval.

## Failure Handling

- If `FreeCADCmd` is unavailable, rerun setup with approved downloads and inspect `.tools/logs/helpers/freecad_gears/`.
- If headless export fails, preserve the JSON manifest as diagnostic evidence and do not promote the provider beyond inspection status.
- If the submodule becomes dirty, reject outputs and restore the submodule before retrying.
