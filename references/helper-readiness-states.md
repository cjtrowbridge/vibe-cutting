# Reference: Helper Readiness States

## Purpose

Define evidence-bearing bootstrap and helper states. A state is a verified claim, not a progress label. Missing, stale, or contradictory evidence invalidates the state and fails closed.

## Bootstrap States

| State | Required evidence | Allowed next states |
| --- | --- | --- |
| `uninitialized` | Repository and host Git are inspectable; no valid manager evidence exists | `manager-ready` |
| `manager-ready` | Pinned manager exists beneath `.tools/bin/`; artifact checksum and platform match | `base-ready`, `uninitialized` |
| `base-ready` | Locked base environment exists; managed Python and stage-two smoke tests pass | `tools-partial`, `tools-ready`, `manager-ready` |
| `tools-partial` | Base is ready and at least one requested helper is blocked or below its requested state | `tools-ready`, `base-ready` |
| `tools-ready` | Every requested helper has reached its requested non-fabrication readiness state | `verified`, `tools-partial`, `base-ready` |
| `verified` | Host report, submodule checks, provider smoke tests, and requested integration tests pass | `tools-partial`, `base-ready`, `manager-ready`, `uninitialized` |

State may move backward whenever its evidence is invalidated. `repair` may reconstruct evidence but may not skip a transition or reuse stale evidence.

## Helper States

| State | Required evidence | Permitted use |
| --- | --- | --- |
| `registered` | Valid adapter, source path, source pin, license metadata, platform declaration, and typed capabilities | Routing and planning only |
| `dependencies-ready` | Provider environment matches source pin, lock, adapter fingerprint, platform, and runtime smoke test | Provider diagnostics only |
| `invocation-ready` | Typed request driver, path confinement, source-cleanliness checks, and invocation smoke test pass | Controlled test invocation |
| `output-validated` | Declared output inventory, parser, hashes, deterministic fixture, and geometry validation pass | Geometry comparison and untrusted pipeline input |
| `pipeline-integrated` | Host operation mapping, bounds, provenance, staging, manifest, and audit tests pass | Host-controlled artifact generation |
| `fabrication-approved` | Machine/material calibration, operation ordering, safety review, and fabrication-specific acceptance are approved | The explicitly approved machine/material/job scope only |

Readiness is capability-specific. A helper may be `output-validated` for planar spur gears and only `registered` for helical gears. The report must not collapse these into one broader claim.

## Invalidation Triggers

Invalidate the affected state and every downstream state when any of these change:

- Submodule revision, cleanliness, URL, or license evidence.
- Adapter manifest or typed request/result schema.
- Environment lock, resolved package set, runtime, provider, or manager.
- Invocation driver, parser, normalizer, validator, or golden fixture.
- Machine profile, material profile, kerf/backlash policy, or calibration evidence.
- Host platform, architecture, or native prerequisite used by the evidence.

An interrupted setup, incomplete staged environment, missing report field, hash mismatch, or conflicting state record is invalid evidence.

## Authority Boundaries

- `registered` through `invocation-ready` cannot supply geometry to an authoritative build.
- `output-validated` permits comparison or ingestion only through host normalization and validation.
- `pipeline-integrated` does not permit fabrication G-code unless the relevant machine/material scope is separately `fabrication-approved`.
- No helper-generated G-code, recipe, or readiness claim overrides the host pipeline.
- A state accepted on one platform, helper capability, machine, material, or thickness does not apply to another.
