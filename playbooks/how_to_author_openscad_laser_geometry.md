# Playbook: Author OpenSCAD Laser Geometry

*Status: MVP*

## Objective

Use OpenSCAD as a deterministic geometry frontend without making it responsible for machine recipes, operation ordering, safety, or hardware control.

## Prerequisites

- An active approved implementation plan.
- A recorded minimum OpenSCAD version.
- Fonts and other external geometry inputs with verified licenses and stable logical names.
- A design config that declares the OpenSCAD backend and every shaping parameter.

## Procedure

1. Keep reusable OpenSCAD sources under `openscad/`.
2. Pass design values with separate `-D` arguments; never construct a shell command.
3. Export one semantic operation or geometry role at a time.
4. Accept only the documented SVG subset and fail on unsupported path commands.
5. Normalize exported coordinates into the framework's millimeter, lower-left, Y-up contract.
6. Convert filled geometry into an explicit engraving strategy such as deterministic hatching.
7. Run bounds and owning-shape containment assertions after conversion.
8. Record the backend, font, fill strategy, and shaping values in the job manifest.
9. Stage, audit, and install artifacts through `scripts/laser_build.py`.

## Verification

- Missing OpenSCAD, missing fonts, empty geometry, malformed SVG, and unsupported commands fail before installation.
- Repeated builds with identical toolchain and inputs produce byte-identical artifacts.
- Preview, SVG, manifest, and G-code use the same converted geometry.
- No OpenSCAD source contains material recipes or hardware commands.

## Failure

Do not fall back silently to another font or geometry backend. Preserve the previous current output and follow `playbooks/debugging_changes_that_lead_to_errors.md`.
