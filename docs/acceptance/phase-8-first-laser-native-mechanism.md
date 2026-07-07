# Phase 8 Acceptance: First Laser-Native Mechanism

## Result

Accepted.

## Scope

- Added `mechanism_sheet` support to `scripts/laser_build.py`.
- Added `primitive_power_extender_laser_0_1` as the first mechanism design.
- Validated a two-gear 1:1 input/output rotor mechanism through `scripts/mechanism_validate.py`.
- Generated host-owned cut profiles, engraving labels, PNG preview, GRBL, setup notes, operations CSV, job manifest, build manifest, and mechanism validation report.
- Generated CQ_Gears primary provenance and BOSL2 comparison provenance from pinned helper requests.

## Evidence

```bash
python3 scripts/mechanism_validate.py designs/primitive_power_extender_laser_0_1/mechanisms/primitive_power_extender.mechanism.json --output .tmp/primitive_power_extender/mechanism-validation.json
python3 scripts/laser_build.py --design primitive_power_extender_laser_0_1
python3 scripts/laser_build.py --audit-only --design primitive_power_extender_laser_0_1
setup/bootstrap.sh run -- setup/tools/cq_gears.py run --manifest tool_adapters/cq_gears.json designs/primitive_power_extender_laser_0_1/helper_requests/cq_gears_primary.request.json
setup/bootstrap.sh run -- setup/tools/bosl2.py run --manifest tool_adapters/bosl2.json designs/primitive_power_extender_laser_0_1/helper_requests/bosl2_comparison.request.json
python3 -m unittest tests.test_laser_build tests.test_mechanism_validate -v
```

## Artifact Evidence

- Output directory: `output/primitive_power_extender_laser_0_1`
- Artifact count: `8`
- `design.svg`: `b105d1887624de3bb0e1431ffa9dbdf8cf263414aa855e0cea6e45aea1bcaa10`
- `job.gcode`: `79a13547685b82b7ba096642e4d0c26a6c0041d3521831099b7d735cec31c59f`
- `job_manifest.json`: `fcb618f4d73e1aa093f8956ba7611eeb2209dd1266ac8d45b3502991ca92ef38`
- `mechanism_validation.json`: `bcd89b33ce6791fc96d1f23a9fec3f3970346e08df9b79d56a078e21da437c54`
- CQ_Gears primary SVG: `ef427ebc9f06ad4251174ff520c7376f5437edbd821f07a2087d400d86dfb092`
- BOSL2 comparison SVG: `1e8ed7e0e9f4333cb522fecbb274004ee20e8e105c314db1ca51e14940c3effc`

## Boundary

- The generated G-code remains `calibration_only`.
- The current laser gear outline is host-owned prototype geometry, not a physically validated power-transmission profile.
- CQ_Gears and BOSL2 outputs are provenance/comparison artifacts and do not own machine artifacts.
