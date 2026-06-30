# Build Script Reference

Requires Python 3.11 or newer and no third-party Python packages.

```bash
python3 scripts/laser_build.py --design shot_coins
python3 scripts/laser_build.py --design shot_coins --dry-run
python3 scripts/laser_build.py --design shot_coins --validate-only
python3 scripts/laser_build.py --design shot_coins --audit-only
python3 scripts/laser_build.py --design shot_coins --quantity 40
python3 scripts/laser_build.py --design shot_coins --new-revision
```

Normal builds atomically replace `output/<design>/`. Revision builds create immutable `revisions/<design>/rev_000N/` directories. The script generates artifacts only and cannot stream to hardware.

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
- Raster engraving, DXF, OpenSCAD import, hardware streaming, and arbitrary nesting remain roadmap work.
- The generated Falcon/basswood job is calibration-only.
