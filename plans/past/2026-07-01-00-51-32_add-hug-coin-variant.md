---
plan_id: 2026-07-01-00-51-32_add-hug-coin-variant
title: Add Hug Coin Variant
summary: Add and validate a separate 30 mm coin design that engraves HUG instead of SHOT.
status: past
created_at: 2026-07-01-00-51-32
---

# Add Hug Coin Variant

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Approved Scope

- [x] 1. Add the hug design.
  - [x] 1.1 Add the continuous-line vector `U` glyph required by `HUG`.
  - [x] 1.2 Create `designs/hug_coins/project.json` and its first safe revision config.
  - [x] 1.3 Document the hug design's phrase, build command, layout, and calibration status.

- [x] 2. Validate the variant.
  - [x] 2.1 Add design-discovery, phrase, containment, orientation, and glyph coverage.
  - [x] 2.2 Build all 81 hug coins and inspect the generated preview.
  - [x] 2.3 Run exact audits, G-code safety tests, and deterministic repeat-build checks.

- [x] 3. Publish the completed variant.
  - [x] 3.1 Update human documentation, roadmap state, and today's journal.
  - [x] 3.2 Archive this plan, commit the variant, and push `main`.
