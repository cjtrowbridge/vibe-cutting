---
plan_id: 2026-07-10-09-42-08_improve-laser-pipeline-and-designs
title: Improve Laser Pipeline Constraints and Design Scales
summary: Update pipeline artifacts to use shared bounding boxes, add clearance asserts, and scale up all coin/badge designs to account for wide physical laser kerf.
status: past
created_at: 2026-07-10-09-42-08
---

# Improve Laser Pipeline Constraints and Design Scales

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

- [x] 1. Update pipeline for alignment and safety constraints.
  - [x] 1.1 Standardize sidecar bounding boxes in `scripts/laser_build.py`.
    - [x] 1.1.1 Modify `generate_cut_svg` and `generate_svg` to enforce the viewBox and width/height to match the machine bed size (e.g. using `machine["work_area_x"]` and `machine["work_area_y"]`).
    - [x] 1.1.2 Modify `generate_engraving_png` to pad the raw byte output with transparency so the final PNG matches the machine bed dimensions.
  - [x] 1.2 Implement clearance asserts in `scripts/laser_build.py`.
    - [x] 1.2.1 Update the base schema validation in `scripts/laser_build.py` to accept `expected_kerf_width` and `minimum_cut_clearance`.
    - [x] 1.2.2 Implement a bounding-box overlap check in the layout/segmentation logic of `scripts/laser_build.py` that raises an exception if a cut path enters the bounding box of an engraving operation plus the `minimum_cut_clearance`.

- [x] 2. Iterate on design documents for resolution and spacing.
  - [x] 2.1 Update `shot_coins` and `hug_coins` design configs.
    - [x] 2.1.1 Copy `designs/shot_coins/configs/rev_0005.json` to `rev_0006.json` and `designs/hug_coins/configs/rev_0003.json` to `rev_0004.json`.
    - [x] 2.1.2 In the new configs, increase `coin_diameter_mm` to 45.0. Since coin text auto-scales to the diameter minus the inset, this will natively increase the font size. Increase `engraving_inset_mm` slightly (e.g. to 3.0) to keep text safely away from the wide kerf edge.
    - [x] 2.1.3 In the new configs, increase `coin_gap_mm` from 1.0 to 3.0 to maintain sheet structural integrity given the thick kerf. Add `expected_kerf_width`: 3.0 and `minimum_cut_clearance`: 1.0 to configure the new asserts.
  - [x] 2.2 Update merit badge designs.
    - [x] 2.2.1 Create new revisions (e.g., `rev_0002.json` or incremented) in `designs/bwb_merit_badges/configs/`, `designs/queer_sex_party_merit_badges/configs/`, and `designs/community_garden_merit_badges/configs/`.
    - [x] 2.2.2 In the new configs, increase `token_width_mm`, `token_height_mm`, and `corner_radius_mm` proportionally.
    - [x] 2.2.3 Increase `title_font_size_mm`, `title_line_height_mm`, `body_font_size_mm`, and `body_line_height_mm` to ensure legibility.
    - [x] 2.2.4 Increase `token_gap_mm` to 3.0 and add `expected_kerf_width`: 3.0 and `minimum_cut_clearance`: 1.0.

- [x] 3. Verification.
  - [x] 3.1 Validate pipeline changes.
    - [x] 3.1.1 Build a design and verify PNG and SVG sidecars have identical physical bounding boxes.
    - [x] 3.1.2 Intentionally configure a violating clearance and verify the pipeline correctly throws an assertion error.
  - [x] 3.2 Validate design iterations.
    - [x] 3.2.1 Rebuild all updated design configurations.
    - [x] 3.2.2 Audit outputs and visually inspect previews to ensure sufficient spacing and readable text.
