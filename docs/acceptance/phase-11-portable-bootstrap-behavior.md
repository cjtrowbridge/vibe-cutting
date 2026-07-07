# Phase 11 Acceptance: Portable Bootstrap Behavior

## Result

Accepted.

## Scope

- Ran bootstrap from an alternate empty tools root under `.tmp/bootstrap-ws14.*`.
- Verified `doctor`, `setup`, `verify`, `report`, and managed `run`.
- Verified managed `scripts/laser_build.py --design primitive_power_extender_laser_0_1 --validate-only`.
- Verified idempotent repeated setup on the same alternate tools root.
- Generated a full host-readiness report from the alternate managed runtime.
- Reused unit tests for checksum mismatch, interrupted setup preservation, path confinement, unsupported managed commands, host Python masking, PowerShell syntax, and bootstrap failure modes.
- Confirmed all submodules remained clean.

## Evidence

```bash
VIBE_CUTTING_TOOLS_ROOT=.tmp/bootstrap-ws14.* setup/bootstrap.sh doctor
VIBE_CUTTING_TOOLS_ROOT=.tmp/bootstrap-ws14.* setup/bootstrap.sh --allow-downloads setup
VIBE_CUTTING_TOOLS_ROOT=.tmp/bootstrap-ws14.* setup/bootstrap.sh verify
VIBE_CUTTING_TOOLS_ROOT=.tmp/bootstrap-ws14.* setup/bootstrap.sh run -- scripts/laser_build.py --design primitive_power_extender_laser_0_1 --validate-only
VIBE_CUTTING_TOOLS_ROOT=.tmp/bootstrap-ws14.* setup/bootstrap.sh run -- scripts/host_readiness_report.py --output-root .tmp/bootstrap-ws14-readiness
VIBE_CUTTING_TOOLS_ROOT=.tmp/bootstrap-ws14.* setup/bootstrap.sh --allow-downloads setup
VIBE_CUTTING_TOOLS_ROOT=.tmp/bootstrap-ws14.* setup/bootstrap.sh run -- scripts/laser_build.py --help
python3 -m unittest discover -s tests -v
```

## Local Result

- Alternate tools root: `.tmp/bootstrap-ws14.Fn3Bzr`
- Bootstrap state: `verified`
- Verified submodules: `8`
- Full readiness blocked capabilities: `0`

## Boundary

- This phase verifies behavior on the development Linux x86-64 host.
- Windows, macOS, and Linux ARM64 remain pending Workstream 15 CI/clean-host evidence.
