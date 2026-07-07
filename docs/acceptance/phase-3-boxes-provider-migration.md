# Phase 3 Acceptance: Boxes.py Provider Migration

Date: 2026-07-06

Plan: `plans/current/2026-07-06-19-19-57_migrate-boxes-to-provider-helper.md`

Parent roadmap: `plans/future/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`

Decision: accepted with platform limitations.

## Scope Accepted

- Migrated `tool_adapters/boxes.json` to schema-version `2` using the `pixi_environment` provider.
- Added `schemas/boxes_generation_request.schema.json`.
- Added locked Boxes dependency constraints in `setup/tools/boxes-requirements.lock`.
- Added `setup/tools/boxes.py` for managed setup, readiness validation, YAML multi-generator invocation, smoke testing, SVG validation, output inventory checks, and source-mutation rejection.
- Added `pip` to the managed base runtime so provider drivers can install pinned local helper dependencies into repository-local `.tools/` environments.
- Updated helper tests and Boxes integration tests to exercise the provider path through `setup/bootstrap.sh run`.
- Updated docs, playbooks, README, and agent guidance to remove the Boxes legacy-helper exception.

## Evidence

- Boxes source revision: `836f5f72bedb33ac4262ed925545eacb31e926a8`.
- Boxes provider environment fingerprint: `25abd20e931243560e6d3e172d277267fd0dfa9ef9050841da94f679dfe95070`.
- Boxes dependency lock hash: `b2b32e8a2b2dfe3c4aea60c9a454a4d811d01a38593c446e550fefe42271c0b6`.
- Managed Python version: `3.12.13`.
- Installed package count: `36`.
- Smoke artifact: `.tmp/boxes/provider-smoke/generated/smoke_0.svg`.
- Smoke artifact SHA-256: `1c85beede190a1072b2a6f6a5d3e9ab477f54e273dd5c721b8ce6085d6e73845`.

## Commands Run

```sh
VIBE_CUTTING_TOOLS_ROOT="$TOOLS_ROOT" setup/bootstrap.sh --allow-downloads setup
VIBE_CUTTING_TOOLS_ROOT="$TOOLS_ROOT" setup/bootstrap.sh run -- scripts/helper_tool.py setup boxes
VIBE_CUTTING_TOOLS_ROOT="$TOOLS_ROOT" setup/bootstrap.sh run -- scripts/helper_tool.py check boxes
VIBE_CUTTING_TOOLS_ROOT="$TOOLS_ROOT" setup/bootstrap.sh run -- setup/tools/boxes.py smoke --manifest tool_adapters/boxes.json
python3 -m unittest discover -s tests -v
git diff --check
python3 agents/scripts/regenerate_plan_indexes.py --repo-root . --check
git submodule status --recursive
```

## Validation Result

- Complete host test suite passed: 50 tests passed, 1 skipped.
- The skipped test is PowerShell syntax validation because `pwsh` is not installed on this Linux host.
- Managed Boxes provider setup succeeded with repo-local `.tools/` writes only.
- `setup/bootstrap.sh run -- scripts/helper_tool.py check boxes` reported `ready: true`.
- Managed provider smoke generated parseable deterministic SVG.
- Recursive submodules remained clean and pinned.
- No global packages, system package managers, administrative privileges, OpenSCAD, FreeCAD, CadQuery, BOSL2, or hardware access were used.

## Known Limitations

- Linux x86-64 is the only runtime-qualified platform in this checkpoint.
- Boxes.py output is still source geometry only; host pipeline ingestion of arbitrary Boxes SVG remains a later integration task.
- Boxes.py remains not fabrication-approved; thickness and burn values must come from calibrated host material/job bindings before production use.
