---
plan_id: 2026-07-06-19-08-31_build-generalized-helper-adapter-platform
title: Build Generalized Helper Adapter Platform
summary: Implement Phase 2 provider-discriminated helper adapter contracts, setup-provider scaffolding, typed request/result schemas, provenance, and common validation without migrating Boxes.py yet.
status: past
created_at: 2026-07-06-19-08-31
---

# Build Generalized Helper Adapter Platform

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Parent and Phase

- Parent roadmap: `plans/past/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`
- Phase: `2 — Generalized helper adapter platform`
- Parent checklist scope: `4.1` through `5.10`

## Entry Evidence

- Preceding archived child plan: `plans/past/2026-07-06-10-44-27_build-native-bootstrap-and-managed-base-runtime.md`
- Approved preceding acceptance report: `docs/acceptance/phase-1-native-bootstrap-and-managed-base-runtime.md`
- Required readiness states: bootstrap state `base-ready` and managed `run` operational on Linux x86-64.
- Required submodule pins: current recursive gitlinks clean and pinned.

## Scope

- Create provider-neutral helper adapter schema support without migrating `tool_adapters/boxes.json` to the new provider contract in this phase.
- Add schemas for helper requests, helper results, provider identities, environment fingerprints, provenance, output inventories, and readiness evidence.
- Add `setup/providers/` scaffolding for `pixi_environment`, `openscad_library`, `system_application`, and `manual_operator` provider types.
- Add `setup/tools/` scaffolding for provider setup and smoke-test drivers without tool-specific Boxes.py migration.
- Add validation and report commands that can inspect legacy adapters and future provider adapters.
- Modify docs and playbooks to tell agents how to route through provider abstractions after Phase 2.
- Exclude actual Boxes.py environment migration, CadQuery/CQ_Gears setup, BOSL2 setup, FreeCAD setup, fabrication behavior changes, and generated laser artifacts.
- Supported executable platform for validation: Linux x86-64 development host through managed bootstrap.
- Network approval boundary: no network access required for schema/provider scaffolding tests.
- Package-manager approval boundary: no system package managers.
- Privilege approval boundary: no administrative privileges.
- Heavyweight-install approval boundary: no OpenSCAD, FreeCAD, CadQuery, BOSL2, or Boxes.py dependency installs in this phase.

## Execution Plan

- [x] 1. Define generalized adapter schemas.
  - [x] 1.1 Add a provider-discriminated adapter schema while preserving legacy schema validation for `boxes`.
  - [x] 1.2 Add common adapter identity, capability, routing, source, license, platform, safety, and readiness fields.
  - [x] 1.3 Add provider-specific setup, invocation, version, and environment fields.
  - [x] 1.4 Add typed helper request and helper result schemas.
  - [x] 1.5 Add environment-fingerprint and provenance schemas.
  - [x] 1.6 Add exact output inventory and output-hash schema fields.

- [x] 2. Implement provider scaffolding.
  - [x] 2.1 Create `setup/providers/__init__.py`.
  - [x] 2.2 Create `setup/providers/base.py` for provider contracts and shared validation helpers.
  - [x] 2.3 Create `setup/providers/pixi.py` with no-network dry validation and future environment hooks.
  - [x] 2.4 Create `setup/providers/openscad.py` with executable detection and version-report hooks.
  - [x] 2.5 Create `setup/providers/system_application.py` with manual remediation diagnostics.
  - [x] 2.6 Create `setup/providers/manual_operator.py` for tools that cannot be automated.
  - [x] 2.7 Create `setup/tools/__init__.py` and shared tool-driver helpers.
  - [x] 2.8 Ensure provider code writes only beneath declared repository-local roots.

- [x] 3. Extend helper dispatcher behavior.
  - [x] 3.1 Teach `scripts/helper_tool.py` to validate both legacy and provider adapter manifests.
  - [x] 3.2 Add provider-aware `describe` output without exposing internal host paths.
  - [x] 3.3 Add readiness report generation for registered provider adapters.
  - [x] 3.4 Enforce repository-relative input and output paths in request validation.
  - [x] 3.5 Enforce declared output formats and exact output inventories.
  - [x] 3.6 Preserve previous authoritative outputs on helper setup or invocation failure.
  - [x] 3.7 Detect source-submodule mutation after setup and invocation.
  - [x] 3.8 Keep legacy `boxes` commands operational until Phase 3 migration.

- [x] 4. Add tests.
  - [x] 4.1 Add schema tests for provider discriminator acceptance and invalid-provider rejection.
  - [x] 4.2 Add path-confinement tests for provider roots, request inputs, outputs, logs, cache, and temporary paths.
  - [x] 4.3 Add readiness-state tests for registered, dependencies-ready, invocation-ready, output-validated, pipeline-integrated, and fabrication-approved boundaries.
  - [x] 4.4 Add provenance tests for pins, lock hashes, runtime versions, request hashes, output hashes, and environment fingerprints.
  - [x] 4.5 Add failure-preservation tests that prove authoritative outputs are not replaced by partial helper output.
  - [x] 4.6 Add submodule mutation detection tests using isolated fixtures.
  - [x] 4.7 Add managed-bootstrap invocation tests for provider validation commands.
  - [x] 4.8 Keep existing Boxes.py integration tests passing through the legacy path.

- [x] 5. Update governance and documentation.
  - [x] 5.1 Update `AGENTS.md` with provider-first helper-routing rules.
  - [x] 5.2 Update `docs/helper-tools.md` for provider types, readiness states, and Phase 2 limitations.
  - [x] 5.3 Update `references/helper-tool-contract.md`.
  - [x] 5.4 Add `references/helper-runtime-providers.md`.
  - [x] 5.5 Update `playbooks/how_to_add_and_validate_a_helper_tool.md`.
  - [x] 5.6 Update `playbooks/how_to_use_boxes_for_laser_geometry.md` to call out the Phase 3 migration boundary.
  - [x] 5.7 Update README only where human-facing helper setup commands change.

- [x] 6. Verify and accept Phase 2.
  - [x] 6.1 Run the complete host test suite.
  - [x] 6.2 Run managed provider validation through `setup/bootstrap.sh run -- scripts/helper_tool.py ...`.
  - [x] 6.3 Verify no global package, Python, OpenSCAD, FreeCAD, or helper dependency installs occur.
  - [x] 6.4 Verify plan indexes, whitespace, and repository diff.
  - [x] 6.5 Verify every recursive submodule remains clean and pinned.
  - [x] 6.6 Create `docs/acceptance/phase-2-generalized-helper-adapter-platform.md`.
  - [x] 6.7 Update umbrella workstreams 4 and 5 only where implementation evidence is complete.
  - [x] 6.8 Record and archive the accepted checkpoint, then continue to Phase 3 under standing execution approval.

## Verification

- Positive-path tests: legacy Boxes adapter remains valid; sample provider manifests validate; provider readiness reports render deterministically.
- Negative-path tests: unknown providers, invalid paths, dirty source, missing outputs, unexpected outputs, and partial failures fail closed.
- Idempotence tests: repeated validation and report generation produce stable evidence without mutating submodules or outputs.
- Isolation and path-confinement tests: provider setup/reporting writes only beneath `.tools/`, `.tmp/`, `output/`, `revisions/`, or explicit fixture roots.
- Interruption and safe-resume tests: partial provider staging data is ignored or safely resumable without replacing prior authoritative outputs.
- Rollback and prior-state preservation tests: failed helper/provider operations keep existing output inventories unchanged.
- Submodule cleanliness checks: recursive submodules clean before acceptance.
- Platform-specific checks: Linux x86-64 managed-bootstrap validation only; other platforms remain unqualified.
- Documentation and index checks: docs reflect transitional legacy Boxes path and future provider migration boundary.

## Rollback

- Preserve Phase 1 bootstrap files and locked runtime.
- Preserve legacy `tool_adapters/boxes.json` and the current Boxes.py helper behavior.
- Remove only new provider scaffolding, schemas, docs, and tests if Phase 2 cannot be accepted.
- Never modify third-party submodule contents during rollback.

## Stop Condition

Stop if provider adapters cannot coexist with the legacy Boxes adapter, provider validation requires unapproved network or global installs, path confinement cannot be enforced, or failure handling risks replacing authoritative outputs with partial helper artifacts.

## Acceptance Gate

- Acceptance report path: `docs/acceptance/phase-2-generalized-helper-adapter-platform.md`
- Required decision: accepted with any non-Linux platforms explicitly labeled unqualified until Phase 9.
- Downstream Phase 3 is prohibited until this plan is archived and its report is accepted.
