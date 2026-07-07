# Portable Host Bootstrap

The `setup/` entrypoints prepare a freshly cloned repository when the host has Git plus a native shell, but does not already have Python, Pixi, Conda, OpenSCAD, FreeCAD, or helper-tool dependencies.

The bootstrap installs only repository-local managed tools beneath `.tools/` by default. It does not install global packages, request administrator privileges, or modify third-party submodule source directories.

## Commands

Linux and macOS:

```sh
setup/bootstrap.sh doctor
setup/bootstrap.sh --allow-downloads setup
setup/bootstrap.sh verify
setup/bootstrap.sh run -- scripts/laser_build.py --help
```

Windows PowerShell:

```powershell
.\setup\bootstrap.ps1 doctor
.\setup\bootstrap.ps1 -AllowDownloads setup
.\setup\bootstrap.ps1 verify
.\setup\bootstrap.ps1 run -- scripts/laser_build.py --help
```

## Command Semantics

- `doctor` checks host platform, Git, Pixi, and tools-root status without downloading or creating files.
- `setup` installs the pinned Pixi manager when needed, creates the locked base Python environment, initializes submodules, and writes readiness evidence.
- `verify` checks the installed manager, locked runtime, submodule pins, and cleanliness.
- `repair` repeats setup with a download approval gate and may replace incomplete local bootstrap artifacts.
- `report` prints the most recent host-readiness report path.
- `run -- <repo-script.py> [args...]` executes approved repository Python scripts through managed Python instead of host Python.

`setup` and `repair` require `--allow-downloads` or `-AllowDownloads` when the pinned manager is missing or must be re-downloaded.

## Managed Paths

Persistent bootstrap state lives below `.tools/`:

- `.tools/bin/` for the pinned Pixi executable.
- `.tools/cache/` for Pixi cache data.
- `.tools/environments/` for detached managed environments.
- `.tools/reports/host-readiness/` for machine-readable and human-readable readiness reports.
- `.tools/state/` for readiness markers.
- `.tools/staging/` for incomplete downloads and atomic replacements.

Set `VIBE_CUTTING_TOOLS_ROOT` to use an alternate repository-local tools root, such as an isolated test directory under `.tmp/`. The bootstrap rejects tools roots outside this repository, including symlink escapes.

## Current Qualification

Phase 1 qualifies Linux x86-64 on the development host. The manifest also pins Linux ARM64, macOS Intel, macOS Apple silicon, and Windows x86-64 Pixi artifacts, but those platforms still require Phase 9 clean-host qualification before they are treated as fully validated.

PowerShell syntax is maintained in-repo; runtime qualification requires a Windows host.
