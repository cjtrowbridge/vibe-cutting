---
plan_id: 2026-06-30-12-38-13_build-portable-laser-fabrication-framework
title: Build Portable Laser Fabrication Framework
summary: Build a machine-portable, configuration-driven framework for laser cutting, engraving, layout, calibration, and audited artifact generation.
status: future
created_at: 2026-06-30-12-38-13
---

# Build Portable Laser Fabrication Framework

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Strategy

Treat the framework as a compiler from design intent to fabrication artifacts:

1. A design defines geometry and named operations without embedding machine settings.
2. A layout places one object, repeated objects, or multi-part kits on stock.
3. A material profile supplies tested process recipes and safety restrictions.
4. A machine profile supplies physical limits and supported capabilities.
5. A job config binds one design revision, layout, material batch, and machine.
6. Preflight validates the complete combination before any fabrication artifact is accepted.
7. Export adapters produce portable design files first and machine-specific files only when that adapter has been validated.

The complete framework should eventually generate layered SVG, optional DXF, raster assets, a human-readable operation sheet, a machine-readable job manifest, and validated GRBL G-code for supported machine profiles. The MVP is the vector-only subset defined below. LaserGRBL should be the primary open reference application for previewing and streaming generated G-code to the Falcon A1 Pro. Direct USB streaming from this framework remains a post-MVP capability behind explicit safety and hardware-verification gates.

### Single Build Entrypoint

The user-facing workflow must remain as simple as `vibe-modeling`. The repository should expose one Python script:

```bash
python3 scripts/laser_build.py --design x
```

The script should resolve the design's default revision/job configuration, run the complete geometry, layout, material, machine, preflight, preview, G-code, manifest, staging, and audit pipeline, then atomically install the authoritative current artifact set at `output/x/`.

Advanced behavior should use optional flags on the same script:

```bash
python3 scripts/laser_build.py --design x --config designs/x/configs/rev_0002.json
python3 scripts/laser_build.py --design x --job basswood-3mm
python3 scripts/laser_build.py --design x --quantity 12
python3 scripts/laser_build.py --design x --new-revision
python3 scripts/laser_build.py --design x --validate-only
python3 scripts/laser_build.py --design x --audit-only
python3 scripts/laser_build.py --design x --dry-run
```

The script may import internal Python modules to keep implementation maintainable, but users must not need to install or learn a separate command suite. It generates G-code but does not emit laser light or stream to hardware.

### OpenSCAD Role

OpenSCAD should be supported as an optional parametric design frontend, but it should not be the framework's canonical job or process engine.

OpenSCAD is a good fit for:

- Parameterized 2D cut geometry.
- Designs derived from 3D assemblies using `projection()`.
- Reusing the revision/config conventions established by `vibe-modeling`.
- Exporting individual 2D SVG or DXF geometry artifacts.

OpenSCAD should not own the complete pipeline because laser fabrication also requires concerns that are not naturally represented by a single constructive-geometry result:

- Multiple semantic operation layers such as cut, score, vector engrave, raster engrave, registration, fixture, and keep-out.
- Raster image preprocessing, dithering, line interval, and scan-direction metadata.
- Material and machine recipe resolution.
- Batch layout, deterministic nesting, grain constraints, and multi-sheet jobs.
- Arbitrary-object placement using fixtures, measured datums, or calibrated cameras.
- Operation sequencing, thermal controls, air-assist settings, focus offsets, and safety assertions.
- Complete job manifests and exporter-specific metadata.

The integration boundary should therefore be:

```text
OpenSCAD design/config -> SVG or DXF operation geometry
                               |
                               v
                 framework operation/job model
                               |
                               v
          layout -> preflight -> manifests -> GRBL G-code
                                                   |
                                                   v
                                      LaserGRBL -> machine
```

An OpenSCAD-backed design may expose one entrypoint per semantic operation or part. The framework should import and validate those exported paths, attach process intent, and combine them with engraving assets and job configuration. Native SVG/Python designs and OpenSCAD-backed designs should converge on the same internal operation model.

### Callable Helper-Tool Role

Specialized third-party repositories may be registered as callable helpers when they materially reduce fabrication-geometry, conversion, layout, or testing risk. Callable helpers remain separate pinned submodules and run only as subprocesses through `scripts/helper_tool.py`; they are not imported into the host process.

Every helper must have a machine-readable `tool_adapters/<id>.json` contract declaring its capabilities, source pin, license, runtime, accepted outputs, operation mappings, and safety boundaries. Agents select helpers by capability through `references/geometry-backend-selection.md` and tool-specific playbooks.

Helper output is untrusted source material. It must converge on the same host operation model as native and OpenSCAD geometry before layout, recipes, preflight, previews, manifests, G-code, or readiness claims are accepted.

Boxes.py is the first callable helper. Use it for supported fitted panel assemblies, boxes, trays, shelves, finger joints, dovetails, living hinges, gears, and related structural geometry. Accept SVG only; never treat Boxes.py-generated G-code as authoritative host output.

### Implemented Vector Foundation

The 2026-06-30 bounded implementation plan delivered a dependency-free native vector foundation before the broader MVP:

- `scripts/laser_build.py` resolves committed design, machine, and material JSON.
- Current outputs and immutable numbered revisions use staged exact-artifact audits.
- SVG, PNG preview, GRBL G-code, manifests, operation data, and setup guidance are generated from one command.
- The first `shot_coins` design produces 81 nominal 30 mm coins inside the configured 300 x 268 mm effective area.
- Focused tests cover packing, bounds, minimum spacing, SVG coordinates, G-code state, operation order, and exact artifact manifests.
- Shot-coin revision `rev_0003` uses upright continuous-line vector glyphs, circle-aware text scaling, and fail-closed engraving containment assertions.
- The `hug_coins` variant proves a second design can reuse the same machine, material, layout, containment, preview, G-code, manifest, and audit pipeline.
- Default coin revisions now use an OpenSCAD 2021.01+ adapter with pinned SIL OFL 1.1 Liberation Sans Regular files, linear SVG parsing, Y-axis normalization, deterministic hatch fill, and font provenance in manifests; prior Bold revisions remain reproducible.
- Reusable `merit_badge_set` configs now generate 24 mixed-type 72 x 42 mm rounded tokens with measured title/body wrapping, even type allocation, rounded-shape containment, and complete per-type manifest counts.
- All current machine and material settings remain provisional or calibration-only.

OpenSCAD was not installed in the implementation environment, so the native vector backend established the pipeline without making an external tool a blocker. The OpenSCAD adapter remains planned work and must converge on this operation and artifact model.

## Design Principles

- Keep geometry independent from laser brand, module, material, and process recipe.
- Use millimeters as the canonical unit and an explicit coordinate-system contract.
- Represent cuts, scores, vector engraving, raster engraving, registration, fixtures, keep-outs, and construction geometry as distinct operation classes.
- Treat material settings as empirical recipes with calibration provenance, not universal truths.
- Separate requested effect from execution recipe: for example, `through_cut`, `surface_mark`, or `target_depth_mm` resolves to speed, power, passes, focus offset, air assist, and dwell only through a tested material profile.
- Require schema validation for every configuration and manifest.
- Preserve immutable numbered design revisions and reproducible build manifests.
- Stage and audit complete artifact sets before replacing current outputs.
- Never describe an uncalibrated material/depth combination as fabrication-ready.
- Keep machine communication outside the geometry core.
- Treat LaserGRBL as the preferred open controller/streamer, not as the canonical design compiler.
- Generate G-code before the LaserGRBL handoff because LaserGRBL's SVG support does not preserve separate cut/engrave behavior by layer or color.
- Keep the generated G-code portable enough to load in another compatible GRBL sender when LaserGRBL is unavailable.
- Assign every third-party repository an explicit role: reference-only, callable helper, runtime library, or operator application.
- Do not copy, import, link, vendor, or create runtime dependencies on code from either reference submodule.
- Invoke callable helpers only through pinned subprocess adapters and treat their outputs as untrusted interchange artifacts.
- Prefer independently specified behavior, clean-room implementation, and golden compatibility fixtures derived from public formats and observed outputs.

## Pre-Execution Decision Gates

Implementation must not begin until each blocking decision is recorded in an architecture decision record and reflected in affected schemas, playbooks, and documentation.

### Project license and third-party boundary

- The root `LICENSE` declares Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International for host-authored repository material.
- `third_party/vibe-modeling` and `third_party/lasergrbl` are external read-only reference repositories, not implementation source or runtime dependencies.
- `third_party/boxes` is a separately licensed callable helper invoked in a subprocess; it is not imported or relicensed as host source.
- Their contents remain governed by their own upstream licenses and are not relicensed by the host `LICENSE`.
- Use a clean-room implementation that studies documented behavior, public formats, and independently generated compatibility outputs without copying source.
- Do not import, link, vendor, translate, adapt, or copy code from either submodule into host implementation.
- Record attribution and license obligations for every separately added Python dependency, font, fixture, and sample asset.
- Block any proposed dependency or copied asset whose license is incompatible with the host license or intended use.

### Python and dependency policy

- Select and document the minimum supported Python version; recommended starting baseline is Python 3.11.
- Keep `scripts/laser_build.py` cross-platform across Windows, Linux, and macOS even though LaserGRBL itself is Windows-native.
- Prefer the Python standard library for orchestration, JSON, XML, hashing, subprocesses, paths, and manifests.
- Add third-party dependencies only when they materially reduce geometry, SVG, schema, raster, or testing risk.
- Prefer subprocess-only callable helpers with isolated `.tmp` environments when a separately maintained tool can produce a validated interchange artifact.
- Pin every runtime and development dependency with its license and supported platform matrix.
- Decide whether the project uses a virtual environment plus requirements/lock files or another reproducible dependency mechanism.
- Block implementation of geometry normalization until the chosen SVG/geometry approach passes a focused compatibility spike.

### Canonical source and configuration decisions

- Use JSON as the canonical machine, material, design, part, fixture, job, and manifest format.
- Use versioned JSON Schemas for validation.
- Use the dependency-free native vector backend as the initial pipeline proof.
- Add OpenSCAD as an optional parametric design backend after its SVG operation adapter passes compatibility tests.
- Define how `--design <name>` resolves the default committed design revision and default job binding without guessing.
- Define one revision identity that pins effective design, machine, material, module, recipe, layout, fixture, and exporter inputs.

### Hardware and safety readiness

- Identify the physical Falcon A1 Pro, firmware version, installed laser module, available materials, ventilation, fire response equipment, and responsible operator.
- Capture live GRBL configuration without modifying it.
- Treat manufacturer settings as unverified seeds until local calibration.
- Block emitting tests until non-emitting travel, framing, bounds, interlock, exhaust, focus, and emergency-stop checks pass.
- If hardware is unavailable, allow software milestones to reach `test-ready` but not `fabrication-ready`.

## Local Third-Party Repositories

### `third_party/vibe-modeling`

Use the OpenSCAD framework as the reference for:

- Parameterized design folders and numbered configuration revisions.
- Single-part and manifest-driven complete builds.
- Managed scratch, staging, current-output, and immutable-revision destinations.
- Exact artifact-set validation.
- Source, config, manifest, Git, and artifact provenance hashes.
- Atomic installation and audit-only verification.

Do not inherit its gaps:

- Flat, unversioned design config schemas.
- Inconsistent use of authoritative part manifests.
- Limited automated tests.
- Generated-artifact tracking that conflicts with documented ignore policy.
- Documentation examples that do not always match current repository contents.

### `third_party/lasergrbl`

Pinned reference revision for this plan audit: `1f9337b3af27133f8b1696e41cc110f2af74d04f`.

Use LaserGRBL as behavioral and compatibility reference for:

- G-code loading, parsing, bounds, timing, and preview: `LaserGRBL/GrblFile.cs`.
- GRBL command parsing and modal state: `LaserGRBL/GrblCommand.cs` and `LaserGRBL/StateBuilder.cs`.
- Command queueing, buffering, acknowledgements, alarms, reset, hold, resume, jogging, configuration, and streaming: `LaserGRBL/Core/GrblCore.cs`.
- Communication abstraction boundaries: `LaserGRBL/ComWrapper/IComWrapper.cs` and concrete serial/WebSocket wrappers.
- SVG units, transforms, paths, curves, arcs, and conversion behavior: `LaserGRBL/SvgConverter/GCodeFromSVG.cs`.
- G-code motion, laser on/off, power, feed, arc, compression, and decimal formatting behavior: `LaserGRBL/SvgConverter/gcodeRelated.cs`.
- Raster preprocessing, grayscale, thresholding, dithering, scan direction, sizing, offset, and power range: `LaserGRBL/RasterConverter/ImageProcessor.cs`.
- Power-versus-speed and cutting-test generators: `LaserGRBL/Generator/PowerVsSpeedForm.cs` and `LaserGRBL/Generator/CuttingTest.cs`.
- GRBL protocol simulation: `LaserGRBL/GrblEmulator/Grblv11Emulator.cs`.
- Existing compatibility-test style and current test-coverage gaps: `LaserGRBL.Tests/`.

Constraints on using this reference:

- LaserGRBL is a Windows GUI and must not become a runtime dependency of the cross-platform core.
- LaserGRBL's direct SVG support is experimental and does not preserve distinct cut/engrave semantics by layer or color.
- LaserGRBL has minimal Z-axis control, while the Falcon A1 Pro has autofocus/Z behavior that requires a dedicated machine profile.
- LaserGRBL is GPLv3. Study documented interfaces and independently generated outputs only; do not copy or adapt its implementation.
- Neither reference submodule may be imported by host Python code, invoked as a required build dependency, packaged into releases, or treated as host-owned source.
- Compatibility tests should compare generated G-code behavior, bounds, state transitions, and preview expectations rather than importing LaserGRBL internals.

### `third_party/boxes`

Pinned callable-helper revision: `836f5f72bedb33ac4262ed925545eacb31e926a8`.

Use Boxes.py through `scripts/helper_tool.py` for:

- Parametric boxes, trays, shelves, enclosures, racks, and wall-storage structures.
- Finger joints, dovetails, living hinges, tabs, gears, and supported fabrication parts.
- Material-thickness-aware geometry and Boxes.py edge-aware burn compensation.
- Reproducible SVG generation through its YAML multi-generator mode.

Constraints:

- Keep Boxes.py as a separate GPL-3.0-or-later submodule and subprocess tool.
- Never import it into the host Python process, modify its source, or copy its implementation.
- Accept SVG source geometry only until other formats receive separate compatibility validation.
- Map declared operation colors into host semantic operations and reject unknown fabrication colors.
- Keep machine recipes, bounds, ordering, artifacts, G-code, readiness, and hardware control in the host pipeline.
- Record tool ID, revision, invocation/config hash, source SVG hash, measured thickness, and burn value in provenance.
- Use only calibrated burn values and never apply kerf compensation twice.

## Proposed Repository Structure

```text
src/vibe_cutting/
  geometry/
  operations/
  layout/
  preflight/
  exporters/
  manifests/
scripts/
  helper_tool.py
  laser_build.py
tool_adapters/
  boxes.json
schemas/
  helper_tool.schema.json
machines/
  creality/falcon_a1_pro.json
materials/
  wood/
  acrylic/
  paper/
  leather/
  metal/
designs/<design>/
  src/
  configs/rev_000N.json
  parts.json
jobs/<job>/rev_000N.json
calibration/
  machines/<machine-id>/
  materials/<material-id>/
fixtures/
output/<design>/
revisions/<design>/rev_000N/
.tmp/laser/<design>/
tests/
docs/
playbooks/
references/
templates/
third_party/
  boxes/
  vibe-modeling/
  lasergrbl/
```

## Canonical Data Model

### Machine Profile

The first profile, `machines/creality/falcon_a1_pro.json`, should distinguish manufacturer-reported values from locally verified values and include source URLs, source dates, firmware assumptions, and verification status.

Initial reported constraints to encode and verify:

- Nominal work area: `268 x 358 mm`; verify X/Y orientation and conservative usable margins on the physical machine.
- Maximum motion speed: `600 mm/s`.
- Product operating temperature: `5-35 C`; keep recipe-specific preferred ranges separate.
- Autofocus measurement accuracy: reported as less than `0.3 mm`.
- Supported focus/surface range: reported hard limits of `7-30 mm`; verify exact coordinate meaning on-device.
- Factory camera calibration height: `7 mm`; camera alignment should be refreshed when material height changes significantly.
- 20 W blue module: `455 +/- 5 nm`, reported spot approximately `0.08 x 0.10 mm`.
- 2 W IR module: `1064 +/- 1 nm`, reported spot approximately `0.03 x 0.03 mm`.
- Supported interchange formats: SVG, DXF, JPEG, PNG, BMP, and related formats.
- Supported host workflows: Falcon Design Space, LightBurn, and LaserGRBL.
- Primary open host workflow: generated `.gcode` or `.nc` loaded, previewed, and streamed with LaserGRBL.
- LaserGRBL is Windows-native; the framework itself and its generated GRBL artifacts must remain cross-platform.
- LaserGRBL SVG import is experimental and does not support separate cut/engrave behavior by SVG layer or color, so it must not be the primary multi-operation interchange boundary.
- Camera support is software-adapter-specific; current official guidance says LightBurn does not support the A1 Pro camera workflow.
- Lid interlock, emergency stop, flame detection, air assist, exhaust, focus behavior, and module-specific thermal alarms.
- Power-loss behavior: the interrupted job does not automatically resume.
- Optional rotary capability and any future conveyor/extended-work-area capability must be separate accessories/capability flags.

Manufacturer one-pass cutting claims such as `10 mm basswood`, `8 mm black acrylic`, and `0.04 mm stainless sheet` must be stored as sourced advisory claims, not hard acceptance limits. Fabrication readiness must depend on local material calibration.

### Material Profile

Each material profile should include:

- Stable material ID, category, composition, color, finish, supplier, batch/lot, and measured thickness.
- Safety classification: allowed, conditional, or prohibited.
- Compatible laser modules and unsupported wavelengths.
- Kerf measurements by module, thickness, speed, power, passes, focus, and air-assist setting.
- Cut recipes by thickness and desired result.
- Engraving recipes by desired effect or calibrated depth.
- Raster line interval, overscan, scan angle, dithering mode, and image preprocessing.
- Air-assist, exhaust, masking, surface preparation, cooldown, and cleanup requirements.
- Test coupon and measurement provenance.
- Confidence level, date, operator, machine profile revision, firmware, lens condition, and environmental notes.
- Maximum verified thickness/depth; values beyond it require calibration mode.

Profiles must prohibit or hard-fail unknown chlorine-containing, highly reflective, explosive, or otherwise unsafe materials unless an explicitly reviewed policy says otherwise. The safe default for unknown composition is refusal, not a guessed recipe.

### Design and Part Manifest

Each design should define:

- Parameterized geometry with named dimensions.
- One or more parts in an authoritative `parts.json`.
- Operation geometry grouped by semantic operation, not display color alone.
- Minimum feature size, minimum ligament, minimum hole/slot size, and kerf-compensation intent.
- Optional engraving artwork, text, raster assets, and font provenance.
- Allowed rotations, grain direction, face/orientation, and mirroring rules.
- Quantity-independent geometry; repetition belongs to layout/job configuration.

### Job Configuration

A job binds:

- Design revision and selected parts.
- Quantity or set count.
- Machine profile revision.
- Laser module.
- Material profile and measured stock dimensions/thickness.
- Layout mode, margins, spacing, rotation, grain constraints, and keep-outs.
- Fixture, origin, registration strategy, and camera/manual placement mode.
- Desired operation effects and resolved process recipes.
- Export adapter and expected artifacts.

## Required Preflight Assertions

- All config files pass their JSON Schemas.
- Every referenced revision, part, machine, material, recipe, and fixture exists.
- Geometry bounds fit within the conservative usable machine area.
- Stock bounds, fixture keep-outs, clamp zones, and head-clearance zones are respected.
- Requested speed, power, pass count, focus position, raster interval, and module are within machine and recipe limits.
- The selected module supports the requested material and operation.
- Unknown or prohibited materials fail closed.
- Material surface height is within the machine focus range.
- Camera-dependent placement requires a valid calibration for the relevant material-height range.
- Cut geometry is closed, non-self-intersecting, and free of unintended duplicates.
- Minimum features survive kerf compensation.
- Slots and mating joints use the selected material's measured kerf, not a global constant.
- Engraving occurs before perimeter release cuts unless explicitly overridden.
- Interior cuts occur before exterior contours.
- Multi-pass jobs include thermal/cooldown and re-registration requirements where applicable.
- Raster resolution is compatible with spot size and tested line interval.
- Repeated objects and sets have adequate spacing and remain complete after nesting.
- Arbitrary-object engraving requires a declared datum strategy: fixture, registration marks, measured coordinates, or a supported calibrated camera workflow.
- Machine-specific output cannot be labeled ready until its exporter has passed a hardware acceptance suite.

## Canonical Build Artifacts

A complete build should stage, validate, hash, and atomically install:

- `design.svg`: canonical layered vector geometry.
- `design.dxf`: optional vector interchange artifact.
- Raster source/output files when raster engraving is present.
- `preview.svg` and/or `preview.png`: stock, work area, fixtures, keep-outs, operation order, and bounds.
- `job_manifest.json`: all pinned inputs, resolved recipes, operation order, dimensions, and provenance.
- `operations.csv`: operator-readable layer, module, speed, power, passes, air-assist, focus, and notes.
- `material_setup.md`: preparation, fixture, focus, ventilation, safety, and cleanup checklist.
- Optional exporter artifacts such as LightBurn-compatible layered SVG or validated GRBL/G-code.
- `job.gcode`: validated machine-executable artifact for a supported GRBL machine profile.
- `build_manifest.json`: hashes, Git state, schema versions, config sources, artifact inventory, and readiness status.

Generated artifacts should be ignored by Git by default. Small, intentional golden fixtures may be committed only under test-fixture paths.

## MVP Boundary

The first release must prove the architecture without attempting every planned fabrication mode.

### Included in the MVP

- One repository-local entrypoint: `python3 scripts/laser_build.py --design <name>`.
- Native vector designs and an optional OpenSCAD adapter exporting separate cut, score, and vector-engrave geometry into the same operation model.
- One canonical operation model and deterministic operation ordering.
- One machine profile: Creality Falcon A1 Pro with the 20 W blue module.
- One locally calibrated starter material/thickness, recommended `3 mm` basswood.
- Single-object and rectangular-array quantity layouts.
- Vector engraving, interior cuts, exterior cuts, and optional score lines.
- JSON configs and schemas for design, parts, job, machine, material, and manifests.
- Bounds, focus, module, material, recipe, topology, kerf, ordering, and safety preflight.
- Layered SVG, preview PNG, operation sheet, setup checklist, GRBL G-code, and build manifest.
- Replaceable `output/<design>/` builds and immutable `revisions/<design>/rev_000N/` snapshots.
- LaserGRBL G-code loading, preview, bounds comparison, and supervised streaming documentation.
- Dry-run, validate-only, audit-only, and new-revision modes.

### Explicitly deferred beyond the MVP

- Raster/photo engraving and dithering.
- Arbitrary-object camera placement.
- Rotary engraving.
- Automatic irregular nesting.
- Multi-sheet spillover and complete-set optimization.
- Multi-module jobs requiring a blue/IR module swap.
- Calibrated depth/relief engraving.
- Conveyor or tiled long-stock processing.
- Direct framework-to-machine streaming.
- A second machine profile.
- LightBurn and Falcon Design Space project exporters.
- Cost estimation, remnants inventory, maintenance tracking, and production analytics.

Deferred work remains in this umbrella roadmap but must not block the MVP release.

## MVP Acceptance Criteria

The MVP is complete only when all applicable criteria pass:

- `python3 scripts/laser_build.py --design example_tag --dry-run` resolves every input and prints deterministic planned artifacts without writing current outputs.
- A normal `example_tag` build creates exactly the declared artifact set under `output/example_tag/`.
- `example_tag` contains at least one exterior cut, one interior cut, one vector engraving, and one optional score operation.
- A quantity build creates a deterministic rectangular array without overlap and remains inside the conservative usable work area.
- `--new-revision` creates matching committed config and immutable artifact revision paths and refuses overwrite.
- `--audit-only` verifies exact files, hashes, pinned inputs, and readiness without rebuilding.
- Repeating a build with identical inputs produces identical deterministic artifacts except explicitly declared timestamps.
- Out-of-bounds geometry, unknown materials, incompatible modules, unsupported commands, unsafe laser-on travel, and missing recipes fail before output installation.
- Parsed generated G-code bounds and operation order match the canonical job manifest and preview.
- LaserGRBL loads the generated G-code without parse errors and shows matching bounds and operation order.
- Non-emitting machine framing stays inside stock and conservative machine limits.
- A supervised calibration coupon and `example_tag` test on the Falcon A1 Pro match declared dimensional and process tolerances before the profile is marked fabrication-ready.
- Human README instructions and agent playbooks reproduce the same successful workflow from a clean clone.

## Milestone Plan Decomposition

This file is an umbrella roadmap and must not be promoted wholesale to `plans/current/`. Before implementation, create a separate bounded plan for each milestone and request approval for that milestone only.

1. **Milestone 0 — Decisions and governance**
   - Record the selected CC BY-NC-SA 4.0 host license and read-only submodule boundary; select the Python baseline, dependency mechanism, SVG/geometry approach, config resolution, and hardware owner.
   - Create the minimum governing playbooks, ADRs, safety docs, schemas, and templates required for Milestone 1.
2. **Milestone 1 — Build and revision skeleton**
   - Implement `scripts/laser_build.py`, design discovery, config resolution, managed staging, `output/<design>/`, immutable revisions, exact artifact manifests, hashes, dry-run, validate-only, and audit-only.
   - Use placeholder deterministic text/JSON artifacts before geometry or G-code.
3. **Milestone 2 — OpenSCAD operation export**
   - Implement per-operation OpenSCAD builds, SVG normalization, operation import, topology/bounds checks, and preview generation.
   - Deliver `example_tag` geometry with cut, score, and vector engraving.
4. **Milestone 3 — Machine, material, and preflight**
   - Implement Falcon A1 Pro and basswood profiles, schema validation, kerf/focus/recipe resolution, prohibited-material rejection, and conservative bounds checks.
   - Generate calibration coupons without streaming.
5. **Milestone 4 — GRBL vector artifact generation**
   - Implement deterministic vector G-code, modal-state parsing, safe header/footer, laser-off travel, operation ordering, bounds simulation, and LaserGRBL compatibility fixtures.
6. **Milestone 5 — Quantity layout and complete MVP build**
   - Implement rectangular arrays, quantity validation, final operation sheets, setup checklists, complete artifact auditing, and documentation walkthroughs.
7. **Milestone 6 — Hardware acceptance**
   - Execute non-emitting tests, calibration coupons, supervised `example_tag`, dimensional checks, alarm/abort exercises, and readiness decisions.
8. **Milestone 7+ — Deferred capabilities**
   - Create separate future plans for raster, arbitrary-object fixtures, nesting, multi-sheet sets, IR module support, rotary, direct streaming, and additional machines.

Every milestone plan must list exact files, tests, documentation updates, expected artifacts, rollback path, and acceptance evidence.

## Risk Register and Stop Conditions

- **Third-party contamination risk:** stop if implementation copies, imports, links, vendors, or adapts source from either read-only reference submodule.
- **Coordinate mismatch risk:** stop emitting tests if design, SVG, G-code, LaserGRBL, and physical-machine origins or axis directions disagree.
- **Unsafe modal-state risk:** reject any G-code whose laser state, units, positioning mode, feed, or power cannot be proven at every motion.
- **SVG variability risk:** restrict the accepted SVG subset and stop broadening it until golden fixtures cover transforms, curves, units, text outlines, and winding.
- **Unverified machine-limit risk:** use conservative reported limits for software testing and block fabrication-ready status until physical verification.
- **Material variability risk:** do not interpolate or generalize recipes across composition, supplier, batch, color, finish, or thickness without evidence.
- **Artifact drift risk:** stop installation when expected files, hashes, source inputs, or schema versions differ from the manifest.
- **Scope-expansion risk:** move any deferred feature into a separate approved plan rather than enlarging the active MVP milestone.
- **Hardware-availability risk:** continue non-emitting software work but stop at `test-ready` when physical acceptance cannot be performed.
- **Platform risk:** keep the build script cross-platform; treat LaserGRBL preview/streaming as a Windows acceptance step rather than a Python runtime dependency.

## Required Playbooks

Each playbook must contain: status, objective, scope, prerequisites, required inputs, safety boundaries, atomic procedure, expected artifacts, verification gates, failure/rollback behavior, lifecycle compliance, and related playbooks/references. `AGENTS.md` must index every playbook and state when it is mandatory.

### `playbooks/how_to_add_a_new_laser_design.md`

Required content:

- Select native SVG/Python or OpenSCAD-backed authoring mode.
- Create the design folder, source entrypoints, revision config, `parts.json`, and design README.
- Declare parameters, units, coordinate origin, allowed rotations, grain constraints, minimum features, and operation outputs.
- Assign stable part and operation IDs.
- Generate initial geometry without machine/material settings embedded in design code.
- Validate topology, bounds, operation completeness, and deterministic output.
- Build one single-part and one complete-manifest dry run.
- Record expected source/config/artifact provenance.
- Fail if any operation is unlabeled, any part is missing, or generated files escape managed destinations.

### `playbooks/how_to_author_openscad_laser_geometry.md`

Required content:

- Define one command-line-selectable entrypoint per part and semantic operation.
- Pass revision parameters through deterministic OpenSCAD `-D` values.
- Export 2D-only SVG/DXF geometry with explicit millimeter assumptions.
- Use `projection()` only with documented projection plane and cut semantics.
- Convert text to geometry or pin fonts and verify outlines.
- Prohibit process settings, material recipes, and machine limits inside SCAD geometry.
- Normalize and inspect exported bounds, transforms, winding, closure, and curve approximation.
- Compare OpenSCAD exports against committed golden fixtures.
- Fail on empty exports, non-2D results, unit ambiguity, unsupported elements, or nondeterministic geometry.

### `playbooks/how_to_create_and_validate_a_machine_profile.md`

Required content:

- Gather manufacturer claims, official control files, live GRBL configuration, firmware identity, and physical measurements.
- Separate reported, measured, inferred, and unverified values.
- Define work area, origin, axes, travel, speed, acceleration, power scale, modules, focus range, accessories, interlocks, and dialect capabilities.
- Record source URLs, retrieval dates, profile revision, and verification evidence.
- Verify bounds using non-emitting moves and frame-only tests.
- Verify power mapping only with controlled test material and supervision.
- Add conservative margins and keep-outs.
- Run schema, static preflight, emulator, and hardware acceptance tests.
- Fail closed for missing safety-critical limits or mismatched live configuration.

### `playbooks/how_to_calibrate_a_material_and_promote_recipes.md`

Required content:

- Identify composition, supplier, batch, color, finish, measured thickness, and safety classification.
- Reject unknown, chlorinated, explosive, or highly reflective materials by default.
- Select compatible module and machine profile.
- Generate power-speed-pass, kerf, slot-fit, hole-size, focus, raster-interval, and depth coupons as applicable.
- Record environment, firmware, lens condition, air assist, exhaust, focus, and measurement tools.
- Measure and attach results without overwriting raw observations.
- Promote only passing cells into recipes with confidence and verified ranges.
- Create a new profile revision when evidence changes.
- Fail if provenance, supervision, ventilation, or measurement evidence is incomplete.

### `playbooks/how_to_build_and_audit_a_laser_job.md`

Required content:

- Select design revision, parts, quantities, material batch, machine profile, module, fixture, layout, and desired effects.
- Resolve effects into verified recipes.
- Run schema, topology, kerf, bounds, keep-out, focus, capability, ordering, and safety preflight.
- Stage all artifacts under `.tmp/laser/<design>/<build-id>/`.
- Generate canonical geometry, preview, operation sheet, setup checklist, G-code, and build manifest.
- Validate exact artifact names, counts, sizes, and hashes.
- Atomically replace current output or create an immutable revision.
- Run audit-only verification after installation.
- Fail without installing partial outputs.

### `playbooks/how_to_generate_and_validate_grbl_gcode.md`

Required content:

- Pin GRBL dialect/profile, coordinate mode, unit mode, origin, power scale, laser mode, feed limits, arc support, decimal precision, and accessory commands.
- Convert semantic operations into deterministic ordered toolpaths.
- Emit explicit safe header and footer with laser-off guarantees.
- Keep rapid moves laser-off and prevent accidental modal power carryover.
- Apply interior-before-exterior and engraving-before-release ordering.
- Handle arcs according to profile capability or flatten within declared tolerance.
- Validate bounds from parsed generated G-code, not only source geometry.
- Simulate modal state, laser state, feed, power, and end position.
- Compare against golden vectors and LaserGRBL preview expectations.
- Fail on unsupported commands, out-of-bounds motion, unsafe laser state, ambiguous units, or unverified dialect behavior.

### `playbooks/how_to_preview_and_stream_with_lasergrbl.md`

Required content:

- Confirm Windows/LaserGRBL version, machine connection, correct COM port, firmware identity, and imported GRBL configuration.
- Load framework-generated `.gcode` or `.nc`, never rely on LaserGRBL SVG layers for multi-operation jobs.
- Compare LaserGRBL bounds, estimated duration, path preview, and operation order with the build manifest.
- Verify origin, frame bounds, module, focus, stock, fixture, air assist, exhaust, enclosure, and emergency stop.
- Require supervised start and define hold, resume, abort, reset, alarm, and disconnect responses.
- Prohibit changing power/speed overrides unless the deviation is recorded as a new run result.
- Capture run outcome and machine alarms in a fabrication-run report.
- Fail before emission if preview or live configuration differs from the manifest.

### `playbooks/how_to_create_single_batch_set_and_nested_layouts.md`

Required content:

- Select single-object, rectangular-array, complete-set, deterministic-nesting, or multi-sheet mode.
- Define stock, margins, spacing, allowed rotations, grain direction, keep-outs, and quantity.
- Preserve set completeness and stable instance IDs.
- Apply layout transforms only after part geometry validation.
- Verify no overlaps after kerf expansion and no instances exceed usable area.
- Produce per-sheet manifests, previews, labels, and quantity totals.
- Record nesting algorithm/version and deterministic seed.
- Fail on missing set members, unstable layout, or stock overcommit.

### `playbooks/how_to_create_mixed_cut_score_and_engrave_jobs.md`

Required content:

- Inventory every semantic operation and required laser module.
- Decide whether a module swap or multiple machine runs are required.
- Define engraving, score, interior-cut, exterior-cut, and release ordering.
- Resolve each operation to a verified material recipe.
- Add registration and cooldown requirements between stages.
- Generate stage-specific previews and one combined job manifest.
- Verify stage alignment and prohibit moving stock between dependent stages unless a fixture/registration contract exists.
- Fail if operations have incompatible modules, recipes, or ordering constraints.

### `playbooks/how_to_engrave_arbitrary_objects_with_fixtures.md`

Required content:

- Capture object dimensions, engravable surface, curvature, finish, reflectivity, composition, and allowable heat.
- Choose fixture datum, registration marks, measured absolute coordinates, or a calibrated camera adapter.
- Define fixture geometry and machine keep-outs.
- Validate focus range and collision clearance over the full object.
- Run a low-power frame or non-emitting boundary check.
- Use a sacrificial/test object when recipe or registration is unverified.
- Record placement repeatability and final offset corrections.
- Fail for unknown composition, excessive curvature, reflective risk, focus-range violation, or unverified datum.

### `playbooks/how_to_run_laser_hardware_acceptance_tests.md`

Required content:

- Verify machine identity, firmware, profile revision, module, interlocks, emergency stop, exhaust, air assist, and fire response equipment.
- Run non-emitting homing, origin, travel, frame, and soft-limit tests.
- Run minimum-power mark tests before cutting tests.
- Verify power scale, feed scale, coordinate orientation, arcs/line flattening, pass behavior, hold/resume, abort, reset, and alarm recovery.
- Compare physical dimensions and placement against expected tolerances.
- Record every result in a versioned acceptance report.
- Gate exporter readiness by exact machine-profile revision and firmware.
- Fail closed and preserve evidence on any safety or dimensional discrepancy.

### `playbooks/how_to_handle_interrupted_failed_or_unsafe_jobs.md`

Required content:

- Stop emission and motion using the safest available control.
- Distinguish hold, abort, alarm, disconnect, power loss, fire, material shift, incomplete cut, and software failure.
- Preserve G-code, manifests, logs, machine state, photos, and stock position when safe.
- Prohibit blind resume after power loss or lost position.
- Decide whether registered restart, stage restart, salvage, or discard is safe.
- Create a new job revision for changed parameters or geometry.
- Record incident cause, response, and preventive action.
- Route software defects through the debugging playbook and hardware hazards through operator safety procedures.

### `playbooks/how_to_add_or_modify_a_grbl_dialect_adapter.md`

Required content:

- Define adapter ownership and supported firmware/machine profiles.
- Document commands, modal assumptions, power mapping, units, coordinates, arcs, accessories, status, alarms, and buffering.
- Add parser/generator/emulator fixtures before implementation.
- Add safe header/footer and unsupported-command rejection.
- Test deterministic generation, round-trip parsing, bounds, modal state, and failure cases.
- Run hardware acceptance before marking the adapter fabrication-ready.
- Update compatibility tables and migration notes.
- Never broaden device support based only on syntactic G-code acceptance.

### `playbooks/how_to_update_reference_submodules_and_review_compatibility.md`

Required content:

- Record old and proposed submodule revisions.
- Review upstream changelogs and diffs relevant to observed behavior.
- Re-run source-map checks and identify moved/renamed reference files.
- Re-run golden compatibility fixtures and emulator/preview comparisons.
- Review licensing changes before borrowing or adapting behavior.
- Update local references, compatibility notes, and affected plans.
- Require user approval before changing compatibility claims or copied/synthesized material.
- Preserve rollback pointers for every updated submodule.

### `playbooks/how_to_add_and_validate_a_helper_tool.md`

Required content:

- Classify the tool and define narrow capabilities, routing, output, safety, and license contracts.
- Add a pinned submodule and schema-valid adapter manifest.
- Install dependencies only into an isolated disposable environment.
- Invoke only through the generic subprocess runner.
- Test pin matching, path confinement, readiness, determinism, output parsing, and failure behavior.
- Update agent routing, human documentation, and rollback guidance.

### `playbooks/how_to_use_boxes_for_laser_geometry.md`

Required content:

- Select Boxes.py only for supported fitted structures and fabrication primitives.
- Discover generators and arguments through the generic helper runner.
- Use YAML multi-generator mode for reproducible source SVG.
- Define thickness, burn ownership, and double-kerf prevention.
- Map SVG colors into host operations and reject unknown semantics.
- Preserve host ownership of recipes, validation, G-code, artifacts, and readiness.
- Record complete helper provenance.

### `playbooks/how_to_review_laser_job_safety_and_fabrication_readiness.md`

Required content:

- Review material identity and hazards.
- Review machine/module/profile compatibility.
- Review geometry, kerf, bounds, focus, fixtures, ordering, thermal concentration, and loose-part risks.
- Review generated G-code modal state, laser-off travel, power/feed limits, and final shutdown.
- Review operator setup, supervision, ventilation, fire response, and protective equipment.
- Assign readiness as blocked, calibration-only, test-ready, or fabrication-ready.
- Cite exact design/job/material/machine revisions and evidence.
- Prohibit readiness claims when any mandatory gate is unverified.

## Required Documentation

Human-facing documentation must explain concepts and workflows without embedding agent policy. Agent execution rules, mandatory playbook selection, plan governance, and completion-report requirements belong in `AGENTS.md`.

### Root and architecture documentation

- `README.md`
  - Explain the project purpose, supported workflows, prerequisites, quick start, output artifacts, safety warning, and links to deeper documentation.
  - Include one minimal design-to-LaserGRBL walkthrough after the MVP exists.
  - Do not duplicate agent-only process policy.
- `AGENTS.md`
  - Index every project-specific playbook and reference.
  - Map task types to mandatory playbooks.
  - Define documentation synchronization rules, generated-artifact policy, safety-stop authority, required verification summaries, and third-party licensing boundaries.
- `docs/architecture.md`
  - Define the compiler pipeline, module boundaries, dependency direction, extension points, callable-helper boundary, and reasons OpenSCAD/LaserGRBL/helper tools are adapters rather than the core.
- `docs/helper-tools.md`
  - Define helper classes, adapter manifests, setup, invocation, trust boundaries, provenance, updates, and failure behavior.
- `docs/repository-structure.md`
  - Define ownership and lifecycle of every top-level directory and generated destination.
- `docs/coordinate-systems-and-units.md`
  - Define millimeters, design coordinates, stock coordinates, machine coordinates, origin conventions, transforms, axis direction, rounding, and tolerance.
- `docs/operation-model.md`
  - Define every operation type, required fields, ordering rules, module compatibility, and conversion to toolpaths.
- `docs/artifact-lifecycle-and-provenance.md`
  - Define staging, current output, immutable revisions, manifests, hashes, audit-only verification, cleanup, and rollback.

### Configuration and schema documentation

- `docs/configuration-model.md`
  - Explain schema versioning, references, IDs, revisions, overrides, validation, and migration.
- `docs/machine-profiles.md`
  - Define reported/measured/inferred values, capabilities, conservative limits, accessories, firmware binding, and readiness.
- `docs/machines/creality-falcon-a1-pro.md`
  - Record sourced specifications, locally verified dimensions, modules, focus behavior, interlocks, GRBL settings, software compatibility, known limitations, and acceptance status.
- `docs/material-profiles-and-recipes.md`
  - Define material identity, batches, safety classes, recipe evidence, confidence, interpolation prohibition, and promotion rules.
- `docs/design-and-parts-manifests.md`
  - Define design parameters, stable part IDs, operation IDs, authoring backends, constraints, and completeness.
- `docs/job-configuration.md`
  - Define how designs, quantities, layouts, materials, machines, modules, fixtures, effects, recipes, and exporters bind.
- `schemas/README.md`
  - Index schemas, versions, compatibility guarantees, examples, and migration rules.

### Authoring and integration documentation

- `docs/design-authoring.md`
  - Explain native geometry authoring, deterministic outputs, operation separation, parts, revisions, and tests.
- `docs/openscad-integration.md`
  - Explain CLI defines, per-operation exports, projection, units, supported SVG/DXF subset, normalization, and failure cases.
- `docs/grbl-dialect-and-gcode.md`
  - Explain supported commands, modal state, safe headers/footers, power/feed mapping, arcs, formatting, parsing, and validation.
- `docs/lasergrbl-integration.md`
  - Explain why G-code is the handoff, supported LaserGRBL versions, loading/preview/streaming workflow, limitations, and cross-platform alternatives.
- `docs/exporter-and-adapter-contracts.md`
  - Define pure inputs/outputs, capability declaration, deterministic behavior, error handling, test fixtures, and readiness gates.
- `docs/tools/boxes.md`
  - Define Boxes.py routing, setup, generator discovery, deterministic YAML generation, SVG operation colors, kerf/thickness ownership, provenance, and unsupported uses.
- `docs/build-script-reference.md`
  - Define `scripts/laser_build.py`, its arguments, defaults, exit codes, output layout, dry-run behavior, and examples.
  - Cover normal builds, explicit configs/jobs, quantities, new revisions, validation-only, audit-only, and dry-run modes.
  - State explicitly that the script generates artifacts but never streams to hardware or emits laser light.
- `docs/licensing-and-third-party-references.md`
  - Record submodule licenses, permitted reference use, clean-room boundaries, attribution, update procedure, and incompatibility risks.

### Fabrication and operator documentation

- `docs/safety/material-safety.md`
  - Define prohibited/conditional material classes, unknown-material refusal, fumes, reflectivity, fire, supervision, ventilation, and emergency response.
- `docs/safety/machine-operation.md`
  - Define preflight, enclosure/interlocks, focus, framing, emergency stop, hold/abort, cleanup, and maintenance.
- `docs/calibration.md`
  - Explain coupon families, measurement methods, evidence, recipe promotion, uncertainty, and recalibration triggers.
- `docs/layout-and-nesting.md`
  - Explain single, batch, set, nesting, grain, keep-outs, multi-sheet, deterministic seeds, and completeness.
- `docs/fixtures-registration-and-camera-placement.md`
  - Explain datum strategies, fixture manifests, registration marks, arbitrary-object engraving, camera capability boundaries, and repeatability.
- `docs/operator-workflow.md`
  - Provide setup-to-cleanup flow using build artifacts and LaserGRBL.
- `docs/fabrication-readiness.md`
  - Define blocked, calibration-only, test-ready, and fabrication-ready states with exact evidence requirements.
- `docs/troubleshooting.md`
  - Route geometry, config, G-code, connection, alarm, incomplete-cut, alignment, raster, and safety failures to the correct playbook.

### Testing and compatibility documentation

- `docs/testing-strategy.md`
  - Define unit, schema, property, golden, parser, emulator, preview, integration, hardware acceptance, and regression tests.
- `docs/compatibility-matrix.md`
  - Track machines, firmware, modules, GRBL dialects, exporters, senders, operating systems, and readiness.
- `docs/portability-guide.md`
  - Explain how to add another machine without changing design geometry.
- `docs/migration-policy.md`
  - Define schema, profile, manifest, generated-artifact, and adapter migrations with rollback requirements.

## Required References and Templates

### References

- `references/laser-operation-ordering.md`: canonical engraving, scoring, interior-cut, exterior-cut, release, cooldown, and module-swap ordering rules.
- `references/grbl-command-and-state-model.md`: commands, modal groups, laser state, power/feed state, coordinates, acknowledgements, alarms, and reset semantics.
- `references/material-safety-classification.md`: allowed, conditional, prohibited, and unknown classifications with evidence rules.
- `references/calibration-evidence-and-confidence.md`: raw observations, measurements, uncertainty, confidence, recipe promotion, and invalidation.
- `references/coordinate-and-tolerance-conventions.md`: units, transforms, tolerances, curve flattening, kerf, and numeric precision.
- `references/artifact-readiness-levels.md`: exact requirements for blocked, calibration-only, test-ready, and fabrication-ready outputs.
- `references/third-party-source-map.md`: pinned upstream paths and the behavior each path informs.
- `references/lasergrbl-compatibility-observations.md`: local observations from loading generated golden G-code, without copying GPLv3 implementation.
- `references/helper-tool-contract.md`: common roles, manifests, setup, invocation, provenance, update, and failure boundaries for callable helpers.
- `references/geometry-backend-selection.md`: capability-based selection among native, OpenSCAD, callable-helper, and combined geometry sources.

### Templates

- `templates/machine_profile.json`: complete machine-profile skeleton with provenance and verification fields.
- `templates/material_profile.json`: material identity, safety, recipes, evidence, and confidence skeleton.
- `templates/design_manifest.json`: design identity, backend, revision, parameters, constraints, and parts reference.
- `templates/parts_manifest.json`: stable part and operation IDs with completeness rules.
- `templates/job_config.json`: design/material/machine/layout/fixture/effect/export binding.
- `templates/fixture_manifest.json`: datum, geometry, keep-outs, stock/object placement, and repeatability.
- `templates/calibration_report.md`: setup, matrix, raw measurements, observations, promoted cells, failures, and attachments.
- `templates/hardware_acceptance_report.md`: machine/profile/firmware identity, test cases, evidence, deviations, and readiness decision.
- `templates/fabrication_run_report.md`: job/build identity, setup, overrides, alarms, outcome, measurements, and follow-up.
- `templates/safety_review.md`: material, machine, geometry, G-code, operator, environment, and readiness gates.
- `templates/incident_report.md`: event type, immediate response, evidence, root cause, disposition, and prevention.

## Execution Plan

Tasks labeled `post-MVP` require separate future plans and do not block the MVP acceptance criteria.

- [ ] 1. Establish architecture and contracts.
  - [x] 1.1 Record CC BY-NC-SA 4.0 as the host license and prohibit copying, importing, linking, vendoring, or runtime dependence on either reference submodule.
  - [x] 1.2 Select and document Python 3.11+ with a standard-library-only initial runtime and no dependency lock file.
  - [ ] 1.3 Write an architecture decision record for the compiler-style pipeline and machine-independent core.
  - [ ] 1.4 Complete an SVG/geometry compatibility spike and select the MVP normalization approach.
  - [x] 1.5 Define and prototype an OpenSCAD font-to-operation-model adapter using SVG exports.
  - [ ] 1.6 Define canonical units, coordinate axes, origin, winding, transforms, tolerances, and operation ordering.
  - [ ] 1.7 Define versioned JSON Schemas for machine, material, design, parts, fixture, job, and build manifests.
  - [x] 1.8 Define deterministic default design-revision resolution through `project.json`.
  - [ ] 1.9 Add dependency management, formatting, static checks, and automated tests before feature growth.
  - [x] 1.10 Define the stable `scripts/laser_build.py` argument, default-resolution, output, non-emission, and dry-run contracts.
  - [ ] 1.11 Define the continuous-integration matrix for supported Python versions, operating systems, schemas, golden fixtures, and deterministic builds.
  - [x] 1.12 Create and approve a bounded vector-foundation active plan rather than promoting this umbrella roadmap.
  - [x] 1.13 Define and implement a manifest-driven subprocess contract for callable helper tools with Boxes.py as the first adapter.

- [ ] 2. Create each project-specific playbook before its governed implementation.
  - [x] 2.1 Create and index `how_to_add_a_new_laser_design.md`.
  - [x] 2.2 Create and index `how_to_author_openscad_laser_geometry.md`.
  - [x] 2.3 Create and index `how_to_create_and_validate_a_machine_profile.md`.
  - [ ] 2.4 Create and index `how_to_calibrate_a_material_and_promote_recipes.md`.
  - [x] 2.5 Create and index `how_to_build_and_audit_a_laser_job.md`.
  - [x] 2.6 Create and index `how_to_generate_and_validate_grbl_gcode.md`.
  - [ ] 2.7 Create and index `how_to_preview_and_stream_with_lasergrbl.md`.
  - [ ] 2.8 Create and index `how_to_create_single_batch_set_and_nested_layouts.md`; mark nesting and multi-sheet sections `post-MVP`.
  - [ ] 2.9 Create and index `how_to_create_mixed_cut_score_and_engrave_jobs.md`; keep vector-only single-module use in MVP and mark module swaps `post-MVP`.
  - [ ] 2.10 Create and index `how_to_engrave_arbitrary_objects_with_fixtures.md` (`post-MVP`).
  - [ ] 2.11 Create and index `how_to_run_laser_hardware_acceptance_tests.md`.
  - [ ] 2.12 Create and index `how_to_handle_interrupted_failed_or_unsafe_jobs.md`.
  - [ ] 2.13 Create and index `how_to_add_or_modify_a_grbl_dialect_adapter.md`.
  - [ ] 2.14 Create and index `how_to_update_reference_submodules_and_review_compatibility.md`.
  - [ ] 2.15 Create and index `how_to_review_laser_job_safety_and_fabrication_readiness.md`.
  - [ ] 2.16 Verify every playbook contains prerequisites, atomic steps, safety boundaries, artifacts, verification, failure handling, and related references.
  - [x] 2.17 Create and index generic helper-tool and Boxes.py geometry playbooks.

- [ ] 3. Create and synchronize governing project documentation.
  - [x] 3.1 Update human-facing `README.md` with purpose, prerequisites, quick start, safety, outputs, and documentation links.
  - [x] 3.2 Expand `AGENTS.md` with the implemented laser playbook index and routing guidance.
  - [ ] 3.3 Create architecture and repository-structure documentation.
  - [ ] 3.4 Create coordinate, operation-model, artifact-lifecycle, and provenance documentation.
  - [ ] 3.5 Create configuration, schema, machine, material, design, parts, and job documentation.
  - [ ] 3.6 Create OpenSCAD, GRBL, LaserGRBL, exporter, and licensing integration documentation.
  - [ ] 3.7 Create safety, calibration, layout, fixture, operator, readiness, and troubleshooting documentation.
  - [ ] 3.8 Create testing, compatibility, portability, and migration documentation.
  - [ ] 3.9 Verify all documented paths, commands, schemas, examples, and readiness claims against the repository.
  - [x] 3.10 Document callable helper tools and the Boxes.py integration boundary.

- [ ] 4. Create reusable references and templates.
  - [ ] 4.1 Create operation-ordering and GRBL state-model references.
  - [ ] 4.2 Create material-safety, calibration-evidence, coordinate/tolerance, and readiness references.
  - [ ] 4.3 Create third-party source-map and LaserGRBL compatibility-observation references.
  - [ ] 4.4 Create JSON templates for machine, material, design, parts, job, and fixture configs.
  - [ ] 4.5 Create report templates for calibration, hardware acceptance, fabrication runs, safety reviews, and incidents.
  - [ ] 4.6 Validate every JSON template against its schema and every Markdown template against its governing playbook.
  - [x] 4.7 Create reusable helper-tool contract and geometry-backend selection references.

- [ ] 5. Implement the machine-profile system.
  - [x] 5.1 Create the sourced provisional Falcon A1 Pro profile.
  - [ ] 5.2 Add machine-profile schema validation and limit assertion helpers.
  - [ ] 5.3 Read the physical machine or official device profile to verify X/Y travel, origin, focus semantics, firmware, and module capabilities.
  - [ ] 5.4 Record conservative usable margins and head/fixture keep-outs from physical measurements.
  - [ ] 5.5 Add a generic reference-machine profile proving that core code contains no Falcon-specific assumptions.

- [ ] 6. Implement geometry and operation modeling.
  - [ ] 6.1 Implement primitives, paths, text outlines, transforms, grouping, and bounding boxes.
  - [ ] 6.2 Implement MVP semantic operation classes for through-cut, score, vector engrave, registration, fixture, keep-out, and construction geometry.
  - [ ] 6.3 Implement kerf compensation with explicit inside, outside, and centerline intent.
  - [ ] 6.4 Implement topology checks for closure, self-intersection, duplicates, minimum features, and post-kerf viability.
  - [ ] 6.5 Build a parameterized calibration-card design as the first end-to-end design.
  - [ ] 6.6 Implement raster-engrave operation classes and raster geometry bindings (`post-MVP`).

- [ ] 7. Implement material calibration and process recipes.
  - [ ] 7.1 Define material identity, batch, thickness, safety, and recipe schemas.
  - [ ] 7.2 Implement power-speed-pass test matrices for cutting and engraving.
  - [ ] 7.3 Implement MVP kerf, slot-fit, hole-size, and focus-ramp coupons.
  - [ ] 7.4 Capture measured results and promote only verified cells into fabrication recipes.
  - [x] 7.5 Seed the first Falcon basswood profile from an official recommendation while marking every value unverified.
  - [x] 7.6 Implement hard rejection for unknown-composition materials.
  - [ ] 7.7 Implement raster-interval and depth-calibration coupons (`post-MVP`).

- [ ] 8. Implement single-object, batch, and set layout.
  - [ ] 8.1 Place a single object with explicit origin and margins.
  - [x] 8.2 Generate deterministic rectangular arrays for repeated identical and mixed-type objects.
  - [ ] 8.3 Place complete multi-part sets with set-level quantity and completeness checks.
  - [ ] 8.4 Add rotation, grain-direction, spacing, and stock-edge constraints.
  - [ ] 8.5 Add deterministic nesting behind a replaceable layout interface (`post-MVP`).
  - [ ] 8.6 Add multi-sheet spillover and per-sheet manifests (`post-MVP`).

- [ ] 9. Implement engraving workflows.
  - [x] 9.1 Support vector engraving embedded in the first cut design.
  - [ ] 9.2 Support raster engraving embedded in cut designs (`post-MVP`).
  - [ ] 9.3 Support engraving-only jobs on arbitrary objects using fixtures or measured datums (`post-MVP`).
  - [ ] 9.4 Add optional camera-assisted placement as an adapter capability rather than a core dependency (`post-MVP`).
  - [ ] 9.5 Support calibrated multi-pass/depth engraving with uncertainty and thermal controls (`post-MVP`).
  - [ ] 9.6 Support separate laser modules and fail when the requested material/effect is incompatible (`post-MVP`).

- [ ] 10. Implement build, preview, and provenance.
  - [x] 10.1 Generate layered SVG and operation previews.
  - [x] 10.2 Generate exact artifact expectations from job and build manifests.
  - [x] 10.3 Stage complete builds under `.tmp/laser/<design>/`.
  - [x] 10.4 Hash design sources, configs, machine/material profiles, and artifacts.
  - [x] 10.5 Atomically install current outputs and preserve immutable numbered revisions.
  - [x] 10.6 Implement audit-only verification for installed current artifacts.
  - [x] 10.7 Ensure generated outputs are ignored and keep tests source-only.
  - [x] 10.8 Implement `scripts/laser_build.py --design <name>` with default config resolution and atomic installation to `output/<design>/`.
  - [?] 10.9 Implement optional `--config`, `--job`, `--quantity`, and `--new-revision` flags; all except `--job` are implemented.
  - [x] 10.10 Implement `--validate-only`, `--audit-only`, and `--dry-run` flags.
  - [x] 10.11 Keep the initial implementation behind one script without package installation or additional user-facing commands.
  - [?] 10.12 The script has no hardware transport or streaming code; deterministic exit-code coverage remains pending.

- [ ] 11. Implement exporters and operator handoff.
  - [x] 11.1 Export SVG with semantic operation groups, deterministic colors, units, and a lower-left coordinate transform.
  - [ ] 11.2 Export DXF for vector-only interchange.
  - [ ] 11.3 Export raster assets with pinned size, resolution, and preprocessing metadata (`post-MVP`).
  - [x] 11.4 Generate operation data and a material setup checklist.
  - [ ] 11.5 Implement a versioned GRBL dialect adapter with explicit coordinate, power-scale, motion, arc, laser-mode, and accessory capabilities.
  - [ ] 11.6 Generate deterministic `.gcode` and `.nc` artifacts from the canonical operation model.
  - [ ] 11.7 Validate generated G-code using LaserGRBL preview, bounds checks, framing, and controlled hardware acceptance tests.
  - [ ] 11.8 Document LaserGRBL loading, preview, connection, alarm, hold, resume, reset, and streaming procedures.
  - [ ] 11.9 Validate Falcon Design Space and LightBurn compatibility as secondary workflows using golden jobs (`post-MVP`).
  - [ ] 11.10 Add direct framework-to-device streaming only after command semantics, buffering, interlocks, framing, abort behavior, and emergency-stop behavior are tested on hardware (`post-MVP`).

- [ ] 12. Complete hardware acceptance and portability proof.
  - [x] 12.1 Run dry-run and artifact audits without hardware for the first design.
  - [ ] 12.2 Run frame-only bounds tests on the Falcon A1 Pro.
  - [ ] 12.3 Cut and measure calibration coupons across initial materials and thicknesses.
  - [ ] 12.4 Verify engraving registration, repeatability, camera/manual datum workflows, and mixed-operation ordering.
  - [ ] 12.5 Verify interruption behavior and document safe restart procedures.
  - [ ] 12.6 Add a second machine profile and execute the same acceptance suite without changing design code (`post-MVP`).
  - [ ] 12.7 Publish the MVP `example_tag` template with vector cut, score, engraving, and rectangular-array examples.
  - [ ] 12.8 Publish arbitrary-object, raster, multi-module, and complete-set starter templates (`post-MVP`).

## Additional Modes and Processes

After the core workflow is stable, consider:

- Score, fold-line, perforation, kiss-cut, and through-cut modes.
- Interior-first and common-line cutting optimization.
- Tabs/micro-joints that retain small pieces in the sheet.
- Inlay, marquetry, veneer, stencil, and press-fit joint workflows.
- Two-sided engraving/cutting with flip jigs and registration pins.
- Rotary/cylindrical engraving.
- Conveyor or tiled long-stock processing.
- Camera tracing and batch placement when supported by the selected adapter.
- Photo engraving with pluggable dithering and grayscale calibration.
- Multicolor or oxidation marking recipes for supported metals.
- Relief/depth engraving with measured depth maps and uncertainty.
- Variable-power vector engraving and hatch/fill generation.
- Material utilization estimates, deterministic nesting, remnants inventory, and cost estimation.
- Multi-sheet kits with labels, assembly marks, and bill of materials.
- Fixture and jig generation, including sacrificial alignment templates.
- Focus maps or segmented jobs for slightly non-flat stock.
- Checkpointed jobs designed for safe manual restart because the A1 Pro does not resume after power loss.
- Maintenance tracking for lens cleaning, exhaust condition, air-assist verification, and calibration age.
- Post-process inspection records with photos, dimensions, cut-through checks, and artifact-to-result traceability.
- A simulation mode that estimates path length, runtime, operation count, thermal concentration, and likely risk areas without controlling hardware.

## Verification Objective

- [ ] 13. Verify the framework against its core promises.
  - [ ] 13.1 Prove one design can target two machine profiles without geometry changes.
  - [ ] 13.2 Prove one material can hold distinct recipes for different modules and thicknesses.
  - [ ] 13.3 Prove single, repeated, set, mixed cut/engrave, and engraving-only jobs use the same build pipeline.
  - [ ] 13.4 Prove every accepted artifact set can be reproduced and audited from pinned inputs.
  - [ ] 13.5 Prove unsafe, unsupported, out-of-bounds, or uncalibrated jobs fail before export.
  - [ ] 13.6 Prove generated G-code loads and previews consistently in LaserGRBL and at least one alternate GRBL sender.
  - [ ] 13.7 Prove project documentation, playbooks, references, templates, schemas, and implementation remain synchronized.
