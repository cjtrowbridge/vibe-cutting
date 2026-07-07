# CI Verification

The cross-platform bootstrap workflow verifies that a Git-equipped host can prepare the repository-local tool runtime through the native bootstrap entrypoints.

## Workflow

- Workflow: `.github/workflows/cross-platform-bootstrap.yml`
- Platforms: Linux x86-64, Windows x86-64 through PowerShell, and macOS on the current hosted runner architecture.
- Trigger: pushes to `main`, pull requests, and manual `workflow_dispatch`.
- Submodules: checked out recursively before bootstrap commands run.

## Default Checks

Each platform job runs:

```text
doctor
setup with explicit download approval
verify
managed scripts/laser_build.py --help
managed scripts/helper_tool.py validate
managed scripts/host_readiness_report.py
report
```

The workflow proves setup and managed command execution. It does not prove that a given machine/material combination is ready for fabrication.

## Cache Policy

CI caches only repository-local bootstrap paths:

- `.tools/cache`
- `.tools/pixi-home`
- `.tools/environments`

Cache keys include the runner platform plus `setup/pixi.lock`, Pixi checksum records, setup tool lock files, and the upstream FreeCAD Gears Pixi lock. Cached content is still revalidated by the bootstrap checksum and locked-environment checks before use.

## Heavyweight Helpers

FreeCAD and similarly large helpers are optional in CI. Run the workflow manually with `run_heavyweight_helpers=true` to attempt heavyweight smoke tests. These steps are allowed to fail without failing the bootstrap job because hosted runner limits do not define fabrication readiness.

## Evidence Artifacts

Every job uploads `.tools/reports/host-readiness` as `host-readiness-<os>-<arch>`. Treat those artifacts as platform setup evidence only. A platform remains pending until a successful workflow run exists for that platform, and helper readiness remains below `fabrication-approved` unless a design-specific fabrication validation plan says otherwise.
