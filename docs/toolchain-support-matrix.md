# Toolchain Support Matrix

| Capability | Provider | Linux x86-64 | Other Supported Pixi Platforms | Fabrication Authority |
|---|---|---:|---:|---:|
| Managed Python runtime | `setup/bootstrap.*` | Verified | Pending clean-host evidence | No |
| Native laser build | `scripts/laser_build.py` | Verified | Pending clean-host evidence | Calibration-only artifacts |
| Boxes.py | `boxes` | Verified | Pending clean-host evidence | No |
| CadQuery + CQ_Gears | `cq_gears` | Verified | Pending clean-host evidence | No |
| BOSL2 + OpenSCAD | `bosl2` | Verified when OpenSCAD is present | Pending OpenSCAD evidence | No |
| FreeCAD Gears | `freecad_gears` | Verified inspection smoke | Optional/heavyweight pending | No |
| LaserGRBL | External operator app | Reference only | Windows application | Manual streaming only |

## Platform Notes

- Pixi lock coverage includes Linux, Windows, and macOS targets, but clean-host verification is recorded separately.
- FreeCAD is heavyweight; CI or local hosts may skip its smoke test when runner limits prevent setup.
- OpenSCAD may be discovered as a system executable until a managed acquisition path is added.
- No helper currently has `fabrication-approved` readiness.

## Evidence Locations

- `docs/acceptance/` records phase acceptance reports.
- `.tools/reports/host-readiness/` records local bootstrap reports.
- `scripts/host_readiness_report.py` writes `host-readiness-full.json` and `host-readiness-full.md`.
- `tool_adapters/*.json` records source pins, provider kinds, safety boundaries, and readiness states.
- `.github/workflows/cross-platform-bootstrap.yml` runs Linux, Windows, and macOS bootstrap verification and uploads host-readiness reports as CI artifacts.
- `docs/ci-verification.md` defines the CI checks, cache policy, optional heavyweight helpers, and evidence caveats.

## CI Evidence Policy

- A platform is only treated as CI-verified after a successful workflow run uploads its host-readiness artifact.
- CI cache contents are keyed by platform, checksums, and lock files, then revalidated by bootstrap before use.
- FreeCAD and other heavyweight helper checks are opt-in and non-blocking by default.
- CI readiness never implies fabrication approval; machine/material validation remains design-specific and operator-controlled.
