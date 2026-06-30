---
plan_id: 2026-06-30-13-57-36_enforce-engraving-containment
title: Enforce Engraving Containment
summary: Make shot-coin text legible, correctly oriented, contained inside its circular cut boundary, and rejected if any engraving geometry crosses the configured inset.
status: past
created_at: 2026-06-30-13-57-36
---

# Enforce Engraving Containment

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Approved Scope

- [x] 1. Implement circle-aware engraving geometry.
  - [x] 1.1 Add a configurable engraving inset to the next shot-coin revision.
  - [x] 1.2 Replace fragmented horizontal pixel runs with a continuous-line vector font.
  - [x] 1.3 Generate glyph rows and line order correctly in the canonical Y-up coordinate system.
  - [x] 1.4 Scale the complete text block against both width and height at the circular boundary.
  - [x] 1.5 Assert every generated segment endpoint remains inside its owning coin's engraving boundary.

- [x] 2. Prevent regressions.
  - [x] 2.1 Add passing containment coverage for the shot-coin text.
  - [x] 2.2 Add a failing test for deliberately out-of-bounds engraving geometry.
  - [x] 2.3 Assert top-to-bottom line order and upright glyph orientation.
  - [x] 2.4 Preserve packing, G-code safety, deterministic build, and exact audit behavior.

- [x] 3. Validate and publish the fix.
  - [x] 3.1 Rebuild and visually inspect the preview.
  - [x] 3.2 Run the complete automated and artifact audit suite.
  - [x] 3.3 Update human documentation, roadmap state, and today's journal.
  - [x] 3.4 Archive this plan, commit the fix, and push `main`.
