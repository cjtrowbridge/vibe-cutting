# Phase 5 Acceptance: BOSL2 OpenSCAD Provider

Date: 2026-07-06

Plan: `plans/current/2026-07-06-20-02-16_integrate-bosl2-openscad-provider.md`

Parent roadmap: `plans/past/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`

Decision: accepted with platform and comparison-only limitations.

## Scope Accepted

- Added `tool_adapters/bosl2.json` as a schema-version `2` `openscad_library` provider.
- Added `schemas/bosl2_gear_request.schema.json`.
- Added `setup/tools/bosl2.py` for OpenSCAD detection, provider marker creation, per-process `OPENSCADPATH`, wrapper source generation, SVG export, smoke testing, and validation.
- Added deterministic smoke coverage for spur, ring, and rack comparison profiles.
- Added `docs/tools/bosl2.md` and `playbooks/how_to_use_bosl2_gear_geometry.md`.
- Updated helper routing documentation and agent guidance.

## Evidence

- BOSL2 source revision: `fbcdfdd511b6abfde93c43c8f85c2bd24ee7a02d`.
- Provider environment fingerprint: `1797728c349f6181ce55ac46b9cbc36470c072fc9ff6c806b0adcdef5bdb7b4b`.
- OpenSCAD executable: `openscad`.
- OpenSCAD version: `OpenSCAD version 2021.01`.
- Smoke profile hashes:
  - spur: `d276b854710f6def63e1ceeac5852efaf0e5b2b442604dfeed0caa3cf06b353d`
  - ring: `948eb2ef7cb6601a9ce4c10fcfcf579aab8d8a01cdfead8cee88826ad8bad1f9`
  - rack: `fc22a4a2f23106fad5ea76b66b8e0bb514889de87c72744cc7b5e6f9470d1d02`

## Commands Run

```sh
setup/bootstrap.sh run -- scripts/helper_tool.py setup bosl2
setup/bootstrap.sh run -- scripts/helper_tool.py check bosl2
setup/bootstrap.sh run -- setup/tools/bosl2.py smoke --manifest tool_adapters/bosl2.json
python3 -m unittest tests.test_bosl2_provider -v
python3 -m unittest discover -s tests -v
git diff --check
python3 agents/scripts/regenerate_plan_indexes.py --repo-root . --check
git submodule status --recursive
```

## Validation Result

- Complete host test suite passed: 57 tests passed, 1 skipped.
- The skipped test is PowerShell syntax validation because `pwsh` is not installed on this Linux host.
- Managed BOSL2 provider setup succeeded with repo-local `.tools/` writes only.
- `setup/bootstrap.sh run -- scripts/helper_tool.py check bosl2` reported `ready: true`.
- Provider smoke generated deterministic SVG comparison profiles for spur, ring, and rack requests.
- Recursive submodules remained clean and pinned.
- No network access, global packages, system package managers, administrative privileges, FreeCAD, or hardware access were used.

## Known Limitations

- Linux x86-64 with host OpenSCAD 2021.01 is the only runtime-qualified platform in this checkpoint.
- BOSL2 is comparison/fallback source geometry only, not the mechanism validator.
- BOSL2 output remains not fabrication-approved until imported and validated by the host mechanism pipeline.
