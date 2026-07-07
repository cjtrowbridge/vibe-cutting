# Phase 2 Acceptance: Generalized Helper Adapter Platform

Date: 2026-07-06

Plan: `plans/current/2026-07-06-19-08-31_build-generalized-helper-adapter-platform.md`

Parent roadmap: `plans/future/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`

Decision: accepted with migration limitations.

## Scope Accepted

- Added schema-version `2` provider adapter contracts in `schemas/helper_adapter.schema.json`.
- Added typed helper request and helper result/provenance schemas.
- Added provider scaffolding under `setup/providers/` for `pixi_environment`, `openscad_library`, `system_application`, and `manual_operator`.
- Added shared setup-tool helpers under `setup/tools/`.
- Extended `scripts/helper_tool.py` to validate legacy schema-version `1` adapters and provider schema-version `2` adapters.
- Added provider readiness reports, request path checks, exact output-inventory validation, provider fingerprints, lock-hash capture, staging cleanup, scaffold marker generation, and output-preservation utilities.
- Kept the existing Boxes.py adapter on the legacy path for Phase 3 migration.
- Updated helper governance, docs, references, and playbooks for provider-first future helper routing.

## Evidence

- Development platform: Linux x86-64.
- Bootstrap path used for managed validation: `setup/bootstrap.sh run -- scripts/helper_tool.py validate`.
- Current registered adapters: one legacy adapter, `boxes`, schema-version `1`.
- Provider schema-version `2` was validated through isolated test fixtures rather than a real migrated helper manifest.
- Recursive submodules remained pinned and clean.

## Commands Run

```sh
python3 -m unittest discover -s tests -v
git diff --check
python3 agents/scripts/regenerate_plan_indexes.py --repo-root . --check
VIBE_CUTTING_TOOLS_ROOT="$TOOLS_ROOT" setup/bootstrap.sh run -- scripts/helper_tool.py validate
VIBE_CUTTING_TOOLS_ROOT="$TOOLS_ROOT" setup/bootstrap.sh run -- scripts/helper_tool.py report
git submodule status --recursive
```

## Validation Result

- Complete host test suite passed: 50 tests passed, 1 skipped.
- The skipped test is PowerShell syntax validation because `pwsh` is not installed on this Linux host.
- Managed helper validation succeeded through the Phase 1 bootstrap runtime.
- Managed helper report succeeded and showed `boxes` remains a legacy adapter.
- The managed report also showed the old legacy Boxes `.tmp` environment is not ready under managed Python because it was installed under a different Python ABI; this is expected and is the reason Phase 3 migrates Boxes.py into the provider model.
- No network access, global packages, system package managers, administrative privileges, OpenSCAD, FreeCAD, CadQuery, BOSL2, or Boxes.py dependency installs were used in this phase.

## Known Limitations

- No real helper has been migrated to schema-version `2` yet.
- Provider setup creates scaffold markers and validation evidence only; real tool environments are implemented by later tool-specific phases.
- `boxes` remains on the legacy direct-Python helper path until Phase 3.
- Linux x86-64 is the only runtime-qualified platform in this checkpoint.
