---
plan_id: 2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack
title: Build Portable Helper-Tool Bootstrap and Mechanism Stack
summary: Build zero-Python host bootstrap tooling, polymorphic helper adapters, and validated Boxes.py, CadQuery/CQ_Gears, BOSL2, and FreeCAD Gears integrations.
status: future
created_at: 2026-07-06-09-17-37
---

# Build Portable Helper-Tool Bootstrap and Mechanism Stack

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Objective

Make a freshly cloned repository self-preparing on supported Debian/Linux, Windows, and macOS hosts when only Git, an agent, and ordinary operating-system tools are initially available. Do not assume Python, Pixi, Conda, OpenSCAD, FreeCAD, or any helper dependency is preinstalled.

All setup entrypoints and implementation belong under `setup/`. Repository-local persistent installations belong under ignored `.tools/`. Runtime design/build entrypoints remain under `scripts/`.

Gearotic is explicitly out of scope.

## Fixed Architecture Decisions

- Native bootstrap entrypoints are `setup/bootstrap.sh` and `setup/bootstrap.ps1`.
- Native launchers must not require Python.
- Bootstrap downloads must be pinned and checksum-verified before execution.
- Do not use remote shell execution patterns such as `curl | sh`.
- Do not install global packages or request administrative privileges by default.
- Any network access, package-manager use, or privileged remediation requires an explicit approval boundary.
- Git is a required host prerequisite used for cloning and submodule operations; bootstrap verifies it but does not install or replace it.
- Use a repository-local environment manager to provision Python and tool environments.
- Treat Pixi as the leading environment-manager candidate because CadQuery favors Conda-style installation and FreeCAD Gears already maintains Pixi configuration; verify platform coverage before final selection.
- After bootstrap, agents and humans invoke managed runtimes through `setup/bootstrap.sh run -- <repo-command>` or `setup/bootstrap.ps1 run -- <repo-command>` rather than relying on a host Python installation.
- Third-party submodules remain unmodified and separately licensed.
- Helper-generated geometry remains untrusted until normalized and validated by vibe-cutting.
- Vibe-cutting owns material bindings, kerf/backlash policy, operation semantics, bounds, ordering, previews, manifests, G-code, audits, and fabrication readiness.

## Phased Delivery

This file is an umbrella roadmap, not authority to implement every workstream in one checkpoint. Keep it in `plans/future/` while decomposing and executing the following phases through bounded child plans. Before each phase begins, create or promote one child plan with only that phase's atomic implementation scope, request approval, execute it, verify its acceptance gate, archive it, and obtain approval before beginning the next phase.

1. **Phase 0 — Contracts and child-plan boundaries:** Complete workstream 1 and approve the architecture, prerequisites, provider boundaries, phase acceptance gates, and child-plan template.
2. **Phase 1 — Native bootstrap and managed base runtime:** Complete workstreams 2–3 so a Git-equipped host can install the repository-local manager and Python runtime, operate submodules with host Git, and invoke repository commands through the managed `run` interface.
3. **Phase 2 — Generalized helper adapter platform:** Complete workstreams 4–5 and verify provider-discriminated schemas, setup providers, provenance, isolation, and failure handling without migrating additional helpers.
4. **Phase 3 — Boxes.py migration:** Complete workstream 6 and prove the existing Boxes.py integration works through the new bootstrap and adapter contracts before removing its disposable setup model.
5. **Phase 4 — CadQuery and CQ_Gears:** Complete workstream 7 and accept only the validated planar gear subset.
6. **Phase 5 — BOSL2 and managed OpenSCAD:** Complete workstream 8 and establish BOSL2 as a comparison or fallback geometry backend.
7. **Phase 6 — FreeCAD Gears inspection:** Complete workstream 9 and establish a repeatable headless inspection backend without granting it fabrication authority.
8. **Phase 7 — Host mechanism model and prototype:** Complete workstreams 10–11 only after the required geometry backends pass their prior phase gates.
9. **Phase 8 — Governance, documentation, and readiness reports:** Complete workstreams 12–13, updating agent-facing policy and human-facing setup documentation to match implemented behavior.
10. **Phase 9 — Cross-platform qualification and rollout:** Complete workstreams 14–16, including clean-host simulations, CI evidence, migration cleanup, and final roadmap reconciliation.

Each phase must define:

- Entry evidence from the preceding phase.
- Exact files and checklist atoms in scope.
- Supported platforms and intentionally deferred platforms.
- Positive, negative, idempotence, isolation, and rollback tests appropriate to the phase.
- An acceptance report containing commands, versions, checksums, lock hashes, submodule states, and known limitations.
- A stop condition that prevents downstream phases from treating partial readiness as fabrication approval.

## Execution Plan

- [x] 1. Define portable host and bootstrap contracts.
  - [x] 1.1 Define the supported OS/architecture matrix for Debian-family Linux, Windows, and macOS.
  - [x] 1.2 Define unsupported-host behavior and required diagnostic output.
  - [x] 1.3 Define the minimum ordinary system capabilities assumed by each native launcher.
  - [x] 1.4 Define repository-local installation roots beneath `.tools/`.
  - [x] 1.5 Add `.tools/` and generated host-readiness reports to `.gitignore`.
  - [x] 1.6 Define approval gates for downloads, operating-system package managers, administrative privileges, and large tool environments.
  - [x] 1.7 Define bootstrap states: `uninitialized`, `manager-ready`, `base-ready`, `tools-partial`, `tools-ready`, and `verified`.
  - [x] 1.8 Define helper readiness states: `registered`, `dependencies-ready`, `invocation-ready`, `output-validated`, `pipeline-integrated`, and `fabrication-approved`.
  - [x] 1.9 Record an architecture decision for the zero-Python bootstrap and polymorphic helper-provider model.
  - [x] 1.10 Define the bounded child-plan template and acceptance gate for each delivery phase.
  - [x] 1.11 Define Git as a verified host prerequisite and document minimum supported versions.
  - [x] 1.12 Define the managed `run` command contract for repository Python scripts and other repo-local commands.

- [x] 2. Create the `setup/` bootstrap surface.
  - [x] 2.1 Create `setup/README.md` with Linux/macOS and Windows bootstrap commands.
  - [x] 2.2 Create `setup/bootstrap.sh` using portable POSIX shell syntax.
  - [x] 2.3 Create `setup/bootstrap.ps1` using Windows PowerShell-compatible syntax.
  - [x] 2.4 Create `setup/toolchain-manifest.json` for pinned bootstrap binaries and platform artifacts.
  - [x] 2.5 Create `setup/checksums/` records for every downloaded bootstrap artifact.
  - [x] 2.6 Create `setup/pixi.toml` for the managed base environment.
  - [x] 2.7 Generate and commit `setup/pixi.lock` for every supported platform.
  - [x] 2.8 Create `setup/bootstrap_host.py` as the managed stage-two orchestrator.
  - [x] 2.9 Implement `doctor`, `setup`, `verify`, `repair`, `report`, and `run` subcommands.
  - [x] 2.10 Make the native launchers locate or download the pinned environment manager.
  - [x] 2.11 Verify downloaded artifacts before extraction or execution.
  - [x] 2.12 Make bootstrap operations idempotent and resumable after interruption.
  - [x] 2.13 Prevent setup from writing inside third-party submodules.
  - [x] 2.14 Prevent setup from writing outside the repository unless a separately approved remediation requires it.
  - [x] 2.15 Produce actionable remediation instead of silently invoking privileged system package managers.
  - [x] 2.16 Make `run` dispatch Python scripts through the pinned managed Python runtime without consulting host Python.
  - [x] 2.17 Preserve command arguments, exit status, standard output, standard error, and interrupt behavior through `run`.

- [x] 3. Provision the managed base environment.
  - [x] 3.1 Verify host Git exists and satisfies the documented minimum version.
  - [x] 3.2 Provision a pinned Python runtime for bootstrap orchestration and host tests.
  - [x] 3.3 Provision JSON, archive, checksum, and process-inspection utilities required by setup.
  - [x] 3.4 Initialize and update all submodules recursively through the verified host Git executable.
  - [x] 3.5 Verify each submodule path and gitlink revision against `.gitmodules` and adapter manifests.
  - [x] 3.6 Detect dirty, missing, uninitialized, or mismatched submodules and fail closed.
  - [x] 3.7 Record base-environment versions and lock hashes in the host-readiness report.
  - [x] 3.8 Record the verified host Git path and version in the host-readiness report.
  - [x] 3.9 Prove `run` can invoke `scripts/laser_build.py --help` with managed Python while host Python is unavailable.

- [x] 4. Generalize the helper adapter model.
  - [x] 4.1 Replace the Python-only helper schema with provider-discriminated adapter schemas.
  - [x] 4.2 Support `pixi_environment`, `openscad_library`, `system_application`, and `manual_operator` providers.
  - [x] 4.3 Define one common adapter identity, capability, routing, source, license, platform, safety, and readiness contract.
  - [x] 4.4 Add provider-specific setup, invocation, version, and environment fields.
  - [x] 4.5 Add typed helper request and helper result schemas.
  - [x] 4.6 Add environment-fingerprint and provenance schemas.
  - [x] 4.7 Replace arbitrary argument forwarding with typed tool-specific request drivers.
  - [x] 4.8 Enforce repository-relative input and output paths.
  - [x] 4.9 Enforce declared output formats and exact output inventories.
  - [x] 4.10 Record source pins, lock hashes, runtime versions, resolved packages, request hashes, and output hashes.
  - [x] 4.11 Detect source-submodule mutation after every setup and invocation.
  - [x] 4.12 Preserve previous authoritative outputs on every helper failure.
  - [x] 4.13 Keep `scripts/helper_tool.py` as the operational dispatcher after setup has provisioned its runtime.
  - [x] 4.14 Move all provisioning providers and setup-specific tool drivers under `setup/providers/` and `setup/tools/`.

- [x] 5. Implement common setup providers.
  - [x] 5.1 Create `setup/providers/pixi.py`.
  - [x] 5.2 Create `setup/providers/openscad.py`.
  - [x] 5.3 Create `setup/providers/system_application.py`.
  - [x] 5.4 Implement platform and architecture compatibility checks.
  - [x] 5.5 Implement environment creation into fingerprinted `.tools/environments/<tool>/` directories.
  - [x] 5.6 Implement lock-change and source-pin invalidation.
  - [x] 5.7 Implement isolated cache and temporary-directory handling.
  - [x] 5.8 Implement install logs and failure evidence without recording credentials or secrets.
  - [x] 5.9 Implement provider-level smoke-test hooks.
  - [x] 5.10 Implement provider-level cleanup of incomplete staged environments.

- [ ] 6. Migrate and harden the Boxes.py integration.
  - [ ] 6.1 Convert `tool_adapters/boxes.json` to the generalized schema.
  - [ ] 6.2 Create a locked repository-local Boxes.py environment.
  - [ ] 6.3 Create a typed Boxes.py generation-request schema.
  - [ ] 6.4 Create `setup/tools/boxes.py` for setup and smoke testing.
  - [ ] 6.5 Create an operational Boxes.py adapter driver for typed generation.
  - [ ] 6.6 Preserve YAML multi-generator mode for reproducible SVG generation.
  - [ ] 6.7 Enforce SVG-only authoritative source output.
  - [ ] 6.8 Enforce declared operation-color mappings and reject unknown fabrication colors.
  - [ ] 6.9 Enforce calibrated thickness and single-owner burn compensation.
  - [ ] 6.10 Add setup, readiness, deterministic-output, path-safety, mutation, and malformed-output tests.
  - [ ] 6.11 Remove the superseded `.tmp/helper-tools/boxes` setup model after migration validation.

- [ ] 7. Integrate CadQuery and CQ_Gears as one tool stack.
  - [ ] 7.1 Verify compatible CadQuery, CQ_Gears, Python, OCP, and platform versions.
  - [ ] 7.2 Select and document the supported Python version, using Python 3.12 as the initial compatibility candidate.
  - [ ] 7.3 Create one locked Pixi environment from the local CadQuery and CQ_Gears submodules.
  - [ ] 7.4 Prevent package resolution from replacing the pinned local CadQuery or CQ_Gears sources.
  - [ ] 7.5 Create a combined `cq_gears` adapter manifest referencing both submodule pins.
  - [ ] 7.6 Create typed schemas for spur gears, ring gears, racks, and planetary reference assemblies.
  - [ ] 7.7 Define module, tooth count, pressure angle, width, bore, addendum, dedendum, and backlash fields.
  - [ ] 7.8 Create `setup/tools/cq_gears.py` for setup and smoke testing.
  - [ ] 7.9 Create an operational CQ_Gears generation driver.
  - [ ] 7.10 Export raw STEP geometry for provenance and engineering inspection.
  - [ ] 7.11 Extract or project normalized two-dimensional profiles for laser operations.
  - [ ] 7.12 Reject helical, herringbone, bevel, worm, or other non-planar fabrication requests until separately validated.
  - [ ] 7.13 Add deterministic golden fixtures for a spur gear, ring gear, rack, and meshing pair.
  - [ ] 7.14 Add geometry checks for pitch diameter, root diameter, outside diameter, center distance, tooth count, bore, and profile closure.

- [ ] 8. Integrate BOSL2 as an OpenSCAD library provider.
  - [ ] 8.1 Convert the BOSL2 submodule pin and version into an adapter manifest.
  - [ ] 8.2 Verify OpenSCAD acquisition or discovery on each supported platform.
  - [ ] 8.3 Configure `OPENSCADPATH` per invocation without changing user-global configuration.
  - [ ] 8.4 Create `setup/tools/bosl2.py` for dependency and include-path validation.
  - [ ] 8.5 Create a pinned host OpenSCAD adapter source for `BOSL2/gears.scad`.
  - [ ] 8.6 Create typed BOSL2 gear request schemas aligned with the supported planar subset.
  - [ ] 8.7 Export deterministic SVG profiles through the existing OpenSCAD boundary.
  - [ ] 8.8 Add golden spur-gear, ring-gear, and rack fixtures.
  - [ ] 8.9 Compare BOSL2 and CQ_Gears pitch geometry without requiring byte-identical profiles.
  - [ ] 8.10 Document BOSL2 as fallback/experimental geometry rather than the mechanism validator.

- [ ] 9. Integrate FreeCAD Gears as an inspection backend.
  - [ ] 9.1 Create a FreeCAD Gears adapter manifest referencing its submodule pin and GPL license.
  - [ ] 9.2 Create a host-owned Pixi environment or validated use of the upstream Pixi lock.
  - [ ] 9.3 Provision FreeCAD and FreeCAD Gears without requiring a preinstalled system application.
  - [ ] 9.4 Use isolated FreeCAD user, cache, and configuration directories.
  - [ ] 9.5 Create `setup/tools/freecad_gears.py` for setup and headless smoke testing.
  - [ ] 9.6 Detect and verify `FreeCADCmd` inside the managed environment.
  - [ ] 9.7 Generate one headless involute-gear inspection artifact.
  - [ ] 9.8 Verify deterministic STEP/DXF or other approved comparison output.
  - [ ] 9.9 Keep FreeCAD Gears at `output-validated` inspection status until repeatable headless export passes on supported platforms.
  - [ ] 9.10 Prohibit FreeCAD-generated toolpaths from becoming authoritative G-code.

- [ ] 10. Build the host-owned laser mechanism model.
  - [ ] 10.1 Create schemas for gears, racks, cams, ratchets, rotors, linkages, axles, spacers, washers, registration features, and interfaces.
  - [ ] 10.2 Create a mechanism-graph schema for parts, meshes, ratios, phase relationships, channels, and stack layers.
  - [ ] 10.3 Create a stackup schema for sheet thicknesses, spacers, fasteners, bearings, bushings, and service layers.
  - [ ] 10.4 Implement gear mesh-distance validation.
  - [ ] 10.5 Implement declared-ratio validation.
  - [ ] 10.6 Implement phase-relationship validation.
  - [ ] 10.7 Implement minimum-backlash validation.
  - [ ] 10.8 Implement bore, axle, bearing, and bushing clearance validation.
  - [ ] 10.9 Implement minimum tooth-root and web-thickness validation.
  - [ ] 10.10 Implement plan-view rotating-part collision checks.
  - [ ] 10.11 Implement stack-layer and registration-hole completeness checks.
  - [ ] 10.12 Implement power-channel and logic-channel keying checks.
  - [ ] 10.13 Implement duplicate-path and shared-edge overburn checks.
  - [ ] 10.14 Archive raw helper geometry with normalized host operations.
  - [ ] 10.15 Record every mechanism validation result in the job manifest.

- [ ] 11. Prototype the first laser-native mechanism.
  - [ ] 11.1 Create `primitive_power_extender_laser_0_1`.
  - [ ] 11.2 Define one input rotor and one output rotor.
  - [ ] 11.3 Define fixed 1:1 ratio and phase transfer.
  - [ ] 11.4 Define laminated layers, axles, spacers, registration, and service fasteners.
  - [ ] 11.5 Generate primary profiles with CQ_Gears.
  - [ ] 11.6 Generate a BOSL2 comparison profile.
  - [ ] 11.7 Validate ratio, phase, clearance, collisions, bounds, and operation ordering.
  - [ ] 11.8 Generate SVG, PNG preview, operations, setup documentation, manifests, and calibration-only G-code through vibe-cutting.
  - [ ] 11.9 Add deterministic revision and audit tests.

- [ ] 12. Add agent governance and human documentation.
  - [ ] 12.1 Update `AGENTS.md` with bootstrap-first startup and helper-routing rules.
  - [ ] 12.2 Update `README.md` with zero-Python Linux/macOS and Windows quick starts.
  - [ ] 12.3 Add `docs/host-bootstrap.md`.
  - [ ] 12.4 Add `docs/toolchain-support-matrix.md`.
  - [ ] 12.5 Expand `docs/helper-tools.md` for provider types and readiness states.
  - [ ] 12.6 Add or update `docs/tools/boxes.md`.
  - [ ] 12.7 Add `docs/tools/cq-gears.md`.
  - [ ] 12.8 Add `docs/tools/bosl2.md`.
  - [ ] 12.9 Add `docs/tools/freecad-gears.md`.
  - [ ] 12.10 Add `docs/mechanism-model.md`.
  - [ ] 12.11 Add `docs/mechanism-validation.md`.
  - [ ] 12.12 Add `references/helper-runtime-providers.md`.
  - [ ] 12.13 Add `references/mechanism-validation-contract.md`.
  - [ ] 12.14 Update `references/helper-tool-contract.md`.
  - [ ] 12.15 Update `references/geometry-backend-selection.md`.
  - [ ] 12.16 Add `playbooks/how_to_bootstrap_a_fabrication_host.md`.
  - [ ] 12.17 Update `playbooks/how_to_add_and_validate_a_helper_tool.md`.
  - [ ] 12.18 Update `playbooks/how_to_use_boxes_for_laser_geometry.md`.
  - [ ] 12.19 Add `playbooks/how_to_use_cq_gears_for_laser_mechanisms.md`.
  - [ ] 12.20 Add `playbooks/how_to_use_bosl2_gear_geometry.md`.
  - [ ] 12.21 Add `playbooks/how_to_use_freecad_gears_for_inspection.md`.
  - [ ] 12.22 Add `playbooks/how_to_author_and_validate_laser_mechanisms.md`.
  - [ ] 12.23 Update all playbook and reference indexes.

- [ ] 13. Create host-readiness reports.
  - [ ] 13.1 Define a machine-readable host-readiness JSON schema.
  - [ ] 13.2 Define a human-readable host-readiness Markdown template.
  - [ ] 13.3 Record OS, architecture, bootstrap state, and supported-platform classification.
  - [ ] 13.4 Record environment-manager binary version and checksum.
  - [ ] 13.5 Record base and tool lock hashes.
  - [ ] 13.6 Record submodule pins and cleanliness.
  - [ ] 13.7 Record runtime, executable, and resolved dependency versions.
  - [ ] 13.8 Record smoke-test and deterministic-output results.
  - [ ] 13.9 Record blocked capabilities and exact remediation.
  - [ ] 13.10 Exclude secrets, tokens, usernames, and unrelated host data.

- [ ] 14. Test portable bootstrap behavior.
  - [ ] 14.1 Run bootstrap from an alternate empty `.tools` root on the development host.
  - [ ] 14.2 Run a clean-host simulation that retains Git and the native shell but masks host Python, Pixi, Conda, OpenSCAD, FreeCAD, and helper executables.
  - [ ] 14.3 Prove native bootstrap reaches the managed runtime without using system Python.
  - [ ] 14.4 Prove bootstrap initializes every submodule using verified host Git.
  - [ ] 14.5 Prove the managed `run` interface invokes `scripts/laser_build.py`, preserves arguments and exit codes, and never resolves host Python.
  - [ ] 14.6 Prove `doctor` reports a missing or unsupported Git installation with exact remediation and performs no downloads.
  - [ ] 14.7 Prove repeated setup is idempotent.
  - [ ] 14.8 Simulate missing download tools and verify actionable failure.
  - [ ] 14.9 Simulate checksum mismatch and verify refusal to execute.
  - [ ] 14.10 Simulate interrupted environment creation and verify safe resume.
  - [ ] 14.11 Simulate unsupported OS/architecture and verify explicit refusal.
  - [ ] 14.12 Verify setup does not require root/administrator access for the supported path.
  - [ ] 14.13 Verify no global Python, package, OpenSCAD, or FreeCAD state is modified.
  - [ ] 14.14 Verify setup writes only to declared repository-local paths.
  - [ ] 14.15 Verify all third-party submodules remain clean after success, failure, repair, and interruption tests.
  - [ ] 14.16 Run Boxes.py deterministic smoke tests.
  - [ ] 14.17 Run CQ_Gears deterministic and geometry smoke tests.
  - [ ] 14.18 Run BOSL2/OpenSCAD deterministic and geometry smoke tests.
  - [ ] 14.19 Run FreeCAD Gears headless inspection smoke tests where supported.
  - [ ] 14.20 Run the complete host unit and integration test suites.

- [ ] 15. Add cross-platform verification.
  - [ ] 15.1 Add Linux bootstrap CI coverage.
  - [ ] 15.2 Add Windows PowerShell bootstrap CI coverage.
  - [ ] 15.3 Add macOS bootstrap CI coverage.
  - [ ] 15.4 Cache only checksum-validated downloads and lock-addressed environments.
  - [ ] 15.5 Keep heavyweight FreeCAD tests optional when runner limits prevent full execution.
  - [ ] 15.6 Publish support-matrix evidence from CI without claiming untested fabrication readiness.

- [ ] 16. Complete migration and rollout.
  - [ ] 16.1 Remove obsolete Python-first setup instructions.
  - [ ] 16.2 Remove or migrate disposable helper environments created under `.tmp/helper-tools/`.
  - [ ] 16.3 Verify every setup command in documentation from a clean bootstrap root.
  - [ ] 16.4 Verify every helper manifest against its schema.
  - [ ] 16.5 Verify every playbook references existing scripts, schemas, docs, and templates.
  - [ ] 16.6 Review third-party license notices and distribution boundaries.
  - [ ] 16.7 Review all diffs and nested submodule states.
  - [ ] 16.8 Update the active implementation plan and roadmap to match delivered scope.
  - [ ] 16.9 Record completed checkpoints in the journal.
  - [ ] 16.10 Archive completed bounded implementation plans and refresh plan indexes.
  - [ ] 16.11 Commit and push each approved completed checkpoint.
  - [ ] 16.12 Verify every phase has an archived child plan and accepted evidence report.
  - [ ] 16.13 Verify no downstream phase was accepted using an upstream capability below its required readiness state.

## Verification Objective

The plan is complete when a supported host with Git but no preinstalled Python, Pixi, Conda, OpenSCAD, FreeCAD, or helper dependencies can use only `setup/bootstrap.sh` or `setup/bootstrap.ps1` plus approved network access to:

1. Provision the repository-local bootstrap runtime.
2. Initialize pinned submodules through verified host Git.
3. Invoke `scripts/laser_build.py` and other repository commands through the managed `run` interface without host Python.
4. Create locked helper environments.
5. Verify Boxes.py, CQ_Gears, BOSL2, and supported FreeCAD Gears capabilities.
6. Produce a complete host-readiness report.
7. Generate and validate the first laser-native mechanism through vibe-cutting without global installations, dirty submodules, unsafe fallback, or bypassing the host fabrication pipeline.
