---
plan_id: 2026-07-06-08-17-15_create-helper-tool-adapter-system
title: Create Helper Tool Adapter System
summary: Create a reusable helper-tool foundation, add Boxes.py support, and pin the initial mechanical-geometry helper repositories for later integration.
status: past
created_at: 2026-07-06-08-17-15
---

# Create Helper Tool Adapter System

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

- [x] 1. Define the reusable helper-tool contract.
  - [x] 1.1 Add a machine-readable helper-tool schema.
  - [x] 1.2 Add a Boxes.py adapter manifest with identity, pin, invocation, capabilities, outputs, and license metadata.
  - [x] 1.3 Add reusable helper-tool and geometry-backend selection references.

- [x] 2. Implement the generic helper-tool runner.
  - [x] 2.1 Add manifest discovery and validation.
  - [x] 2.2 Add tool listing and readiness inspection.
  - [x] 2.3 Add isolated environment setup with explicit dependency installation.
  - [x] 2.4 Add subprocess-only invocation with pin, path, and environment checks.
  - [x] 2.5 Add diagnostic logging and actionable failure messages.

- [x] 3. Verify the helper-tool runner.
  - [x] 3.1 Add unit tests for manifest loading, pin checks, command construction, path safety, and readiness.
  - [x] 3.2 Verify the Boxes.py adapter against the pinned submodule.
  - [x] 3.3 Verify unavailable dependencies fail closed without modifying the submodule.
  - [x] 3.4 Run the focused and full host test suites.

- [x] 4. Add helper-tool playbooks.
  - [x] 4.1 Add a generic playbook for adding and validating helper tools.
  - [x] 4.2 Add a Boxes.py geometry-authoring playbook.
  - [x] 4.3 Update new-design workflow with mandatory backend selection.
  - [x] 4.4 Update build-and-audit workflow with helper-tool provenance checks.

- [x] 5. Synchronize governance and documentation.
  - [x] 5.1 Update `AGENTS.md` with tool classes, routing rules, commands, and playbook index.
  - [x] 5.2 Update `README.md` with human-facing setup and helper-tool usage.
  - [x] 5.3 Add generic helper-tool architecture documentation.
  - [x] 5.4 Add Boxes.py-specific integration documentation.
  - [x] 5.5 Update architecture and build-script documentation.
  - [x] 5.6 Update the portable-framework roadmap with the generalized helper-tool model.

- [x] 6. Add mechanical-geometry helper source repositories.
  - [x] 6.1 Add CadQuery at `third_party/cadquery`.
  - [x] 6.2 Add CQ_Gears at `third_party/cq_gears`.
  - [x] 6.3 Add BOSL2 at `third_party/bosl2`.
  - [x] 6.4 Add FreeCAD Gears at `third_party/freecad-gears`.
  - [x] 6.5 Record pinned revisions, licenses, and clean nested states.
  - [x] 6.6 Exclude Gearotic from repository and integration planning.
  - [x] 6.7 Propose the remaining polymorphic-adapter and mechanism-integration plan without implementing it.

- [x] 7. Complete repository governance.
  - [x] 7.1 Review helper-runner diffs, links, commands, and generated indexes.
  - [x] 7.2 Review added submodules and the final combined diff.
  - [x] 7.3 Record the checkpoint in today’s journal after user approval.
  - [x] 7.4 Archive the completed plan and refresh plan indexes.
  - [x] 7.5 Commit and push the approved checkpoint.

## Added Submodule Evidence

- `third_party/cadquery`: `f69500e54640a3da8fcee9d063a5a1f996d63263`; Apache-2.0; clean `master`.
- `third_party/cq_gears`: `e73874cf17a25447a99b1e7c22a4d5af38560e9c`; Apache-2.0; clean `main`.
- `third_party/bosl2`: `fbcdfdd511b6abfde93c43c8f85c2bd24ee7a02d`; BSD-2-Clause; clean `master`; BOSL2 `2.0.747`.
- `third_party/freecad-gears`: `d55e8e3d21208e052379a8451507fb4a727ae292`; GPL-3.0; clean `master`.
- Gearotic is intentionally excluded.
