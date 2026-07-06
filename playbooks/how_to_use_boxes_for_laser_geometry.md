# Playbook: Use Boxes.py for Laser Geometry

*Status: MVP*

## Objective

Use the pinned Boxes.py callable helper for fitted structural laser geometry while preserving host ownership of operations, validation, artifacts, and G-code.

## Use Boxes.py When

- The design is a box, tray, shelf, enclosure, rack, wall-storage object, fixture, gear assembly, or similar fitted panel construction.
- It requires finger joints, dovetails, living hinges, tabs, or another supported Boxes.py fabrication primitive.
- An existing Boxes.py generator substantially reduces custom geometry risk.

Do not use it for simple tokens, ordinary repeated shapes, raster engraving, machine recipes, or authoritative G-code.

## Discovery

```bash
python3 scripts/helper_tool.py check boxes
python3 scripts/helper_tool.py run boxes -- --list
python3 scripts/helper_tool.py run boxes -- RegularBox --help
```

If readiness fails, request approval before:

```bash
python3 scripts/helper_tool.py setup boxes
```

## Deterministic Generation

Direct single-generator output includes creation-time metadata and is suitable only for exploration. Authoritative builds must use Boxes.py’s YAML multi-generator path, which enables reproducible metadata:

```bash
python3 scripts/helper_tool.py run boxes -- \
  --multi-generator .tmp/boxes/<design>/generator.yml \
  .tmp/boxes/<design>/generated
```

The YAML must declare exactly one approved generator instance per expected source artifact, explicit arguments, and `format: svg` through the host invocation. Preserve the YAML as a hashed build source.

## Geometry and Process Inputs

- `thickness` is a required fabrication-geometry input and should come from the measured material batch when joints depend on fit.
- Boxes.py owns `burn` compensation for initial jointed-assembly integration because its edge winding distinguishes inner and outer compensation.
- The burn value must come from an approved calibrated material/job binding, never an unsourced design default.
- The host must not apply a second kerf offset.
- Unverified thickness or burn values make the result calibration-only.

## SVG Operation Mapping

Accept only SVG:

- Black `rgb(0,0,0)` → outer/release cut.
- Blue `rgb(0,0,255)` → inner cut.
- Green `rgb(0,255,0)` → vector engraving.
- Cyan `rgb(0,255,255)` → deep vector engraving requiring an explicit host recipe.
- Red `rgb(255,0,0)` → annotation excluded from fabrication.

Reject unknown fabrication colors, malformed geometry, unsupported transforms, missing dimensions/viewBox, or geometry outside declared stock.

## Host Integration

1. Generate reproducible source SVG under `.tmp/`.
2. Parse it into host semantic operations.
3. Normalize millimeters, coordinates, transforms, and path geometry.
4. Attach host material and machine recipes.
5. Validate bounds, operation completeness, non-overlap assumptions, and safe ordering.
6. Generate previews, manifests, and G-code through the host pipeline.
7. Record Boxes.py tool ID, pinned revision, generator, arguments/YAML hash, source SVG hash, thickness, and burn value.

Boxes.py-generated G-code, DXF conversion, LightBurn files, and sheet merging are not authoritative host artifacts until separately validated and approved.

## Verification

- `python3 scripts/helper_tool.py check boxes` reports `ready: true`.
- The submodule is clean and pinned.
- Two identical YAML invocations produce byte-identical SVG.
- SVG operations map only to declared colors.
- Inner cuts precede outer release cuts; engraving precedes cutting.
- All geometry stays inside the effective work area.
- The helper writes nothing inside `third_party/boxes`.
- Host audit passes after artifact installation.

## Failure

Do not edit upstream source, bypass pin checks, use direct time-stamped output as an authoritative input, or silently replace Boxes.py with custom geometry. Preserve prior outputs and follow `playbooks/debugging_changes_that_lead_to_errors.md`.
