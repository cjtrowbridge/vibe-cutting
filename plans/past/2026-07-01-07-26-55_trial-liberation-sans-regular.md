---
plan_id: 2026-07-01-07-26-55_trial-liberation-sans-regular
title: Trial Liberation Sans Regular
summary: Replace the default Bold coin lettering with pinned Liberation Sans Regular and validate legibility, spacing, containment, and reproducibility.
status: past
created_at: 2026-07-01-07-26-55
---

# Trial Liberation Sans Regular

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Approved Scope

- [x] 1. Add the regular font weight.
  - [x] 1.1 Pin the unmodified Liberation Sans Regular file and its SHA-256.
  - [x] 1.2 Register Regular alongside Bold in the OpenSCAD geometry source.
  - [x] 1.3 Preserve Bold revisions and their pinned font input.

- [x] 2. Apply the regular-weight trial.
  - [x] 2.1 Create new `shot_coins` and `hug_coins` revisions using Regular.
  - [x] 2.2 Keep character spacing at the font default after close-up comparison.
  - [x] 2.3 Preserve hatch, containment, operation-ordering, and audit contracts.

- [x] 3. Validate and publish.
  - [x] 3.1 Add font-weight and pinned-hash regression coverage.
  - [x] 3.2 Build close-up and full-sheet previews for both designs.
  - [x] 3.3 Run complete tests, exact audits, and deterministic repeat builds.
  - [x] 3.4 Update documentation, roadmap state, and today's journal.
  - [x] 3.5 Archive this plan, commit the trial, and push `main`.
