# Build Script Reference

The core build script requires Python 3.11 or newer and no third-party Python packages. On portable hosts, use the managed bootstrap so the repository supplies that Python runtime locally:

```bash
setup/bootstrap.sh --allow-downloads setup
setup/bootstrap.sh run -- scripts/laser_build.py --design shot_coins
```

On Windows:

```powershell
.\setup\bootstrap.ps1 -AllowDownloads setup
.\setup\bootstrap.ps1 run -- scripts/laser_build.py --design shot_coins
```

Development hosts with Python 3.11+ may still run the script directly. Designs using `text_backend: openscad_font` additionally require OpenSCAD 2021.01 or newer. Helper-backed geometry currently uses separately installed `.tmp` environments managed by `scripts/helper_tool.py`; this remains transitional until helper providers move behind managed setup phases.

```bash
python3 scripts/laser_build.py --design shot_coins
python3 scripts/laser_build.py --design shot_coins --dry-run
python3 scripts/laser_build.py --design shot_coins --validate-only
python3 scripts/laser_build.py --design shot_coins --audit-only
python3 scripts/laser_build.py --design shot_coins --quantity 40
python3 scripts/laser_build.py --design shot_coins --new-revision
python3 scripts/laser_build.py --design hug_coins
python3 scripts/laser_build.py --design bwb_merit_badges
```

Normal builds atomically replace `output/<design>/`. Revision builds create immutable `revisions/<design>/rev_000N/` directories. The script generates artifacts only and cannot stream to hardware.

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
