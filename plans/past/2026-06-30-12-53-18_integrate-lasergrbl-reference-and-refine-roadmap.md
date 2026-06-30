---
plan_id: 2026-06-30-12-53-18_integrate-lasergrbl-reference-and-refine-roadmap
title: Integrate LaserGRBL Reference and Refine Roadmap
summary: Add LaserGRBL as a reference submodule and make the fabrication-framework roadmap implementation-ready across code, playbooks, references, and documentation.
status: past
created_at: 2026-06-30-12-53-18
---

# Integrate LaserGRBL Reference and Refine Roadmap

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

- [x] 1. Integrate the LaserGRBL reference repository.
  - [x] 1.1 Add `arkypita/LaserGRBL` at `third_party/lasergrbl`.
  - [x] 1.2 Initialize the submodule and record its pinned revision.
  - [x] 1.3 Inspect its G-code generation, raster, SVG, GRBL, streaming, configuration, alarm, and preview implementation boundaries.
  - [x] 1.4 Add the reference submodule to host agent-facing repository guidance.

- [x] 2. Refine the future framework roadmap.
  - [x] 2.1 Add local source-reference roles for `vibe-modeling` and LaserGRBL.
  - [x] 2.2 Reconcile canonical artifacts, LaserGRBL handoff, and direct-streaming boundaries.
  - [x] 2.3 Enumerate every required playbook with its objective, prerequisites, procedure, verification, and failure behavior.
  - [x] 2.4 Enumerate every required architecture, schema, safety, machine, material, design, operator, and contributor document.
  - [x] 2.5 Decompose documentation and playbook work into atomic checklist items.
  - [x] 2.6 Add documentation consistency and index-maintenance requirements.

- [x] 3. Verify the checkpoint.
  - [x] 3.1 Validate submodule status and clean nested worktree state.
  - [x] 3.2 Regenerate and check host plan indexes.
  - [x] 3.3 Review the roadmap for unresolved placeholders and unrepresented deliverables.
  - [x] 3.4 Review the complete host diff and pending downtime reports.
