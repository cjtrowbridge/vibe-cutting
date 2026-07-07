# Reference: Geometry Backend Selection

## Purpose

Help agents select the smallest appropriate geometry source before authoring or changing a laser design.

## Decision Table

| Need | Preferred backend | Reason |
|---|---|---|
| Simple circles, rectangles, rounded tokens, repeated objects, or native text | Native Python geometry | Fewest dependencies and strongest direct validation |
| Text shaping with a pinned font | OpenSCAD font adapter | Existing deterministic contour and hatch workflow |
| Geometry projected from a 3D assembly or expressed naturally with CSG | OpenSCAD geometry adapter | Parametric 3D-to-2D projection |
| Fitted panel assemblies, boxes, trays, shelves, finger joints, dovetails, living hinges, or supported structural parts | Boxes.py callable helper | Mature material-aware fabrication primitives |
| Custom engraving on helper-generated structural parts | Combined helper and native/OpenSCAD operations | Keep structural geometry and decorative operations independently validated |
| Raster engraving or image tracing | No currently accepted backend | Remains roadmap work |

## Selection Procedure

1. Describe the required geometry and semantic operations.
2. Run `setup/bootstrap.sh run -- scripts/helper_tool.py validate` when the portable bootstrap is available, then inspect helper capabilities with `scripts/helper_tool.py list`.
3. Prefer an existing native backend when it completely expresses the design.
4. Prefer a helper when its declared capability directly matches difficult fabrication geometry.
5. Use OpenSCAD when the design depends on CSG, projection, or unsupported custom parametric relationships.
6. Combine backends only at the host operation-model boundary.
7. Record the selected backend and rejected alternatives in the active plan.

For provider-based helpers, also review `references/helper-runtime-providers.md` and require at least `registered` readiness before planning setup or invocation. Do not treat a provider as fabrication-approved unless a later phase records physical process evidence.

## Non-Negotiable Boundary

Geometry sources do not own machine limits, operation ordering, material recipes, readiness claims, artifact installation, or hardware control. Every backend must converge on host-validated semantic operations before fabrication artifacts become authoritative.

## No Silent Fallback

If the selected backend is unavailable or fails validation, stop. Do not substitute a different generator, font, geometry source, or output format without updating the plan and obtaining approval.
