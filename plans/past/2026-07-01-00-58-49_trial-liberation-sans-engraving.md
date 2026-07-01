---
plan_id: 2026-07-01-00-58-49_trial-liberation-sans-engraving
title: Trial Liberation Sans Engraving
summary: Add an OpenSCAD-backed Liberation Sans Bold engraving mode and validate it on both coin designs.
status: past
created_at: 2026-07-01-00-58-49
---

# Trial Liberation Sans Engraving

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Approved Scope

- [x] 1. Establish the font adapter contract.
  - [x] 1.1 Record OpenSCAD 2021.01, Liberation Sans Bold, and SIL OFL 1.1 evidence.
  - [x] 1.2 Create and index the OpenSCAD laser-geometry authoring playbook.
  - [x] 1.3 Define config fields for text backend, logical font, fill mode, hatch spacing, and line spacing.

- [x] 2. Implement normal-font engraving.
  - [x] 2.1 Add a generic OpenSCAD text-to-SVG geometry source.
  - [x] 2.2 Invoke OpenSCAD without a shell and fail clearly when the executable or pinned font is unavailable.
  - [x] 2.3 Parse exported linear SVG contours and reject unsupported commands.
  - [x] 2.4 Scale multiline glyph geometry inside the circular engraving inset.
  - [x] 2.5 Convert filled glyph contours into deterministic hatch segments.
  - [x] 2.6 Preserve fail-closed containment, operation ordering, and exact artifact audits.

- [x] 3. Apply and validate the trial.
  - [x] 3.1 Add new Liberation Sans revisions for `shot_coins` and `hug_coins`.
  - [x] 3.2 Add parser, configuration, font, containment, manifest, orientation, and deterministic-build tests.
  - [x] 3.3 Build and visually inspect both 81-coin previews.
  - [x] 3.4 Run complete tests, exact audits, and repeat-build hash comparisons.

- [x] 4. Publish the completed trial.
  - [x] 4.1 Update human documentation, architecture, roadmap state, and today's journal.
  - [x] 4.2 Archive this plan, commit the trial, and push `main`.
