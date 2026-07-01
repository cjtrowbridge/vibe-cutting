# Merit Badge Sheets

Merit-badge sheets are mixed-type sets of rounded rectangular tokens. The initial geometry uses the Falcon A1 Pro's 300 x 268 mm effective stock/machine intersection:

- Token size: 72 x 42 mm
- Corner radius: 4 mm
- Gap: 2 mm
- Grid: 4 columns x 6 rows
- Capacity: 24 tokens
- Text-safe padding: 4 mm
- Title: Liberation Sans Bold, 3.6 mm
- Description: Liberation Sans Regular, 3.0 mm
- Hatch spacing: 0.18 mm

The 72 mm width is the largest four-column token width that fits inside the configured 2 mm sheet margins. Six 42 mm rows fit the short machine axis. This gives descriptions substantially more line width than circular tokens while preserving enough copies for sets containing up to eleven initial badge types.

## Allocation

The build distributes all 24 positions evenly across badge types in declared order. For example:

- 9 types: six receive 3 copies and three receive 2.
- 6 types: every type receives 4 copies.
- 11 types: two receive 3 copies and nine receive 2.

## Create Another Set

1. Copy one existing `designs/*_merit_badges/` directory.
2. Change the ids and names in `project.json`.
3. Replace `set_name` and the `badges` list in `configs/rev_0001.json`.
4. Keep every badge id stable after publishing.
5. Run `--validate-only`, build, inspect the preview, and run `--audit-only`.

OpenSCAD-measured wrapping fails before artifact installation if a title, description, or line box cannot fit. Any later geometry or typography adjustment belongs in a new numbered revision.

Physical legibility remains calibration-only. Validate font size, hatch spacing, engraving power, speed, smoke staining, and wood grain on representative tokens before producing a complete sheet.
