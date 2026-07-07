---
plan_id: 2026-07-06-19-48-06_integrate-cadquery-and-cq-gears-provider
title: Integrate CadQuery and CQ_Gears Provider
summary: Add a bounded CadQuery/CQ_Gears provider for validated planar gear geometry, provenance, smoke tests, and documentation without granting fabrication authority.
status: past
created_at: 2026-07-06-19-48-06
---

# Integrate CadQuery and CQ_Gears Provider

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Parent and Phase

- Parent roadmap: `plans/future/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`
- Phase: `4 — CadQuery and CQ_Gears`
- Parent checklist scope: `7.1` through `7.14`

## Entry Evidence

- Preceding archived child plan: `plans/past/2026-07-06-19-19-57_migrate-boxes-to-provider-helper.md`
- Approved preceding acceptance report: `docs/acceptance/phase-3-boxes-provider-migration.md`
- Required readiness states: bootstrap `base-ready`; provider platform accepted; Boxes provider migration accepted.
- Required submodule pins: `third_party/cadquery` and `third_party/cq_gears` clean and pinned.

## Scope

- Add a combined `cq_gears` provider adapter that references both local submodule pins.
- Add typed schemas for planar spur gears, ring gears, racks, and simple meshing-pair requests.
- Add `setup/tools/cq_gears.py` for dependency inspection, setup, smoke testing, and deterministic planar profile generation.
- Prefer Python 3.12 through the managed bootstrap and fail closed if CadQuery/CQ_Gears cannot be installed locally.
- Export source inspection geometry and normalized two-dimensional profiles for provenance only.
- Reject helical, herringbone, bevel, worm, or other non-planar requests.
- Add docs for the limited planar subset and non-fabrication status.
- Exclude mechanism graph integration, host laser design ingestion, BOSL2 comparison, FreeCAD inspection, and fabrication artifacts.
- Supported executable platform for validation: Linux x86-64 development host through managed bootstrap.
- Network approval boundary: provider setup may download Conda/PyPI packages and requires explicit approval.
- Package-manager approval boundary: no system package managers.
- Privilege approval boundary: no administrative privileges.
- Heavyweight-install approval boundary: CadQuery/OCP install is allowed only in repository-local `.tools/` state for this phase.

## Execution Plan

- [x] 1. Inspect compatibility and pins.
  - [x] 1.1 Record CadQuery and CQ_Gears source pins.
  - [x] 1.2 Inspect package metadata for Python and dependency constraints.
  - [x] 1.3 Select Python 3.12 as the initial provider runtime candidate.
  - [x] 1.4 Define unsupported request classes and failure messages.

- [x] 2. Add adapter and schemas.
  - [x] 2.1 Create `tool_adapters/cq_gears.json`.
  - [x] 2.2 Add `schemas/cq_gears_request.schema.json`.
  - [x] 2.3 Add fields for module, tooth count, pressure angle, width, bore, addendum, dedendum, and backlash.
  - [x] 2.4 Add fields for spur gears, ring gears, racks, and meshing pairs.
  - [x] 2.5 Declare STEP and SVG as provenance outputs, not authoritative fabrication artifacts.

- [x] 3. Implement provider driver.
  - [x] 3.1 Create `setup/tools/cq_gears.py`.
  - [x] 3.2 Implement setup with repository-local environment, marker, package versions, and lock hashes.
  - [x] 3.3 Prevent package resolution from replacing local CadQuery or CQ_Gears source pins.
  - [x] 3.4 Implement smoke validation for imports and a basic spur gear request.
  - [x] 3.5 Implement deterministic two-dimensional profile export for supported planar requests.
  - [-] 3.6 Implement STEP export when CadQuery supports it in the managed environment.
  - [x] 3.7 Reject non-planar gear types before invocation.

- [x] 4. Add tests.
  - [x] 4.1 Add adapter validation and source-pin tests.
  - [x] 4.2 Add request schema and unsupported-request tests.
  - [x] 4.3 Add setup-marker and readiness tests.
  - [x] 4.4 Add deterministic profile smoke tests when the provider is installed.
  - [x] 4.5 Add geometry sanity checks for pitch diameter, outside diameter, root diameter, tooth count, bore, and closure.
  - [x] 4.6 Verify source submodules remain clean after setup and invocation.

- [x] 5. Update docs and governance.
  - [x] 5.1 Add `docs/tools/cq-gears.md`.
  - [x] 5.2 Update `docs/helper-tools.md`.
  - [x] 5.3 Add `playbooks/how_to_use_cq_gears_for_laser_mechanisms.md`.
  - [x] 5.4 Update `AGENTS.md` helper routing.
  - [x] 5.5 Update README only if human-facing helper commands change.

- [x] 6. Verify and accept Phase 4.
  - [x] 6.1 Run provider setup through the managed bootstrap with explicit download approval if needed.
  - [x] 6.2 Run provider smoke and deterministic profile generation.
  - [x] 6.3 Run the complete host test suite.
  - [x] 6.4 Verify plan indexes, whitespace, and repository diff.
  - [x] 6.5 Verify every recursive submodule remains clean and pinned.
  - [x] 6.6 Create `docs/acceptance/phase-4-cadquery-cq-gears-provider.md`.
  - [x] 6.7 Update umbrella workstream 7 only where implementation evidence is complete.
  - [x] 6.8 Record and archive the accepted checkpoint, then continue to Phase 5 under standing execution approval.

## Stop Condition

Stop if CadQuery/OCP cannot be installed into a repository-local managed environment, local submodule pins cannot be preserved, deterministic planar profile export cannot be proven, or the provider attempts global installs or source mutation.

## Acceptance Gate

- Acceptance report path: `docs/acceptance/phase-4-cadquery-cq-gears-provider.md`
- Required decision: accepted with non-Linux platforms explicitly labeled unqualified until Phase 9.
- Downstream Phase 5 is prohibited until this plan is archived and its report is accepted.
