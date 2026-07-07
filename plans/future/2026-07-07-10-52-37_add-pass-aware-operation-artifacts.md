---
plan_id: 2026-07-07-10-52-37_add-pass-aware-operation-artifacts
title: Add Pass-Aware Operation Artifacts
summary: Update the laser build pipeline to model recipe pass schedules, emit per-operation G-code artifacts with material/thickness/pass-count filenames, and record rerun semantics in job manifests.
status: future
created_at: 2026-07-07-10-52-37
---

# Add Pass-Aware Operation Artifacts

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Objective

Make laser jobs explicitly pass-aware so operators can run or rerun one operation stage without re-running unrelated stages. The default operator-facing model is one G-code artifact per operation, with that artifact internally containing the configured number of passes for the current material and thickness.

Example target artifact names:

```text
operations/001_vector_engrave__basswood_3mm__run_1_pass.gcode
operations/002_through_cut__basswood_3mm__run_3_passes.gcode
```

`job.gcode` remains the full combined job. `job_plan.json` and existing manifests become the machine-readable source of truth for operation order, recipe assumptions, pass counts, rerun implications, and artifact hashes.

## Design Decisions To Preserve

- Emit one default artifact per operation stage, not one default artifact per individual pass.
- Include material identity and thickness in operation artifact filenames.
- Include pass count in operation artifact filenames.
- Keep filenames human-legible but make manifests authoritative.
- Make rerun semantics explicit: rerunning an operation artifact adds its full pass count again.
- Keep optional single-pass diagnostic artifacts out of the default output unless a later calibration mode explicitly requests them.
- Do not let helper libraries own pass scheduling, operation ordering, material recipes, or fabrication readiness.

## Execution Plan

- [ ] 1. Define pass-aware job model.
  - [ ] 1.1 Add a `job_plan.json` schema describing operation stages, material assumptions, pass counts, recipe settings, artifact paths, hashes, and rerun semantics.
  - [ ] 1.2 Define stable operation artifact naming: `<order>_<operation>__<material_id>__run_<n>_pass(es).gcode`.
  - [ ] 1.3 Define filename slug normalization for operation IDs, material IDs, and pass labels.
  - [ ] 1.4 Define how `profile_status`, calibration status, machine ID, module ID, and material thickness are represented in `job_plan.json`.
  - [ ] 1.5 Define whether `job.gcode` inlines stage G-code bodies or regenerates the same deterministic stage bodies during combined output.
  - [ ] 1.6 Define fail-closed behavior for missing, zero, negative, non-integer, or unsupported pass counts.

- [ ] 2. Update material and recipe contracts.
  - [ ] 2.1 Confirm current material recipe fields are sufficient for stage artifacts: speed, power, passes, and air assist.
  - [ ] 2.2 Add schema or validation constraints for positive integer `passes`.
  - [ ] 2.3 Add a forward-compatible place for optional future pass-specific overrides such as focus offset, power ramping, pause prompts, or cleanup passes.
  - [ ] 2.4 Preserve current basswood seed recipe values unless a separate calibration plan changes them.

- [ ] 3. Refactor G-code generation.
  - [ ] 3.1 Split operation-stage G-code generation from combined `job.gcode` generation.
  - [ ] 3.2 Generate `vector_engrave` stage G-code using the configured vector engraving pass count.
  - [ ] 3.3 Generate `through_cut` stage G-code using the configured through-cut pass count.
  - [ ] 3.4 Repeat the same operation path body once per configured pass inside each operation-stage artifact.
  - [ ] 3.5 Generate combined `job.gcode` by preserving stage order and pass repetition exactly.
  - [ ] 3.6 Keep rapid moves laser-off and operation ordering engrave-before-cut.
  - [ ] 3.7 Add clear G-code comments for operation, material, thickness, pass number, total passes, speed, power, and air assist.

- [ ] 4. Update output inventory and manifests.
  - [ ] 4.1 Add `operations/` G-code artifacts to the installed output directory.
  - [ ] 4.2 Add `job_plan.json` to the installed output directory.
  - [ ] 4.3 Update `build_manifest.json` to include the new artifacts and hashes.
  - [ ] 4.4 Update `job_manifest.json` to summarize operation artifact paths, recipe assumptions, pass counts, and rerun effects.
  - [ ] 4.5 Update `operations.csv` to include artifact path and passes-per-run.
  - [ ] 4.6 Ensure `--audit-only` verifies operation artifacts and `job_plan.json`.

- [ ] 5. Update operator documentation.
  - [ ] 5.1 Update `README.md` to describe pass-aware operation artifacts at a high level.
  - [ ] 5.2 Update `docs/build-script-reference.md` with the new output inventory.
  - [ ] 5.3 Update `playbooks/how_to_build_and_audit_a_laser_job.md` with operation-stage run/rerun guidance.
  - [ ] 5.4 Update `docs/safety/material-safety.md` or setup docs with the warning that rerunning an operation artifact repeats its full pass count.
  - [ ] 5.5 Update coin design READMEs if their output examples mention only monolithic `job.gcode`.

- [ ] 6. Add tests for pass-aware artifacts.
  - [ ] 6.1 Test that a multi-pass through-cut recipe repeats cut paths the configured number of times.
  - [ ] 6.2 Test that operation artifact filenames include operation, material ID, and pass count.
  - [ ] 6.3 Test that `job.gcode` and operation artifacts agree on stage order and repeated pass bodies.
  - [ ] 6.4 Test that `job_plan.json` records material ID, material name, thickness, profile status, recipes, paths, hashes, and rerun semantics.
  - [ ] 6.5 Test that `--audit-only` fails when any operation artifact or `job_plan.json` is missing or modified.
  - [ ] 6.6 Test that invalid pass counts fail validation before artifact generation.
  - [ ] 6.7 Test that current shot, hug, merit-badge, and mechanism designs still build deterministically.

- [ ] 7. Verify and checkpoint.
  - [ ] 7.1 Run focused laser build tests.
  - [ ] 7.2 Run the full repository test suite.
  - [ ] 7.3 Build and audit `shot_coins` as the first concrete pass-aware sample.
  - [ ] 7.4 Inspect generated `operations/` filenames and `job_plan.json`.
  - [ ] 7.5 Regenerate plan indexes.
  - [ ] 7.6 Record implementation results in the journal.
  - [ ] 7.7 Commit and push the completed implementation checkpoint.

## Open Questions Before Implementation

- Should `job.gcode` include full operation-stage comments before every repeated pass or only before each operation stage?
- Should the initial implementation support only existing operation types (`vector_engrave`, `through_cut`) or also wire `score` if present in future designs?
- Should operation artifact filenames include machine/module ID now, or should those remain manifest-only until multiple machine profiles are common?
- Should single-pass diagnostic artifacts be added in this plan as an opt-in flag, or deferred to a calibration-specific plan?
