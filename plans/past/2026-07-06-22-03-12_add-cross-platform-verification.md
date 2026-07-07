---
plan_id: 2026-07-06-22-03-12_add-cross-platform-verification
title: Add Cross-Platform Verification
summary: Add CI scaffolding, evidence publication, and support-matrix documentation for Linux, Windows, and macOS bootstrap qualification without claiming fabrication readiness.
status: past
created_at: 2026-07-06-22-03-12
---

# Add Cross-Platform Verification

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Parent and Phase

- Parent roadmap: `plans/future/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`
- Phase: `9 — Cross-platform qualification and rollout`
- Parent checklist scope: `15.1` through `15.6`

## Entry Evidence

- Preceding archived child plan: `plans/past/2026-07-06-20-51-05_test-portable-bootstrap-behavior.md`
- Approved preceding acceptance report: `docs/acceptance/phase-11-portable-bootstrap-behavior.md`
- Required readiness states: local Linux bootstrap behavior accepted; non-Linux platforms still pending CI evidence.
- Required submodule pins: Current clean recursive gitlinks.

## Scope

- Add GitHub Actions coverage for Linux, Windows PowerShell, and macOS bootstrap commands.
- Publish host-readiness reports as CI artifacts.
- Cache only checksum-validated manager downloads and lock-addressed managed environment roots.
- Keep heavyweight helper validation optional so runner resource limits do not block bootstrap qualification.
- Document that CI evidence is setup/toolchain evidence, not fabrication approval.

## Execution Plan

- [x] 1. Add CI bootstrap coverage.
  - [x] 1.1 Create a Linux job that runs `setup/bootstrap.sh` doctor, setup, verify, managed run, and readiness report commands.
  - [x] 1.2 Create a Windows job that runs `setup/bootstrap.ps1` doctor, setup, verify, managed run, and readiness report commands.
  - [x] 1.3 Create a macOS job that runs `setup/bootstrap.sh` doctor, setup, verify, managed run, and readiness report commands.
  - [x] 1.4 Check out recursive submodules before bootstrap commands.

- [x] 2. Add controlled cache and heavy-test policy.
  - [x] 2.1 Key caches from runner platform plus `setup/pixi.lock`, Pixi checksums, setup locks, and helper lock files.
  - [x] 2.2 Cache only repository-local `.tools/cache`, `.tools/pixi-home`, and `.tools/environments`.
  - [x] 2.3 Add an opt-in heavyweight helper validation path for FreeCAD and other large providers.
  - [x] 2.4 Keep default CI focused on bootstrap readiness and lightweight managed commands.

- [x] 3. Publish evidence without overclaiming.
  - [x] 3.1 Upload host-readiness reports from every platform job.
  - [x] 3.2 Update `docs/toolchain-support-matrix.md` with CI artifact expectations and readiness caveats.
  - [x] 3.3 Add a CI verification documentation page.
  - [x] 3.4 Add an acceptance report for this phase.

- [x] 4. Verify and archive.
  - [x] 4.1 Run plan index regeneration.
  - [x] 4.2 Run repository tests.
  - [x] 4.3 Verify whitespace and staged diffs.
  - [x] 4.4 Mark parent checklist items `15.1` through `15.6` complete.
  - [x] 4.5 Record the checkpoint in today’s journal.
  - [x] 4.6 Archive this child plan and refresh indexes.
  - [x] 4.7 Commit and push the completed checkpoint.
