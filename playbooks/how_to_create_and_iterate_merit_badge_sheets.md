# Playbook: Create and Iterate Merit Badge Sheets

*Status: MVP*

## Objective

Create a reusable mixed-type token sheet with a title and wrapped description on every token.

## Procedure

1. Copy an existing `designs/*_merit_badges/` directory to a new stable design id.
2. Update `project.json` identity without changing machine or material bindings unless required.
3. Start a new numbered config revision.
4. Set `set_name` and replace the `badges` list with stable ids, titles, and descriptions.
5. Keep supplied wording verbatim unless the user approves editorial changes.
6. Build with `setup/bootstrap.sh run -- scripts/laser_build.py --design <name> --validate-only`.
7. Generate a one-token inspection config under `.tmp/inspection/` for the longest title and description.
8. Inspect title weight, body size, wrapping, line separation, rounded-edge clearance, and hatch density.
9. Change token dimensions or typography only in a new config revision.
10. Build the full sheet, inspect `preview.png`, and audit the installed artifact set.

## Slot Allocation

The grid capacity is distributed evenly across badge types in declared order. Every type receives the floor of `token_quantity / type_count`; the earliest types receive one additional copy until all slots are allocated.

## Verification

- Every badge type receives at least one token.
- Wrapped title and body text fit the configured inner rectangle.
- Every engraving endpoint remains inside its owning rounded token.
- Cut paths remain in bounds and do not overlap.
- Manifest badge quantities sum to the sheet quantity.
- Repeated builds are byte-identical.

## Safety

Font size and preview legibility do not prove physical readability. Hatch spacing, power, speed, smoke staining, and wood grain remain calibration variables.
