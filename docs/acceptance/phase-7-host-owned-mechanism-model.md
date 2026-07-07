# Phase 7 Acceptance: Host-Owned Mechanism Model

## Result

Accepted.

## Scope

- Added host-owned schemas for mechanism parts, graphs, and stackups.
- Added `scripts/mechanism_validate.py` as a deterministic validation/report CLI.
- Implemented checks for gear mesh distance, declared ratio, phase transfer, backlash, bore/axle clearance, tooth-root estimate, web thickness, rotating-part collisions, stack layers, registration features, channel keying, duplicate cut paths, and helper provenance.
- Added a `job_manifest_fragment` to validation reports for later build integration.
- Documented the mechanism boundary in `docs/mechanism-model.md`, `docs/architecture.md`, `README.md`, and `AGENTS.md`.

## Evidence

```bash
python3 -m py_compile scripts/mechanism_validate.py
python3 -m unittest tests.test_mechanism_validate -v
```

## Boundary

- The validator does not generate geometry, G-code, or recipes.
- Helper geometry remains untrusted until represented in the host-owned mechanism model and validated.
- Build-pipeline job-manifest insertion is exposed as a fragment and will be wired into concrete mechanism designs in a later phase.
