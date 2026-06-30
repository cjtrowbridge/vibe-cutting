---
plan_id: 2026-06-30-13-38-55_implement-vector-mvp-and-shot-coin-test
title: Implement Vector MVP and Shot Coin Test
summary: Build the dependency-free vector laser pipeline and validate it with a maximally packed 30 mm basswood shot-coin design.
status: past
created_at: 2026-06-30-13-38-55
---

# Implement Vector MVP and Shot Coin Test

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Approved Scope

- [x] 1. Establish MVP governance and structure.
  - [x] 1.1 Record Python 3.11+ and standard-library-only as the initial runtime baseline.
  - [x] 1.2 Record the unavailable OpenSCAD tool as a deferred adapter rather than an MVP blocker.
  - [x] 1.3 Create MVP build, design, G-code, machine-profile, and safety playbooks.
  - [x] 1.4 Create machine, material, schema, design, output, revision, temporary, test, and documentation directories.

- [x] 2. Implement the build pipeline.
  - [x] 2.1 Implement `scripts/laser_build.py` with design discovery and config loading.
  - [x] 2.2 Implement deterministic geometry, layout, SVG, PNG preview, and GRBL G-code generation.
  - [x] 2.3 Implement machine/material preflight and safe operation ordering.
  - [x] 2.4 Implement staged atomic output installation and exact build manifests.
  - [x] 2.5 Implement dry-run, validate-only, audit-only, quantity, and new-revision modes.

- [x] 3. Add the first machine, material, and design.
  - [x] 3.1 Add the provisional Creality Falcon A1 Pro 20 W machine profile.
  - [x] 3.2 Add the unverified 3 mm basswood material profile.
  - [x] 3.3 Add a 30 mm shot-coin design with five engraved text lines.
  - [x] 3.4 Implement deterministic maximum hex packing on a 300 x 300 mm sheet.

- [x] 4. Validate the complete pipeline.
  - [x] 4.1 Run focused automated tests for packing, bounds, G-code safety, and manifests.
  - [x] 4.2 Run dry-run and validate-only modes.
  - [x] 4.3 Build `output/shot_coins/` and audit the installed artifacts.
  - [x] 4.4 Create and audit an immutable numbered revision.
  - [x] 4.5 Document artifact counts, coin quantity, bounds, and test-readiness limitations.
  - [x] 4.6 Review diffs, update roadmap state, journal the checkpoint, commit, and push `main`.
