# ADR 0001: Portable Helper Bootstrap and Provider Model

- Status: Accepted for phased implementation
- Date: 2026-07-06

## Context

Vibe-cutting uses heterogeneous helper repositories: Python applications, Python geometry libraries, OpenSCAD libraries, desktop/headless engineering applications, and manual operator tools. A Python-first wrapper cannot prepare a fresh host when Python is absent, and one installation model cannot safely describe every helper.

The repository must remain cloneable onto Debian-family Linux, Windows, and macOS hosts without assuming Python, Pixi, Conda, OpenSCAD, FreeCAD, or helper dependencies. Git is necessarily present because the repository and its submodules are Git resources.

## Decision

1. Provide native `setup/bootstrap.sh` and `setup/bootstrap.ps1` launchers that do not require Python.
2. Require and verify host Git 2.31 or newer; do not install or shadow Git.
3. Download only pinned, checksum-verified bootstrap artifacts after approval.
4. Install the manager, Python, helper environments, caches, logs, and reports beneath ignored `.tools/`.
5. Expose managed commands through `doctor`, `setup`, `verify`, `repair`, `report`, and `run`.
6. Dispatch repository Python scripts through managed Python rather than host Python.
7. Model helpers with provider categories:
   - `pixi_environment` for locked executable or Python environments.
   - `openscad_library` for pinned libraries invoked through a managed OpenSCAD executable.
   - `system_application` for applications that require discovery or managed headless installation.
   - `manual_operator` for tools outside automated artifact authority.
8. Keep third-party repositories as unmodified submodules and invoke callable helpers as separate processes.
9. Treat all helper output as untrusted until the host normalizes operations and validates geometry, bounds, provenance, ordering, and fabrication scope.
10. Deliver the roadmap through gated child plans and acceptance reports.

## Consequences

- Setup gains native launcher duplication, platform manifests, locks, and cross-platform tests.
- The current Python-first helper runner remains transitional until the managed base runtime exists.
- Tool readiness becomes capability-, platform-, and evidence-specific.
- Large environments can be installed lazily and independently.
- Clean-host reproducibility and rollback are testable without changing global host state.
- A helper can accelerate geometry generation without acquiring recipe, G-code, or hardware authority.

## Rejected Alternatives

- **Assume Python:** fails on fresh hosts and makes Python installation an undocumented prerequisite.
- **Provision Git:** creates a bootstrap paradox and unnecessary ambiguity about repository ownership.
- **Use `curl | sh`:** executes unverified remote content and defeats pinning.
- **Install globally:** requires privilege, contaminates hosts, and makes rollback unreliable.
- **Use one Python virtual environment:** cannot represent OpenSCAD, FreeCAD, native applications, or incompatible dependency stacks.
- **Import helper packages into the host:** couples licenses and runtimes and expands the trusted computing boundary.
- **Accept helper G-code directly:** bypasses machine/material profiles and host safety validation.

## Security and Portability Boundaries

- Network, package-manager, elevation, and heavyweight-install actions have explicit approval gates.
- Checksums are verified before extraction or execution.
- Setup writes remain repository-local by default.
- Unsupported targets fail explicitly.
- Platform success is not inferred across untested targets.
- Readiness never implies fabrication approval outside its recorded scope.

## Revisit Triggers

Revisit this decision if Git ceases to be a cloning prerequisite, the selected manager cannot support a target platform, native launchers cannot verify artifacts with ordinary host tools, a helper requires in-process integration, or a validated packaging approach provides equal isolation with less complexity.
