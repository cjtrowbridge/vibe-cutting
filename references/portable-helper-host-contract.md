# Reference: Portable Helper Host Contract

## Purpose

Define the host capabilities that may be assumed before vibe-cutting installs its repository-local helper runtime. This is a target contract for the portable bootstrap; the native launchers are implemented in Phase 1.

## Support Matrix

| Support target | Native entrypoint | Required command environment | Qualification requirement |
| --- | --- | --- | --- |
| Debian 12+ compatible Linux, x86-64 | `setup/bootstrap.sh` | POSIX `/bin/sh` | Clean-host bootstrap and CI |
| Debian 12+ compatible Linux, ARM64 | `setup/bootstrap.sh` | POSIX `/bin/sh` | Clean-host bootstrap and CI |
| Windows 10 22H2 or Windows 11, x86-64 | `setup/bootstrap.ps1` | Windows PowerShell 5.1+ | Clean-host bootstrap and CI |
| macOS 13+, Intel | `setup/bootstrap.sh` | POSIX `/bin/sh` | Clean-host bootstrap and CI |
| macOS 13+, Apple silicon | `setup/bootstrap.sh` | POSIX `/bin/sh` | Clean-host bootstrap and CI |

A listed target is a planned support target, not a readiness claim. It becomes supported only after its acceptance evidence appears in `docs/toolchain-support-matrix.md`. Other operating systems and architectures must fail as unsupported rather than guessing an artifact or environment.

## Required Prerequisites

The bootstrap may assume only:

- A working Git executable, version 2.31 or newer.
- A clone of this repository with its `.git` metadata available.
- The native command environment listed in the support matrix.
- Ordinary filesystem and process execution available to the current user.
- Approved network access when a required pinned artifact is not already cached.

Git must support:

- `git rev-parse`, `git status`, and `git diff`.
- `git config --get`.
- `git submodule status`, `git submodule sync`, and recursive submodule update.
- Work-tree and gitlink inspection without modifying submodule source.

Bootstrap verifies the Git executable path and version. It does not download, install, shadow, or replace Git.

## Native Capabilities

The launcher must discover capabilities rather than assume a specific optional command.

### Linux and macOS

- `/bin/sh`.
- One HTTPS downloader: `curl` or `wget`.
- One SHA-256 verifier: `sha256sum`, `shasum -a 256`, or `openssl dgst -sha256`.
- Native archive support adequate for the selected environment-manager artifact, normally `tar`; `unzip` may be used when present.
- `mktemp`, basic file operations, and process execution.

### Windows

- Windows PowerShell 5.1 or newer.
- `Invoke-WebRequest` for HTTPS downloads.
- `Get-FileHash -Algorithm SHA256`.
- `Expand-Archive` for ZIP artifacts.
- Standard PowerShell filesystem, process, and temporary-path APIs.

If a required capability is missing, `doctor` reports the missing capability and platform-specific remediation without downloading anything or invoking an operating-system package manager.

## Repository-Local Paths

All persistent managed state belongs beneath `.tools/`:

```text
.tools/
  bin/                    # pinned manager and launch shims
  cache/downloads/        # checksum-addressed downloaded archives
  cache/packages/         # environment-manager package cache
  environments/base/      # managed Python and stage-two runtime
  environments/<tool>/    # fingerprinted helper environments
  logs/                   # setup and provider logs
  reports/host-readiness/ # generated machine and human reports
  staging/                # atomic installation staging
  tmp/                    # setup-controlled temporary files
```

Generated compatibility copies under `reports/host-readiness/` are also ignored. Runtime design staging remains under `.tmp/`; authoritative build artifacts remain under `output/` and `revisions/`.

Bootstrap must not write:

- Inside `third_party/` or `agents/`.
- Into a user-global Python, Conda, Pixi, OpenSCAD, or FreeCAD location.
- Into system package directories.
- Outside the repository, except a separately approved remediation that identifies every external path before execution.

## Approval Gates

Separate approval is required before:

- First network download or a download caused by a changed pin.
- Invoking an operating-system package manager.
- Requesting administrator, root, or elevation privileges.
- Creating a heavyweight environment such as FreeCAD when the estimated download and installed sizes exceed the documented threshold.
- Deleting a complete existing environment rather than atomically replacing a staged environment.

Approval is not implied by running `doctor`, `verify`, or `report`. Approved setup may reuse checksum-verified cached artifacts without another network approval.

## Failure Contract

Unsupported platform, missing or obsolete Git, missing native capability, checksum mismatch, dirty submodule, path escape, or unavailable approved network access must:

1. Stop before executing unverified content.
2. Preserve previous complete environments and authoritative outputs.
3. Remove or quarantine only the incomplete staging path.
4. Report the failed check, detected value, required value, and exact remediation.
5. Emit a non-zero exit status and a machine-readable blocked state.
