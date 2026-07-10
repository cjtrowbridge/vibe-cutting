# Scripts Pipeline Guide

This directory contains repository-owned command entrypoints. They are the operational bridge between design/configuration files, managed helper tools, validation, generated laser artifacts, and plan bookkeeping.

The short version: run scripts through the managed bootstrap whenever possible. The bootstrap selects the repository-managed Python runtime and keeps host tools, helper environments, and generated artifacts inside repository-local boundaries.

## Audience

This guide is written for both human operators and agents.

Humans should use it as a safe command map: what to run, what it changes, what outputs to inspect, and where the laser-safety boundary is.

Agents should use it as an execution contract: prefer managed bootstrap commands, keep implementation bound to the active plan, do not import helper submodules directly, and do not treat generated artifacts as fabrication-ready merely because a script succeeds.

## Core Rule

Use managed bootstrap invocation for repo scripts:

```bash
./setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins
```

On Windows:

```powershell
.\setup\bootstrap.ps1 run -- scripts\laser_build.py --design shot_coins
```

Direct `python3 scripts/...` execution is acceptable for quick local read-only inspection or tests when the host already has the needed runtime, but it is not the portable operator path. The portable path is always `setup/bootstrap.* run -- ...`.

Before a fresh host can run managed commands, initialize the managed runtime:

```bash
./setup/bootstrap.sh doctor
./setup/bootstrap.sh --allow-downloads setup
```

On Windows:

```powershell
.\setup\bootstrap.ps1 doctor
.\setup\bootstrap.ps1 -AllowDownloads setup
```

`setup` may download pinned, checksum-verified tooling. Do not run network-using setup in approval-gated environments without approval.

## Pipeline Overview

The laser build pipeline is a compiler-style workflow:

```text
design config + machine profile + material profile
    -> validation and bounded layout
    -> operation geometry
    -> preview, sidecars, G-code, manifests, setup notes
    -> staged exact audit
    -> atomic install under output/<design>/ or revisions/<design>/<revision>/
    -> installed exact audit
```

The pipeline generates files only. It does not connect to a laser, stream G-code, frame a job, set focus, set power, or approve fabrication.

## Script Inventory

### `laser_build.py`

Primary laser artifact builder.

Use it to resolve a design, validate inputs, generate deterministic layout and operation artifacts, stage the complete output set, hash everything, audit staged files, install atomically, and audit installed files.

Common commands:

```bash
./setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --validate-only
./setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --dry-run
./setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins
./setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --audit-only
./setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --quantity 40
./setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --new-revision
```

Windows equivalents:

```powershell
.\setup\bootstrap.ps1 run -- scripts\laser_build.py --design shot_coins --validate-only
.\setup\bootstrap.ps1 run -- scripts\laser_build.py --design shot_coins --dry-run
.\setup\bootstrap.ps1 run -- scripts\laser_build.py --design shot_coins
.\setup\bootstrap.ps1 run -- scripts\laser_build.py --design shot_coins --audit-only
.\setup\bootstrap.ps1 run -- scripts\laser_build.py --design shot_coins --quantity 40
.\setup\bootstrap.ps1 run -- scripts\laser_build.py --design shot_coins --new-revision
```

Supported mode flags:

- `--validate-only`: load inputs and validate constraints without generating artifacts.
- `--dry-run`: report resolved revision, quantity, maximum quantity, and work area without installing artifacts.
- no mode flag: generate and atomically install `output/<design>/`.
- `--audit-only`: verify the exact installed `output/<design>/` inventory, byte counts, and hashes.
- `--new-revision`: copy the current design config to the next numbered revision and install immutable artifacts under `revisions/<design>/<revision>/`.
- `--quantity N`: override the configured quantity for the build.
- `--config PATH`: build with a specific committed design config.

Only one of `--validate-only`, `--dry-run`, `--audit-only`, and `--new-revision` may be selected at a time.

Normal output inventory:

- `design.svg`: complete inspection/interchange SVG.
- `preview.png`: full-job raster preview.
- `job.gcode`: complete combined GRBL job in operation order.
- `operations/*.gcode`: independently runnable operation-stage G-code.
- `operations/*.png`: transparent-background engraving sidecars, currently emitted for `vector_engrave`.
- `operations/*.svg`: cut-only sidecars, currently emitted for `through_cut`.
- `operations.csv`: operator-readable operation table with G-code and sidecar paths.
- `job_plan.json`: machine-readable operation order, stage files, recipes, pass counts, hashes, and rerun semantics.
- `job_manifest.json`: operator and integration summary.
- `build_manifest.json`: exact source and artifact inventory with hashes.
- `material_setup.md`: setup checklist and calibration warnings.
- `mechanism_validation.json`: mechanism report when the design type requires one.

Operation filenames include operation order, operation name, material id, and pass count:

```text
operations/001_vector_engrave__basswood_3mm__run_1_pass.gcode
operations/001_vector_engrave__basswood_3mm__run_1_pass.png
operations/002_through_cut__basswood_3mm__run_1_pass.gcode
operations/002_through_cut__basswood_3mm__run_1_pass.svg
```

Important rerun rule: rerunning an `operations/*.gcode` file repeats that operation artifact's full configured pass count. Sidecar PNG/SVG files are not machine-executable.

### `helper_tool.py`

Helper adapter dispatcher and readiness inspector.

Use it to inspect helper manifests, check readiness, set up isolated provider environments, and invoke ready helper tools through declared adapter contracts.

Common commands:

```bash
./setup/bootstrap.sh run -- scripts/helper_tool.py list
./setup/bootstrap.sh run -- scripts/helper_tool.py validate
./setup/bootstrap.sh run -- scripts/helper_tool.py describe boxes
./setup/bootstrap.sh run -- scripts/helper_tool.py check boxes
./setup/bootstrap.sh run -- scripts/helper_tool.py report boxes
./setup/bootstrap.sh run -- scripts/helper_tool.py setup boxes
./setup/bootstrap.sh run -- scripts/helper_tool.py run boxes -- --list
```

Windows equivalents:

```powershell
.\setup\bootstrap.ps1 run -- scripts\helper_tool.py list
.\setup\bootstrap.ps1 run -- scripts\helper_tool.py validate
.\setup\bootstrap.ps1 run -- scripts\helper_tool.py describe boxes
.\setup\bootstrap.ps1 run -- scripts\helper_tool.py check boxes
.\setup\bootstrap.ps1 run -- scripts\helper_tool.py report boxes
.\setup\bootstrap.ps1 run -- scripts\helper_tool.py setup boxes
.\setup\bootstrap.ps1 run -- scripts\helper_tool.py run boxes -- --list
```

Use `--verbose` before the subcommand for more logging:

```bash
./setup/bootstrap.sh run -- scripts/helper_tool.py --verbose check boxes
```

Safety boundary:

- Helper tools may generate source geometry, not authoritative machine artifacts.
- Helper source under `third_party/` is not host-owned source.
- Do not import helper submodules into host Python.
- Do not modify helper source submodules.
- Do not use helper-generated G-code as authoritative machine output.
- Route helper output back through host validation and `laser_build.py` before any readiness claim.

### `mechanism_validate.py`

Mechanism model validator.

Use it to validate host-owned mechanism JSON before treating a mechanism design as buildable. Mechanism validation checks gear meshes, ratios, phases, backlash, bore/axle clearance, tooth root/web estimates, rotating clearance, stack layers, interfaces, duplicate-cut risk, and helper provenance.

Common command:

```bash
./setup/bootstrap.sh run -- scripts/mechanism_validate.py designs/primitive_power_extender_laser_0_1/mechanisms/primitive_power_extender.mechanism.json --output .tmp/primitive_power_extender/mechanism-validation.json
```

Windows equivalent:

```powershell
.\setup\bootstrap.ps1 run -- scripts\mechanism_validate.py designs\primitive_power_extender_laser_0_1\mechanisms\primitive_power_extender.mechanism.json --output .tmp\primitive_power_extender\mechanism-validation.json
```

When `laser_build.py` builds a mechanism-backed design, it runs mechanism validation as part of the build and installs `mechanism_validation.json` with the output artifacts.

Mechanism validation is necessary but not sufficient for fabrication. It does not prove kerf, material behavior, durability, calibration, or safe machine operation.

### `host_readiness_report.py`

Host readiness evidence reporter.

Use it to capture a local evidence report for bootstrap/tooling state, submodule cleanliness, helper readiness, lock hashes, and smoke artifact presence.

Common command:

```bash
./setup/bootstrap.sh run -- scripts/host_readiness_report.py
```

Optional output root:

```bash
./setup/bootstrap.sh run -- scripts/host_readiness_report.py --output-root .tools/reports/host-readiness
```

Windows equivalent:

```powershell
.\setup\bootstrap.ps1 run -- scripts\host_readiness_report.py --output-root .tools\reports\host-readiness
```

Reports belong under repository-local generated-output paths. Do not include credentials, personal host inventories, unrelated environment variables, or user secrets in readiness evidence.

### `regenerate_plan_indexes.py`

Plan index maintainer.

Use it after creating, moving, archiving, or editing plan files. It refreshes:

- `plans/future/index.md`
- `plans/current/index.md`
- `plans/past/index.md`

Common command:

```bash
python3 agents/scripts/regenerate_plan_indexes.py --repo-root .
```

This repository also has a host-managed copy:

```bash
python3 scripts/regenerate_plan_indexes.py --repo-root .
python3 scripts/regenerate_plan_indexes.py --check --repo-root .
```

Use the `agents/scripts/` path when following the host framework instruction that treats `./agents` as canonical. Use the host-managed `scripts/` copy when maintaining the host copy itself. Both paths should produce the same index format.

## Recommended Human Workflow

1. Confirm the design and material intent.
2. Run bootstrap setup if the host is new:

   ```bash
   ./setup/bootstrap.sh doctor
   ./setup/bootstrap.sh --allow-downloads setup
   ```

3. Validate helper readiness if the design depends on a helper:

   ```bash
   ./setup/bootstrap.sh run -- scripts/helper_tool.py validate
   ./setup/bootstrap.sh run -- scripts/helper_tool.py check boxes
   ```

4. Validate the design without writing output:

   ```bash
   ./setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --validate-only
   ```

5. Dry-run the resolved layout and quantity:

   ```bash
   ./setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --dry-run
   ```

6. Build the output:

   ```bash
   ./setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins
   ```

7. Inspect generated files:

   - `preview.png`
   - `design.svg`
   - `operations.csv`
   - `job_plan.json`
   - `job_manifest.json`
   - `material_setup.md`
   - `operations/*.gcode`
   - `operations/*.png`
   - `operations/*.svg`

8. Run exact audit:

   ```bash
   ./setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --audit-only
   ```

9. Separately preview G-code in a trusted sender/viewer such as LaserGRBL before hardware use.
10. Do not fabricate until machine, material, focus, ventilation, enclosure, fire response, and calibration gates have passed.

## Recommended Agent Workflow

1. Read `AGENTS.md` and `agents/RULES.md` before repository actions.
2. Identify or create the active governing plan before edits.
3. Bind every implementation or documentation edit to explicit plan checklist items.
4. Prefer `rg` for local search when available; otherwise use `grep`.
5. Prefer managed bootstrap commands for build pipeline behavior.
6. Never import or edit read-only helper/reference submodules.
7. Never silently broaden scope when a script exposes missing work; revise the plan first.
8. After plan changes, run:

   ```bash
   python3 agents/scripts/regenerate_plan_indexes.py --repo-root .
   ```

9. For pipeline changes, run focused tests plus relevant builds/audits.
10. For generated output changes, check whether files are tracked or ignored before staging.
11. Run `git diff --check` before summarizing.

## Safety And Authority Boundaries

The scripts can prove that files are internally consistent. They cannot prove that a physical laser job is safe.

Treat these as separate gates:

- Script success: inputs resolved, geometry generated, manifests hashed, audit passed.
- Operator inspection: previews, sidecars, setup notes, G-code, and material assumptions reviewed.
- Machine readiness: machine profile and module constraints understood.
- Material readiness: recipes calibrated for the exact material, thickness, focus, and environment.
- Fabrication approval: supervised non-emitting frame, fire safety, ventilation, enclosure, emergency stop, and accepted calibration coupons.

Only the first gate is owned by these scripts.

## Troubleshooting

If `run` cannot find Python, do not install random host Python packages. Run bootstrap setup or repair through `setup/bootstrap.*`.

If helper checks fail, inspect:

```bash
./setup/bootstrap.sh run -- scripts/helper_tool.py report <tool-id>
```

If a build fails before install, inspect staged evidence under `.tmp/laser/<design>/`. Do not manually copy partial outputs over `output/<design>/`.

If `--audit-only` fails, compare `build_manifest.json` with the installed files. A missing, edited, or extra generated file is enough to fail exact audit.

If a generated operation G-code artifact is rerun on hardware, remember that it repeats every configured pass for that operation. Do not rerun operation artifacts casually.

If plan indexes look stale after moving plan files, regenerate them:

```bash
python3 agents/scripts/regenerate_plan_indexes.py --repo-root .
```
