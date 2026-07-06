# Reference: Managed Bootstrap Command Contract

## Purpose

Define the portable command surface that native launchers must provide after Phase 1. The launchers themselves require no Python; stage-two commands execute with repository-managed runtimes.

## Equivalent Entrypoints

Linux and macOS:

```sh
./setup/bootstrap.sh <command> [arguments]
```

Windows:

```powershell
.\setup\bootstrap.ps1 <command> [arguments]
```

Both entrypoints must implement equivalent behavior and exit-status meaning.

## Commands

- `doctor`: inspect prerequisites and platform support without downloads or mutation.
- `setup`: obtain approved pinned artifacts and converge requested environments.
- `verify`: validate existing installations, locks, pins, cleanliness, and smoke tests without repair.
- `repair`: replace only invalid or incomplete repository-local state after applicable approvals.
- `report`: emit machine-readable JSON and human-readable Markdown readiness reports.
- `run -- <repo-command> [arguments]`: execute an allowed repository command with its declared managed runtime.

## Run Resolution

`run` must:

1. Require `--` before the delegated command.
2. Resolve the delegated path relative to the repository root, independent of the caller's current directory.
3. Reject path traversal, absolute paths outside the repository, submodule entrypoints, and unregistered environment executables.
4. Execute a `.py` repository script with the pinned Python from `.tools/environments/base/`, never `python`, `python3`, `py`, or a virtual environment found on host `PATH`.
5. Resolve registered helper executables only through their fingerprinted managed environments.
6. Permit native commands only when an internal bootstrap allowlist declares them for a specific operation.
7. Preserve delegated arguments exactly without shell re-parsing.

## Process Semantics

The launcher must preserve:

- Repository root as the default working directory, unless the command contract declares another repository-local directory.
- Standard input, output, and error streams.
- Delegated process exit status.
- Environment isolation, adding only declared managed paths and variables.
- Interrupt behavior: POSIX termination and interrupt signals are forwarded where supported; PowerShell cancellation terminates the managed child and returns a non-zero status.

Secrets, ambient Python paths, user package paths, global OpenSCAD paths, and FreeCAD user configuration must not leak into managed invocations.

## Examples

Linux and macOS:

```sh
./setup/bootstrap.sh run -- scripts/laser_build.py --design good-for-one-free-hug
./setup/bootstrap.sh run -- scripts/helper_tool.py check boxes
```

Windows:

```powershell
.\setup\bootstrap.ps1 run -- scripts\laser_build.py --design good-for-one-free-hug
.\setup\bootstrap.ps1 run -- scripts\helper_tool.py check boxes
```

These examples mean “select the registered managed runtime and execute this repository script.” They do not mean “find Python on the host.”

## Diagnostics

Every command must provide:

- A concise human-readable error on standard error.
- A stable non-zero exit status category.
- The failed check, detected value, required value, and remediation.
- Structured report data when `report` is requested.

Reports exclude credentials, tokens, usernames, home-directory inventories, unrelated environment variables, and unrelated host applications.
