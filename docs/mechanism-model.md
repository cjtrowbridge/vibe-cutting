# Host-Owned Mechanism Model

The mechanism model is the host-owned contract for laser-cut mechanical assemblies. Helper libraries can generate source geometry, but this model owns validation before any design can become a cut job.

## Files

- `schemas/mechanism_part.schema.json` describes gears, racks, cams, ratchets, rotors, linkages, axles, spacers, washers, registration features, and interfaces.
- `schemas/mechanism_graph.schema.json` describes meshes, ratios, phases, channels, stack layers, operations, and helper-geometry provenance.
- `schemas/mechanism_stackup.schema.json` describes layers, material thicknesses, fasteners, bearings, bushings, service layers, and registration IDs.
- `scripts/mechanism_validate.py` validates a mechanism JSON file and emits a deterministic report.

## Command

```bash
setup/bootstrap.sh run -- scripts/mechanism_validate.py designs/example/mechanism.json --output output/example/mechanism-validation.json
```

## Validation Checks

- Gear mesh center distances must match pitch diameters within the configured tolerance.
- Declared ratios must match tooth counts.
- Phase transfers must match declared part phases.
- Backlash, bore clearance, tooth-root estimate, and web thickness must meet minimums.
- Same-layer rotating parts must not collide unless they are declared as a mesh pair.
- Every part must be assigned to a declared stack layer.
- Stack registration IDs must reference registration features.
- Power and logic channel interfaces must use the channel key.
- Duplicate through-cut source paths are rejected as overburn risks.
- Helper geometry must record request hashes and source provenance.

## Job Manifest Fragment

The report includes `job_manifest_fragment` with:

- `mechanism_id`
- `mechanism_validation_passed`
- `mechanism_check_count`

Build integrations should copy this fragment into job manifests once a design uses the mechanism model.

## First Prototype

`designs/primitive_power_extender_laser_0_1/` is the first mechanism-sheet design. It uses the mechanism validator during `scripts/laser_build.py`, writes `mechanism_validation.json` alongside the normal laser artifacts, and records the validation fragment in `job_manifest.json`.

## Boundary

This validator does not generate geometry, toolpaths, or process recipes. It checks the host mechanism contract after helper or native geometry has been declared and before the laser artifact pipeline treats the design as buildable.
