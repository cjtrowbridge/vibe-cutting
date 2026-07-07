---
plan_id: 2026-07-06-20-02-16_integrate-bosl2-openscad-provider
title: Integrate BOSL2 OpenSCAD Provider
summary: Add BOSL2 as a pinned OpenSCAD library provider for experimental planar gear comparison profiles without granting fabrication authority.
status: past
created_at: 2026-07-06-20-02-16
---

# Integrate BOSL2 OpenSCAD Provider

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Parent and Phase

- Parent roadmap: `plans/past/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`
- Phase: `5 — BOSL2 and managed OpenSCAD`
- Parent checklist scope: `8.1` through `8.10`

## Entry Evidence

- Preceding archived child plan: `plans/past/2026-07-06-19-48-06_integrate-cadquery-and-cq-gears-provider.md`
- Approved preceding acceptance report: `docs/acceptance/phase-4-cadquery-cq-gears-provider.md`
- Required readiness states: bootstrap `base-ready`; CQ_Gears provider accepted for planar source profiles.
- Required submodule pin: `third_party/bosl2` clean at `fbcdfdd511b6abfde93c43c8f85c2bd24ee7a02d`.

## Scope

- Add `tool_adapters/bosl2.json` as an `openscad_library` provider.
- Add typed BOSL2 planar gear request schema aligned with the currently accepted comparison subset.
- Add `setup/tools/bosl2.py` for dependency detection, include-path setup, smoke testing, and SVG output validation.
- Configure `OPENSCADPATH` per invocation without changing user-global OpenSCAD configuration.
- Generate deterministic SVG comparison profiles for spur gears, ring gears, and racks when supported.
- Document BOSL2 as a comparison/fallback geometry backend, not the mechanism validator.
- Exclude OpenSCAD acquisition, managed OpenSCAD packaging, host mechanism graph integration, and fabrication artifacts.
- Supported executable platform for validation: Linux x86-64 development host with `/usr/bin/openscad` 2021.01.
- Network approval boundary: no network access required.
- Package-manager approval boundary: no system package managers.
- Privilege approval boundary: no administrative privileges.

## Execution Plan

- [x] 1. Add BOSL2 adapter and schema.
  - [x] 1.1 Create `tool_adapters/bosl2.json`.
  - [x] 1.2 Add `schemas/bosl2_gear_request.schema.json`.
  - [x] 1.3 Declare the BOSL2 submodule pin, license, include path, provider roots, outputs, and readiness states.
  - [x] 1.4 Declare supported spur/ring/rack comparison requests and unsupported requests.

- [x] 2. Implement OpenSCAD provider driver.
  - [x] 2.1 Create `setup/tools/bosl2.py`.
  - [x] 2.2 Detect `openscad` and record its path/version.
  - [x] 2.3 Configure `OPENSCADPATH` per process only.
  - [x] 2.4 Generate host-owned OpenSCAD wrapper source under `.tmp/`.
  - [x] 2.5 Export deterministic SVG output through OpenSCAD.
  - [x] 2.6 Validate SVG parseability, hashes, and declared inventory.
  - [x] 2.7 Reject unsupported request types before invoking OpenSCAD.

- [x] 3. Add tests.
  - [x] 3.1 Add adapter validation and source-pin tests.
  - [x] 3.2 Add OpenSCAD detection and provider readiness tests.
  - [x] 3.3 Add deterministic SVG smoke tests for supported comparison requests.
  - [x] 3.4 Add unsupported request and path confinement tests.
  - [x] 3.5 Verify BOSL2 source remains clean after invocation.

- [x] 4. Update docs and governance.
  - [x] 4.1 Add `docs/tools/bosl2.md`.
  - [x] 4.2 Add `playbooks/how_to_use_bosl2_gear_geometry.md`.
  - [x] 4.3 Update `docs/helper-tools.md`.
  - [x] 4.4 Update `AGENTS.md` helper routing.
  - [x] 4.5 Update `references/geometry-backend-selection.md`.

- [x] 5. Verify and accept Phase 5.
  - [x] 5.1 Run BOSL2 provider check and smoke through the managed bootstrap.
  - [x] 5.2 Run the complete host test suite.
  - [x] 5.3 Verify plan indexes, whitespace, and repository diff.
  - [x] 5.4 Verify every recursive submodule remains clean and pinned.
  - [x] 5.5 Create `docs/acceptance/phase-5-bosl2-openscad-provider.md`.
  - [x] 5.6 Update umbrella workstream 8 only where implementation evidence is complete.
  - [x] 5.7 Record and archive the accepted checkpoint, then continue to Phase 6 under standing execution approval.

## Stop Condition

Stop if OpenSCAD cannot import BOSL2 without global configuration, deterministic SVG cannot be generated, or BOSL2 output cannot remain clearly marked as comparison-only source geometry.

## Acceptance Gate

- Acceptance report path: `docs/acceptance/phase-5-bosl2-openscad-provider.md`
- Required decision: accepted with non-Linux platforms explicitly labeled unqualified until Phase 9.
- Downstream Phase 6 is prohibited until this plan is archived and its report is accepted.
