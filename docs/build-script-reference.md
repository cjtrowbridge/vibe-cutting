# Build Script Reference

For a broader human-and-agent guide to every repository script, managed invocation, and pipeline safety boundary, see `scripts/README.md`.

The core build script runs through the managed bootstrap so the repository supplies its Python runtime locally:

```bash
setup/bootstrap.sh --allow-downloads setup
setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins
```

On Windows:

```powershell
.\setup\bootstrap.ps1 -AllowDownloads setup
.\setup\bootstrap.ps1 run -- scripts/laser_build.py --design shot_coins
```

Designs using `text_backend: openscad_font` additionally require OpenSCAD 2021.01 or newer. Helper-backed geometry uses provider environments beneath `.tools/` and should be invoked through `setup/bootstrap.* run -- ...`.

```bash
setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins
setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --dry-run
setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --validate-only
setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --audit-only
setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --quantity 40
setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins --new-revision
setup/bootstrap.sh run -- scripts/laser_build.py --design hug_coins
setup/bootstrap.sh run -- scripts/laser_build.py --design bwb_merit_badges
```

Normal builds atomically replace `output/<design>/`. Revision builds create immutable `revisions/<design>/rev_000N/` directories. The script generates artifacts only and cannot stream to hardware.

## Output Inventory

- `job.gcode`: complete combined job in operation order.
- `operations/*.gcode`: independently runnable operation-stage files.
- `operations/*.png`: transparent-background engraving sidecars for operation-level inspection and transfer.
- `operations/*.svg`: cut-only sidecars for operation-level inspection and transfer.
- `job_plan.json`: machine-readable operation order, material assumptions, recipe settings, pass counts, stage artifact hashes, and rerun semantics.
- `job_manifest.json`: design, readiness, recipe, warning, and operation artifact summary.
- `build_manifest.json`: exact artifact inventory with byte counts and hashes.
- `operations.csv`: operator-readable operation table with G-code artifact paths, sidecar artifact paths, and passes per run.
- `material_setup.md`: setup checklist and calibration warnings.

Operation-stage filenames use `<order>_<operation>__<material_id>__run_<n>_pass(es).gcode`, for example `002_through_cut__basswood_3mm__run_1_pass.gcode`. Rerunning one of these files repeats its full configured pass count.
Operation sidecars use the same filename prefix with an operation-specific extension, for example `001_vector_engrave__basswood_3mm__run_1_pass.png` and `002_through_cut__basswood_3mm__run_1_pass.svg`. Sidecars are recorded in `job_plan.json`, summarized in `job_manifest.json`, and hashed in `build_manifest.json`; they are not machine-executable artifacts.

## Helper Tools

```bash
setup/bootstrap.sh run -- scripts/helper_tool.py list
setup/bootstrap.sh run -- scripts/helper_tool.py validate
setup/bootstrap.sh run -- scripts/helper_tool.py describe boxes
setup/bootstrap.sh run -- scripts/helper_tool.py check boxes
setup/bootstrap.sh run -- scripts/helper_tool.py setup boxes
setup/bootstrap.sh run -- scripts/helper_tool.py run boxes -- --list
```

`check` exits nonzero until the submodule, pin, license, provider install marker, and subprocess import are valid. `setup` may use the network and writes only beneath `.tools/`. Helper source geometry must be imported by a supported design adapter before `laser_build.py` can validate or build it.

## Modes

- No mode flag: generate and install the complete current output.
- `--validate-only`: resolve inputs and validate constraints without generating artifacts.
- `--dry-run`: report the resolved revision, quantity, maximum quantity, and effective area without installing artifacts.
- `--audit-only`: verify the exact installed current artifact inventory, byte counts, and hashes.
- `--new-revision`: copy the current config to the next numbered config and build its immutable artifact snapshot.
- `--quantity N`: build the first `N` deterministic placements instead of the configured maximum.
- `--config PATH`: use an explicit committed config.

Only one mode flag may be selected. `--quantity` and `--config` refine a normal build.

## Current Limits

- The implemented backend supports the native `shot_coins` vector design shape.
- The `merit_badge_set` backend supports mixed-type rounded tokens with measured title/body wrapping and even slot allocation.
- Raster engraving, DXF, general OpenSCAD part import, Boxes.py SVG ingestion, hardware streaming, and arbitrary nesting remain roadmap work.
- The generated Falcon/basswood job is calibration-only.
