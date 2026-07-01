---
plan_id: 2026-07-01-10-32-32_build-reusable-merit-badge-sheets
title: Build Reusable Merit Badge Sheets
summary: Add a reusable mixed-type merit-badge sheet mode and produce BWB, queer sex party, and community garden starter sets with readable title-and-description text.
status: past
created_at: 2026-07-01-10-32-32
---

# Build Reusable Merit Badge Sheets

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Approved Scope

- [x] 1. Define the reusable badge-sheet contract.
  - [x] 1.1 Create and index a merit-badge sheet authoring playbook.
  - [x] 1.2 Create a badge-set schema covering identity, token geometry, typography, layout, and badge content.
  - [x] 1.3 Document the copy-an-existing-set workflow and iteration controls.
  - [x] 1.4 Preserve each supplied title and description verbatim in committed configs.

- [x] 2. Generalize geometry and layout.
  - [x] 2.1 Add `merit_badge_set` as a supported design type without changing existing coin behavior.
  - [x] 2.2 Implement deterministic 4-by-6 grid layout for 72 x 42 mm rounded tokens.
  - [x] 2.3 Distribute 24 token slots evenly across each set's badge types.
  - [x] 2.4 Generate rounded-rectangle cut paths for SVG, PNG preview, and GRBL G-code.
  - [x] 2.5 Assert token cuts remain inside stock and machine limits without overlap.

- [x] 3. Implement readable title-and-description engraving.
  - [x] 3.1 Use pinned Liberation Sans Bold for titles and Regular for descriptions.
  - [x] 3.2 Wrap text using measured OpenSCAD glyph widths rather than character counts.
  - [x] 3.3 Keep title and body sizes, line heights, padding, section gap, and hatch spacing configurable.
  - [x] 3.4 Fail when text cannot fit the configured inner token rectangle.
  - [x] 3.5 Hatch filled text and assert every engraving segment remains inside its owning token.

- [x] 4. Add the initial reusable sets.
  - [x] 4.1 Add `bwb_merit_badges` with nine supplied badge types.
  - [x] 4.2 Add `queer_sex_party_merit_badges` with six supplied badge types.
  - [x] 4.3 Add `community_garden_merit_badges` with eleven supplied badge types.
  - [x] 4.4 Generate manifest counts showing the even slot distribution for each set.

- [x] 5. Validate size and legibility.
  - [x] 5.1 Generate one-token close-ups for the longest title and longest description.
  - [x] 5.2 Build and visually inspect all three 24-token sheets.
  - [x] 5.3 Tune the initial unpublished revisions to 3.0 mm body text; require numbered revisions after publication.
  - [x] 5.4 Run containment, wrapping, allocation, G-code safety, audit, and deterministic-build tests.

- [x] 6. Publish the completed checkpoint.
  - [x] 6.1 Update README, architecture, roadmap state, design docs, and today's journal.
  - [x] 6.2 Archive this plan, commit the implementation, and push `main`.
