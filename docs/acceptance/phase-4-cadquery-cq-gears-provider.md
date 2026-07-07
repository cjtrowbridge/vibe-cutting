# Phase 4 Acceptance: CadQuery and CQ_Gears Provider

Date: 2026-07-06

Plan: `plans/current/2026-07-06-19-48-06_integrate-cadquery-and-cq-gears-provider.md`

Parent roadmap: `plans/future/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`

Decision: accepted with platform and fabrication limitations.

## Scope Accepted

- Added `tool_adapters/cq_gears.json` as a schema-version `2` `pixi_environment` provider.
- Added `schemas/cq_gears_request.schema.json` for planar profile requests.
- Added `setup/tools/cq-gears-requirements.lock` for CadQuery/OCP runtime dependencies.
- Added `setup/tools/cq_gears.py` for provider setup, local source installation, readiness markers, unsupported request rejection, smoke testing, and deterministic SVG profile export.
- Added tests for source pins, non-planar rejection, deterministic profile output, and gear metrics.
- Added `docs/tools/cq-gears.md` and `playbooks/how_to_use_cq_gears_for_laser_mechanisms.md`.
- Updated helper routing docs and agent guidance.

## Evidence

- CQ_Gears source revision: `e73874cf17a25447a99b1e7c22a4d5af38560e9c`.
- CadQuery source revision: `f69500e54640a3da8fcee9d063a5a1f996d63263`.
- Provider environment fingerprint: `f5f5ea3a484359bdf0523a4dbb066feae81dfaaf2d8a732f7e9e2d3e784bcc0b`.
- Dependency lock hash: `6e741de3dc579d24269191c58b40a58001da5c9bd13345b655677157cd28ed92`.
- Managed Python version: `3.12.13`.
- Installed package count: `45`.
- Smoke spur gear metrics: module `2.0`, teeth `18`, pitch diameter `36.0`, outside diameter `40.0`, root diameter `31.0`, bore `5.0`.
- Smoke point count: `1440`.
- Smoke SVG SHA-256: `b4d7e2739d8a1b335f7ab9f93d606c76c14ab1eaa3522bcb1e447f695365c5a4`.

## Commands Run

```sh
setup/bootstrap.sh run -- scripts/helper_tool.py setup cq_gears
setup/bootstrap.sh run -- scripts/helper_tool.py check cq_gears
setup/bootstrap.sh run -- setup/tools/cq_gears.py smoke --manifest tool_adapters/cq_gears.json
python3 -m unittest tests.test_cq_gears_provider -v
python3 -m unittest discover -s tests -v
git diff --check
python3 agents/scripts/regenerate_plan_indexes.py --repo-root . --check
git submodule status --recursive
```

## Validation Result

- Complete host test suite passed: 54 tests passed, 1 skipped.
- The skipped test is PowerShell syntax validation because `pwsh` is not installed on this Linux host.
- Managed CQ_Gears provider setup succeeded with repo-local `.tools/` writes only.
- `setup/bootstrap.sh run -- scripts/helper_tool.py check cq_gears` reported `ready: true`.
- Provider smoke generated deterministic SVG profile geometry and metrics.
- Spur, ring, rack, and meshing-pair profile fixtures generated deterministic source geometry and expected metrics.
- Recursive submodules remained clean and pinned.
- No global packages, system package managers, administrative privileges, FreeCAD, BOSL2, or hardware access were used.

## Known Limitations

- Linux x86-64 is the only runtime-qualified platform in this checkpoint.
- STEP export is not yet accepted as a generated artifact; SVG profile and JSON metrics are the accepted smoke outputs.
- CQ_Gears outputs are source geometry and provenance only until host mechanism validation imports them.
- Helical, herringbone, bevel, worm, crossed-helical, hyperbolic, and other non-planar requests are rejected.
