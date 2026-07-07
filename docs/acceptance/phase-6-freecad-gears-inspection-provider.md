# Phase 6 Acceptance: FreeCAD Gears Inspection Provider

## Result

Accepted.

## Scope

- Registered `freecad_gears` as a schema-version `2` provider helper.
- Used pinned `third_party/freecad-gears` at `d55e8e3d21208e052379a8451507fb4a727ae292`.
- Provisioned FreeCAD Gears through the upstream Pixi manifest and lock.
- Isolated provider cache, temp, log, staging, and user-style directories under `.tools/`.
- Detected managed `freecadcmd` as `FreeCAD 1.0.0 Revision: 39109 (Git)`.
- Generated a headless involute spur gear inspection manifest and STEP artifact.
- Preserved the boundary that FreeCAD Gears output is inspection/provenance only, not authoritative fabrication geometry or G-code.

## Evidence

```bash
python3 -m py_compile setup/tools/freecad_gears.py
python3 -m unittest tests.test_freecad_gears_provider -v
setup/bootstrap.sh run -- scripts/helper_tool.py setup freecad_gears
setup/bootstrap.sh run -- scripts/helper_tool.py check freecad_gears
setup/bootstrap.sh run -- setup/tools/freecad_gears.py smoke --manifest tool_adapters/freecad_gears.json
```

## Environment

- Platform: `linux-x86_64`
- Environment fingerprint: `a8c70742c3d58499cb37bbccb39d6cdf6c3d75de625b3ace190ba36b797b5924`
- Lock hash: `third_party/freecad-gears/pixi.lock` = `3a4f030e97689da8e6687b8e9385eb7dbec80c3bd05d142466b82c805936bad6`
- FreeCAD executable: `freecadcmd`
- FreeCAD version: `FreeCAD 1.0.0 Revision: 39109 (Git)`

## Smoke Artifact

- Request hash: `ced18df55e489e5331f1c80c5a6a148ac00222265a3af6d4ed0858a7e7386992`
- STEP hash: `69b005fa46e634045757fa674739df11bc82ee0e27241404e3aa3f561e165b93`
- Bounding box: `39.976768973290646 x 39.606125540458976 x 3.0 mm`
- Invocation method: `freecadcmd`
- Fabrication approved: `false`

## Limitations

- FreeCAD Gears remains an inspection backend only.
- Outputs are not valid laser toolpaths or process recipes.
- Host-owned mechanism validation and laser artifact generation remain authoritative.
