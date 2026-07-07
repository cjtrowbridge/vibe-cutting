---
plan_id: 2026-07-06-10-29-35_define-portable-helper-bootstrap-contracts
title: Define Portable Helper Bootstrap Contracts
summary: Complete Phase 0 by fixing host prerequisites, bootstrap boundaries, readiness states, managed command invocation, and gated child-plan acceptance rules.
status: past
created_at: 2026-07-06-10-29-35
---

# Define Portable Helper Bootstrap Contracts

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Phase Boundary

This child plan implements only Phase 0 of `plans/past/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`. It defines contracts and templates; it does not create bootstrap executables, download an environment manager, install dependencies, modify third-party submodules, or provision `.tools/`.

- [x] 1. Define the supported host contract.
  - [x] 1.1 Create `references/portable-helper-host-contract.md`.
  - [x] 1.2 Define supported Debian-family Linux, Windows, and macOS architecture targets.
  - [x] 1.3 Define Git and native shell or PowerShell as required host prerequisites.
  - [x] 1.4 Define the minimum supported Git version and required Git capabilities.
  - [x] 1.5 Define ordinary native download, archive, checksum, filesystem, and process capabilities by platform.
  - [x] 1.6 Define unsupported platform, missing prerequisite, and obsolete prerequisite failure behavior.
  - [x] 1.7 Define repository-local `.tools/` installation roots, caches, environments, logs, reports, staging areas, and temporary paths.
  - [x] 1.8 Define the prohibition on default global installation, host Python use, administrative privileges, and writes inside submodules.
  - [x] 1.9 Define explicit approval gates for network downloads, system package managers, privileged remediation, and heavyweight environments.

- [x] 2. Define bootstrap and helper readiness contracts.
  - [x] 2.1 Create `references/helper-readiness-states.md`.
  - [x] 2.2 Define bootstrap states `uninitialized`, `manager-ready`, `base-ready`, `tools-partial`, `tools-ready`, and `verified`.
  - [x] 2.3 Define the allowed transition into and out of every bootstrap state.
  - [x] 2.4 Define helper states `registered`, `dependencies-ready`, `invocation-ready`, `output-validated`, `pipeline-integrated`, and `fabrication-approved`.
  - [x] 2.5 Define evidence required to enter every helper readiness state.
  - [x] 2.6 Define invalidation triggers for source-pin, lock, runtime, adapter, request-schema, machine-profile, material-profile, and validation changes.
  - [x] 2.7 Define fail-closed behavior for partial, stale, interrupted, or contradictory readiness evidence.
  - [x] 2.8 Define which readiness states permit geometry comparison, pipeline input, calibration G-code, and fabrication output.

- [x] 3. Define the managed command interface.
  - [x] 3.1 Create `references/managed-bootstrap-command-contract.md`.
  - [x] 3.2 Define equivalent `setup/bootstrap.sh` and `setup/bootstrap.ps1` command surfaces.
  - [x] 3.3 Define `doctor`, `setup`, `verify`, `repair`, `report`, and `run` command responsibilities.
  - [x] 3.4 Define `run -- <repo-command>` resolution for Python scripts, managed executables, and explicitly allowed native commands.
  - [x] 3.5 Require Python scripts to execute with the pinned managed Python runtime even when host Python is installed.
  - [x] 3.6 Define argument, working-directory, environment, standard-stream, exit-code, signal, and interrupt preservation.
  - [x] 3.7 Define rejection of commands outside the repository or outside registered managed environments.
  - [x] 3.8 Define diagnostic and structured-report behavior without secrets or unrelated host data.
  - [x] 3.9 Include normative Linux/macOS and Windows examples for invoking `scripts/laser_build.py`.

- [x] 4. Record the architecture decision.
  - [x] 4.1 Create `docs/decisions/0001-portable-helper-bootstrap-and-provider-model.md`.
  - [x] 4.2 Record the context and reasons for native zero-Python launchers.
  - [x] 4.3 Record Git as a verified host prerequisite rather than a managed dependency.
  - [x] 4.4 Record repository-local environment management and checksum-verified downloads.
  - [x] 4.5 Record the `pixi_environment`, `openscad_library`, `system_application`, and `manual_operator` provider categories.
  - [x] 4.6 Record why third-party helpers remain subprocess tools and untrusted geometry sources.
  - [x] 4.7 Record consequences, rejected alternatives, security boundaries, portability limits, and future decision triggers.

- [x] 5. Define phased execution and acceptance artifacts.
  - [x] 5.1 Create `templates/helper-stack-phase-plan.md`.
  - [x] 5.2 Require each child plan to declare its parent roadmap, phase, entry evidence, exact files, supported platforms, exclusions, approval boundaries, rollback, and stop condition.
  - [x] 5.3 Create `templates/helper-stack-phase-acceptance-report.md`.
  - [x] 5.4 Require each acceptance report to record commands, platforms, versions, checksums, lock hashes, submodule pins and cleanliness, positive tests, negative tests, idempotence, isolation, rollback, limitations, and readiness decisions.
  - [x] 5.5 Define the rule that downstream phases cannot begin until the preceding child plan is archived and its acceptance report is approved.
  - [x] 5.6 Define the rule that partial platform success cannot be generalized to untested platforms.
  - [x] 5.7 Define the rule that helper readiness never implies fabrication approval without host-pipeline validation.

- [x] 6. Synchronize agent governance and roadmap traceability.
  - [x] 6.1 Update `AGENTS.md` with bootstrap-contract, managed-command, readiness-state, and phased-child-plan routing.
  - [x] 6.2 Update `references/helper-tool-contract.md` to reference the new host, readiness, and managed-command contracts.
  - [x] 6.3 Update the reference and template indexes in the applicable governance files.
  - [x] 6.4 Mark umbrella roadmap items 1.1 through 1.12 complete only where the new artifacts provide explicit evidence.
  - [x] 6.5 Leave umbrella workstreams 2 through 16 pending.
  - [x] 6.6 Regenerate all plan indexes.

- [x] 7. Verify Phase 0 acceptance.
  - [x] 7.1 Verify every Phase 0 umbrella requirement maps to a concrete section in the created contracts.
  - [x] 7.2 Verify all referenced paths, commands, states, providers, and templates exist and use consistent names.
  - [x] 7.3 Verify Linux/macOS and Windows command examples preserve the same semantics.
  - [x] 7.4 Verify no contract assumes host Python, Pixi, Conda, OpenSCAD, FreeCAD, or administrative privileges.
  - [x] 7.5 Verify Git remains the only required development tool beyond the native command environment and ordinary operating-system capabilities.
  - [x] 7.6 Verify network, package-manager, privilege, and heavyweight-install approval boundaries are explicit.
  - [x] 7.7 Verify every phase template requires positive, negative, idempotence, isolation, interruption, and rollback evidence where applicable.
  - [x] 7.8 Run documentation link, plan-index, whitespace, and repository-diff checks.
  - [x] 7.9 Confirm all third-party submodules remain clean and unchanged.
  - [x] 7.10 Create the Phase 0 acceptance report from `templates/helper-stack-phase-acceptance-report.md`.
  - [x] 7.11 Stop and request approval before creating or promoting the Phase 1 child plan.

## Acceptance Gate

Phase 0 is accepted only when the host, readiness, command, provider, and phased-delivery contracts are internally consistent; every umbrella workstream 1 item has traceable evidence; the acceptance report records verification results and limitations; and no bootstrap implementation or dependency installation has occurred.
