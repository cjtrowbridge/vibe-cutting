---
plan_id: 2026-07-06-19-19-57_migrate-boxes-to-provider-helper
title: Migrate Boxes.py to Provider Helper
summary: Convert Boxes.py from the legacy helper path to a locked provider adapter with typed YAML generation, managed setup, deterministic SVG validation, and legacy cleanup.
status: past
created_at: 2026-07-06-19-19-57
---

# Migrate Boxes.py to Provider Helper

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Parent and Phase

- Parent roadmap: `plans/future/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`
- Phase: `3 — Boxes.py migration`
- Parent checklist scope: `6.1` through `6.11`

## Entry Evidence

- Preceding archived child plan: `plans/past/2026-07-06-19-08-31_build-generalized-helper-adapter-platform.md`
- Approved preceding acceptance report: `docs/acceptance/phase-2-generalized-helper-adapter-platform.md`
- Required readiness states: bootstrap state `base-ready`; provider scaffolding accepted; legacy `boxes` adapter remains valid but managed report shows its `.tmp` environment is Python-ABI stale.
- Required submodule pins: `third_party/boxes` clean at `836f5f72bedb33ac4262ed925545eacb31e926a8`.

## Scope

- Convert `tool_adapters/boxes.json` to schema-version `2` using the `pixi_environment` provider.
- Add a locked Boxes provider environment under `setup/` without committing generated `.tools/` state.
- Add `setup/tools/boxes.py` for setup, smoke testing, typed YAML multi-generator execution, and output validation.
- Add a typed Boxes generation request schema and deterministic smoke fixture.
- Preserve SVG-only source geometry, declared operation-color mappings, material thickness, and burn-compensation ownership.
- Update helper docs, playbooks, and tests to use managed bootstrap commands.
- Remove or deprecate the superseded `.tmp/helper-tools/boxes` model only after provider migration validates.
- Exclude host pipeline SVG ingestion, Boxes-generated design configs, CadQuery/CQ_Gears, BOSL2, FreeCAD, and fabrication artifact changes.
- Supported executable platform for validation: Linux x86-64 development host through managed bootstrap.
- Network approval boundary: creating the locked Boxes provider environment may require package downloads and must use explicit tool approval.
- Package-manager approval boundary: no system package managers.
- Privilege approval boundary: no administrative privileges.
- Heavyweight-install approval boundary: no OpenSCAD, FreeCAD, CadQuery, BOSL2, or non-Boxes installs.

## Execution Plan

- [x] 1. Convert the Boxes adapter.
  - [x] 1.1 Update `tool_adapters/boxes.json` to schema-version `2`.
  - [x] 1.2 Declare `pixi_environment` provider setup, invocation, environment, cache, log, temp, and staging paths.
  - [x] 1.3 Preserve source pin, license, capabilities, routing, safety, operation colors, and SVG-only output.
  - [x] 1.4 Add input roots and exact output inventory expectations for YAML multi-generator outputs.
  - [x] 1.5 Set readiness to the highest state proven by this phase and keep `fabrication_approved: false`.

- [x] 2. Lock the Boxes provider environment.
  - [x] 2.1 Add `setup/tools/boxes.py` with setup, smoke, run, and validate subcommands.
  - [x] 2.2 Add a Boxes Pixi manifest or feature file that installs the local `third_party/boxes` source.
  - [x] 2.3 Generate and commit the Boxes lock artifact needed for portable setup.
  - [x] 2.4 Write environment markers with source revision, adapter hash, lock hashes, package versions, Python version, and provider fingerprint.
  - [x] 2.5 Keep cache, logs, temp, staging, and environments under `.tools/`.
  - [x] 2.6 Fail closed on dirty source, pin mismatch, missing license, missing lock, install failure, or import failure.

- [x] 3. Implement typed Boxes generation.
  - [x] 3.1 Add `schemas/boxes_generation_request.schema.json`.
  - [x] 3.2 Accept only YAML multi-generator requests with explicit output directory and expected SVG inventory.
  - [x] 3.3 Enforce repository-relative input/output paths and declared roots.
  - [x] 3.4 Preserve deterministic YAML multi-generator behavior.
  - [x] 3.5 Validate SVG output presence, extension, XML parseability, hashes, and declared inventory.
  - [x] 3.6 Reject non-SVG authoritative output and unknown operation colors.
  - [x] 3.7 Preserve prior authoritative outputs on setup or generation failure.
  - [x] 3.8 Confirm Boxes.py never mutates `third_party/boxes`.

- [x] 4. Add tests.
  - [x] 4.1 Add provider manifest validation tests for migrated `boxes`.
  - [x] 4.2 Add managed setup readiness tests with network-dependent portions isolated behind explicit approval.
  - [x] 4.3 Add deterministic generation tests for a RegularBox YAML fixture.
  - [x] 4.4 Add malformed YAML, path escape, unknown color, missing output, extra output, and source mutation tests.
  - [x] 4.5 Add provider marker, lock-hash, request-hash, output-hash, and package-provenance tests.
  - [x] 4.6 Remove or update legacy `.tmp/helper-tools/boxes` tests after provider tests pass.

- [x] 5. Update docs and governance.
  - [x] 5.1 Update `docs/tools/boxes.md` for provider setup and managed commands.
  - [x] 5.2 Update `docs/helper-tools.md` to remove the Boxes legacy exception.
  - [x] 5.3 Update `playbooks/how_to_use_boxes_for_laser_geometry.md`.
  - [x] 5.4 Update `playbooks/how_to_add_and_validate_a_helper_tool.md` if migration reveals provider playbook gaps.
  - [x] 5.5 Update `AGENTS.md` helper-routing text.
  - [x] 5.6 Update README helper commands if the human-facing workflow changes.

- [x] 6. Verify and accept Phase 3.
  - [x] 6.1 Run Boxes provider setup through the managed bootstrap with explicit download approval if needed.
  - [x] 6.2 Run Boxes smoke generation through the provider driver and verify deterministic SVG output.
  - [x] 6.3 Run the complete host test suite.
  - [x] 6.4 Verify plan indexes, whitespace, and repository diff.
  - [x] 6.5 Verify every recursive submodule remains clean and pinned.
  - [x] 6.6 Create `docs/acceptance/phase-3-boxes-provider-migration.md`.
  - [x] 6.7 Update umbrella workstream 6 only where implementation evidence is complete.
  - [x] 6.8 Record and archive the accepted checkpoint, then continue to Phase 4 under standing execution approval.

## Verification

- Positive-path tests: provider setup reaches `invocation-ready`; deterministic YAML multi-generator smoke fixture produces byte-identical SVG.
- Negative-path tests: dirty source, pin mismatch, missing license, path escapes, malformed YAML, unknown colors, missing/extra outputs, and import failures fail closed.
- Idempotence tests: repeated setup and repeated generation produce stable markers and outputs.
- Isolation and path-confinement tests: no writes outside `.tools/`, `.tmp/`, `output/`, `revisions/`, or declared fixture roots.
- Interruption and safe-resume tests: incomplete provider staging is cleaned or safely resumed.
- Rollback and prior-state preservation tests: failed setup/generation preserves previous authoritative outputs.
- Submodule cleanliness checks: recursive submodules clean before acceptance.
- Platform-specific checks: Linux x86-64 managed-bootstrap validation only; other platforms remain unqualified.
- Documentation and index checks: no remaining docs describe Boxes.py as permanently legacy after acceptance.

## Rollback

- Restore the Phase 2 `tool_adapters/boxes.json` legacy adapter if provider migration cannot be accepted.
- Remove generated `.tools/` Boxes provider state rather than committing it.
- Preserve `third_party/boxes` without source changes.
- Preserve prior authoritative outputs on generation failure.

## Stop Condition

Stop if Boxes.py cannot be installed into the managed provider environment, deterministic multi-generator SVG cannot be reproduced, provider setup requires global packages or privileges, or the migration breaks legacy-safe host validation guarantees.

## Acceptance Gate

- Acceptance report path: `docs/acceptance/phase-3-boxes-provider-migration.md`
- Required decision: accepted with non-Linux platforms explicitly labeled unqualified until Phase 9.
- Downstream Phase 4 is prohibited until this plan is archived and its report is accepted.
