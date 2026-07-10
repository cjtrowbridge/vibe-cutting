---
plan_id: 2026-07-09-10-30-00_add-png-svg-build-artifacts
title: "Generate Operation-Specific PNG and SVG Artifacts"
summary: "Augment the build pipeline to produce .png files for engraving operations and .svg files for cutting operations, in addition to existing G-code artifacts."
status: past
created_at: 2026-07-09-10-30-00
---

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

### Plan

**Phase 1: Investigation and Discovery (Read-Only)**

- `[x]` Analyze `scripts/laser_build.py` to identify the operation processing loop and existing artifact generation logic.
- `[x]` Analyze a sample design configuration to determine how engraving and cutting operations are defined and differentiated.
- `[x]` Review `setup/pixi.toml` to list current SVG/image libraries and identify any missing dependencies for SVG-to-PNG conversion.

**Phase 2: Artifact Contract and Audit Model**

- `[x]` Define the per-operation sidecar artifact naming contract using the same operation, material, and pass-count prefix as existing G-code artifacts, for example `operations/001_vector_engrave__basswood_3mm__run_1_pass.png` and `operations/002_through_cut__basswood_3mm__run_1_pass.svg`.
- `[x]` Define artifact semantics: engraving PNGs are inspection/transfer artifacts for engraving geometry only, cutting SVGs are inspection/transfer artifacts for cutting geometry only, and G-code remains the machine-authoritative artifact.
- `[x]` Decide whether sidecars are emitted only for current known operation classes (`vector_engrave` -> `.png`, `through_cut` -> `.svg`) or for every future operation type through an explicit operation-to-sidecar mapping.
- `[x]` Define the `job_plan.json` and `job_manifest.json` metadata shape for operation sidecars, including path, kind, byte count, and SHA-256 hash.
- `[x]` Define whether `operations.csv` should list sidecar paths in additional columns alongside the authoritative G-code artifact path.
- `[x]` Define exact audit expectations: sidecar artifacts must be included in `build_manifest.json`, and `--audit-only` must fail when any generated sidecar is missing or modified.
- `[x]` Prefer extending the existing dependency-free PNG rendering path before adding third-party SVG-to-PNG conversion dependencies.
- `[-]` If native rendering cannot meet the artifact contract, propose and receive approval for any new dependency (for example `cairosvg`) and document the bootstrap/platform validation impact before editing `setup/pixi.toml`.

Decision notes:

- Current operation sidecars are explicit by operation type: `vector_engrave` emits transparent-background PNG, `through_cut` emits cut-only SVG, and unknown operations fail closed until mapped.
- `job_plan.json` and `job_manifest.json` record sidecars under `sidecar_artifacts` with `kind`, `path`, `bytes`, and `sha256`.
- `operations.csv` includes sidecar artifact path columns so operator-facing tabular output matches the manifests.
- Native dependency-free rendering is sufficient for the current vector engraving PNG sidecar; no new `setup/pixi.toml` dependency is planned.

**Phase 3: Implementation**

- `[x]` In `scripts/laser_build.py`, add explicit operation-to-sidecar mapping logic for engraving, cutting, and unsupported/other operations.
- `[x]` Add helper functions that derive sidecar artifact names from the existing operation artifact prefix without duplicating filename policy.
- `[x]` For engraving operations, implement the logic to isolate the operation's geometry and render it as a `.png` file in the `operations` output directory.
- `[x]` For cutting operations, implement the logic to isolate the operation's geometry and save it as a new `.svg` file in the `operations` output directory.
- `[x]` Update operation stage records so `job_plan.json` records all sidecar artifacts with kind, path, bytes, and SHA-256 hash.
- `[x]` Update `job_manifest.json` so each operation summary references its sidecar artifacts without implying they are machine-executable.
- `[x]` Update `operations.csv` if Phase 2 selects CSV sidecar columns.
- `[x]` Ensure `build_manifest.json` and staged exact audits include the new sidecar artifacts before install.
- `[x]` Preserve existing `design.svg`, `preview.png`, `job.gcode`, operation G-code, operation order, rerun semantics, and readiness behavior.

**Phase 4: Tests**

- `[x]` Add focused filename tests for `.png` and `.svg` sidecar paths that match the operation, material, and pass-count naming contract.
- `[x]` Add a build test that asserts expected `.gcode`, `.png`, and `.svg` files are created in the `operations` output directory.
- `[x]` Add manifest tests proving `build_manifest.json` includes sidecar byte counts and hashes.
- `[x]` Add job metadata tests proving `job_plan.json` and `job_manifest.json` reference sidecar artifacts with the expected kind/path/hash fields.
- `[x]` Add audit tamper tests proving `--audit-only` fails when a sidecar artifact is deleted.
- `[x]` Add audit tamper tests proving `--audit-only` fails when a sidecar artifact is modified.
- `[x]` Add geometry-isolation tests proving the cut SVG contains `through_cut` geometry and does not include `vector_engrave` geometry.
- `[x]` Add PNG validity tests proving the engraving sidecar is valid PNG data and contains engraving pixels.
- `[x]` Add regression tests proving `design.svg`, `preview.png`, operation G-code, operation ordering, and rerun metadata retain their existing roles.

**Phase 5: Verification**

- `[x]` Run the modified build script for the `shot_coins` design.
- `[x]` Verify that the `output/shot_coins/operations/` directory contains the expected `.png`, `.svg`, and `.gcode` files.
- `[x]` Manually inspect the generated `shot_coins` image artifacts to confirm they are correct (e.g., engraving-only PNG content, cut-only SVG paths, expected orientation).
- `[x]` Run automated smoke builds for `hug_coins`, one merit badge set, and `primitive_power_extender_laser_0_1` to catch design-family assumptions.
- `[x]` Run `--audit-only` against the rebuilt output and confirm exact artifact inventory and hashes pass.
- `[x]` Run the entire test suite, including the new test cases, to ensure no regressions were introduced.

**Phase 6: Documentation**

- `[x]` Update `README.md` to list the `.png` and `.svg` files as part of the standard build output.
- `[x]` Update `docs/build-script-reference.md` with a more detailed description of the new artifacts.
- `[x]` Document that per-operation PNG/SVG artifacts are inspection/transfer sidecars and that G-code remains the machine-authoritative artifact.
- `[x]` Document the sidecar naming contract and where hashes are recorded.
- `[x]` Review `playbooks/how_to_build_and_audit_a_laser_job.md` and update it to include checking the new image files as part of the audit process.
