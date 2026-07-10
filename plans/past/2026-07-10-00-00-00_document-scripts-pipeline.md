---
plan_id: 2026-07-10-00-00-00_document-scripts-pipeline
title: "Document Scripts Pipeline"
summary: "Add verbose scripts-folder documentation for humans and agents explaining script responsibilities, safe invocation, and how to run the laser pipeline end to end."
status: past
created_at: 2026-07-10-00-00-00
---

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

### Plan

**Phase 1: Discovery**

- `[x]` Inventory scripts in `scripts/` and identify their operator-facing responsibilities.
- `[x]` Review existing build, helper, mechanism, and plan-index documentation to avoid contradictions.
- `[x]` Identify safe command paths for Linux/macOS shell and Windows PowerShell.

**Phase 2: Documentation**

- `[x]` Add verbose `scripts/README.md` documentation for humans and agents.
- `[x]` Explain how to run setup, validate-only, dry-run, normal build, audit-only, revision build, helper checks, mechanism validation, host readiness reporting, and plan index regeneration.
- `[x]` Document expected output artifacts, including operation G-code plus transparent PNG and cut SVG sidecars.
- `[x]` Document safety boundaries: scripts generate and audit artifacts but do not stream to hardware.
- `[x]` Document agent-specific operating rules for using managed bootstrap, preserving generated artifacts, and avoiding direct helper imports.
- `[x]` Cross-link the scripts documentation from existing build reference documentation.

**Phase 3: Verification**

- `[x]` Check documentation paths and commands for consistency with existing files.
- `[x]` Run plan index regeneration after creating this plan.
- `[x]` Run `git diff --check`.
