---
plan_id: 2026-07-06-10-44-27_build-native-bootstrap-and-managed-base-runtime
title: Build Native Bootstrap and Managed Base Runtime
summary: Implement Phase 1 native bootstrap launchers, pinned manager acquisition, managed Python execution, host Git verification, submodule checks, and clean-host tests.
status: past
created_at: 2026-07-06-10-44-27
---

# Build Native Bootstrap and Managed Base Runtime

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Parent and Phase

- Parent roadmap: `plans/past/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`
- Phase: `1 — Native bootstrap and managed base runtime`
- Parent checklist scope: `2.1` through `3.9`

## Entry Evidence

- Preceding archived child plan: `plans/past/2026-07-06-10-29-35_define-portable-helper-bootstrap-contracts.md`
- Approved preceding acceptance report: `docs/acceptance/phase-0-portable-helper-bootstrap-contracts.md`
- Required readiness states: Phase 0 contracts accepted; runtime remains `uninitialized`.
- Required submodule pins: Current clean recursive gitlinks.

## Scope

- Create `setup/` native launchers, manifest, checksums, Pixi base environment, stage-two orchestrator, and setup documentation.
- Add bootstrap contract and clean-host tests under `tests/`.
- Update agent governance and human architecture/build documentation for implemented behavior.
- Supported implementation targets: Linux x86-64, Linux ARM64, Windows x86-64, macOS Intel, and macOS Apple silicon.
- Executable qualification in this phase: development-host Linux x86-64; other targets require Phase 9 CI evidence.
- Exclude helper-provider migration, Boxes.py migration, mechanism geometry, and fabrication changes.
- Network downloads require tool-level approval.
- System package managers and privileges are prohibited in the supported path.

## Execution Plan

- [x] 1. Select and pin the environment manager.
  - [x] 1.1 Verify official Pixi platform artifacts and checksum publication.
  - [x] 1.2 Verify repository-local environment and cache placement controls.
  - [x] 1.3 Record the selected Pixi version, artifact URLs, archive formats, and SHA-256 values.
  - [x] 1.4 Create `setup/toolchain-manifest.json`.
  - [x] 1.5 Create checksum records under `setup/checksums/`.

- [x] 2. Implement native launchers.
  - [x] 2.1 Create POSIX-compatible `setup/bootstrap.sh`.
  - [x] 2.2 Create Windows PowerShell-compatible `setup/bootstrap.ps1`.
  - [x] 2.3 Implement repository-root and supported-platform detection.
  - [x] 2.4 Implement host Git 2.31+ verification.
  - [x] 2.5 Implement native downloader, SHA-256 verifier, and archive extraction selection.
  - [x] 2.6 Implement staged manager installation beneath `.tools/bin/`.
  - [x] 2.7 Refuse unapproved downloads through an explicit `--allow-downloads` gate.
  - [x] 2.8 Prevent writes outside declared repository-local paths.
  - [x] 2.9 Dispatch stage-two commands through the pinned manager.

- [x] 3. Implement the managed base environment.
  - [x] 3.1 Create `setup/pixi.toml` with pinned Python and supported platforms.
  - [x] 3.2 Generate and commit `setup/pixi.lock`.
  - [x] 3.3 Keep manager, cache, environments, logs, reports, staging, and temporary files beneath `.tools/`.
  - [x] 3.4 Create `setup/bootstrap_host.py`.
  - [x] 3.5 Implement `doctor`, `setup`, `verify`, `repair`, `report`, and `run`.
  - [x] 3.6 Implement bootstrap-state evidence and actionable diagnostics.
  - [x] 3.7 Implement recursive host-Git submodule initialization and verification.
  - [x] 3.8 Detect missing, dirty, uninitialized, and mismatched submodules.
  - [x] 3.9 Record host Git, manager, lock, runtime, and submodule evidence in readiness reports.
  - [x] 3.10 Dispatch repository Python scripts exclusively through managed Python.
  - [x] 3.11 Preserve delegated arguments, streams, working directory, interrupts, and exit status.

- [x] 4. Document the implemented bootstrap.
  - [x] 4.1 Create `setup/README.md`.
  - [x] 4.2 Update `AGENTS.md` from target-contract wording to implemented bootstrap commands.
  - [x] 4.3 Update `README.md` with concise human-facing bootstrap quick starts.
  - [x] 4.4 Update `docs/architecture.md` and `docs/build-script-reference.md`.
  - [x] 4.5 Keep transitional direct-Python commands explicitly labeled until later migration phases.

- [x] 5. Add unit and integration tests.
  - [x] 5.1 Add manifest, platform mapping, checksum, and path-confinement tests.
  - [x] 5.2 Add missing/obsolete Git and unsupported-platform tests.
  - [x] 5.3 Add no-download `doctor` tests.
  - [x] 5.4 Add checksum mismatch and incomplete-staging refusal tests.
  - [x] 5.5 Add managed `run` path, argument, exit-code, and host-Python masking tests.
  - [x] 5.6 Add submodule missing, dirty, and revision-mismatch tests using isolated fixtures.
  - [x] 5.7 Add repeated setup and repair idempotence tests.
  - [x] 5.8 Verify no global package, Python, OpenSCAD, FreeCAD, or submodule state changes.

- [x] 6. Verify and accept Phase 1.
  - [x] 6.1 Bootstrap from an empty alternate tools root on Linux x86-64.
  - [x] 6.2 Verify `scripts/laser_build.py --help` through managed `run` while host Python is masked.
  - [x] 6.3 Run the complete host test suite.
  - [x] 6.4 Verify plan indexes, documentation references, whitespace, and repository diff.
  - [x] 6.5 Verify every recursive submodule remains clean and pinned.
  - [x] 6.6 Create `docs/acceptance/phase-1-native-bootstrap-and-managed-base-runtime.md`.
  - [x] 6.7 Update umbrella workstreams 2 and 3 only where implementation evidence is complete.
  - [x] 6.8 Record and archive the accepted checkpoint, then continue to Phase 2 under standing execution approval.

## Rollback

- Preserve any complete prior `.tools/` installation until a staged replacement verifies successfully.
- Remove only incomplete paths beneath `.tools/staging/`.
- Restore launchers, manifest, lock, and checksums together.
- Never modify third-party submodule contents during rollback.

## Stop Condition

Stop if official artifacts cannot be pinned and verified, repository-local placement cannot be enforced, managed Python cannot run with host Python masked, or submodule state changes.

## Acceptance Gate

Phase 1 is accepted when Linux x86-64 clean-root bootstrap and managed execution pass, all platform artifacts are pinned, untested platforms are labeled unqualified, all tests pass, and no global or submodule state changes occur.
