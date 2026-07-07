# Phase 1 Acceptance: Native Bootstrap and Managed Base Runtime

Date: 2026-07-06

Plan: `plans/current/2026-07-06-10-44-27_build-native-bootstrap-and-managed-base-runtime.md`

Parent roadmap: `plans/future/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`

Decision: accepted with documented platform limitations.

## Scope Accepted

- Native bootstrap launchers under `setup/bootstrap.sh` and `setup/bootstrap.ps1`.
- Pinned Pixi manager artifacts recorded in `setup/toolchain-manifest.json` and `setup/checksums/pixi-v0.72.0.sha256`.
- Locked managed Python base environment in `setup/pixi.toml` and `setup/pixi.lock`.
- Managed stage-two orchestration in `setup/bootstrap_host.py`.
- No-download `doctor`, approval-gated `setup` and `repair`, `verify`, `report`, and managed `run`.
- Recursive submodule initialization and fail-closed verification through host Git.
- Repository-local manager, cache, environment, report, state, and staging paths.
- Clean-host simulation using an alternate empty tools root and masked host Python path.

## Evidence

- Selected Pixi version: `0.72.0`.
- Managed Python version: `3.12.13`.
- Host Git path: `/usr/bin/git`.
- Host Git version: `2.47.3`.
- Lock SHA-256 observed in readiness report: `eb7f2870e17ec554c8e27405b847b0167c9ad2814791576c79dca6e89c0f690f`.
- Development-host tools root used for acceptance: `.tmp/bootstrap-phase1.DPcotl`.
- Readiness report path: `.tmp/bootstrap-phase1.DPcotl/reports/host-readiness/host-readiness.json`.

## Commands Run

```sh
TOOLS_ROOT=$(mktemp -d "$PWD/.tmp/bootstrap-phase1.XXXXXX")
printf '%s\n' "$TOOLS_ROOT" > .tmp/bootstrap-phase1-last-root
VIBE_CUTTING_TOOLS_ROOT="$TOOLS_ROOT" setup/bootstrap.sh --allow-downloads setup
VIBE_CUTTING_TOOLS_ROOT="$TOOLS_ROOT" setup/bootstrap.sh verify
env -u PYTHONHOME -u PYTHONPATH PATH=/usr/bin:/bin VIBE_CUTTING_TOOLS_ROOT="$TOOLS_ROOT" setup/bootstrap.sh run -- scripts/laser_build.py --help
VIBE_CUTTING_TOOLS_ROOT="$TOOLS_ROOT" setup/bootstrap.sh setup
```

```sh
python3 -m unittest discover -s tests -v
git diff --check
python3 agents/scripts/regenerate_plan_indexes.py --repo-root . --check
```

## Validation Result

- Complete host test suite passed: 39 tests passed, 1 skipped.
- The skipped test is PowerShell syntax validation because `pwsh` is not installed on this Linux host.
- Managed `run` executed `scripts/laser_build.py --help` while host Python environment variables were removed and `PATH` was restricted to `/usr/bin:/bin`.
- Repeated `setup` completed without `--allow-downloads` after the base runtime was already ready.
- Submodules remained pinned and clean during acceptance.
- No global packages, system package managers, or administrative privileges were used.

## Known Limitations

- Linux x86-64 is the only runtime-qualified platform in this checkpoint.
- Linux ARM64, macOS Intel, macOS Apple silicon, and Windows x86-64 artifacts are pinned but not clean-host qualified here.
- `scripts/helper_tool.py` remains a transitional direct-Python helper interface until the generalized provider phases migrate it behind managed setup providers.
- OpenSCAD, Boxes.py, CadQuery/CQ_Gears, BOSL2, and FreeCAD Gears helper environments are not provisioned by Phase 1.
