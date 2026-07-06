---
plan_id: YYYY-MM-DD-HH-mm-ss_slug
title: Phase N Title
summary: One-sentence bounded phase outcome.
status: future
created_at: YYYY-MM-DD-HH-mm-ss
---

# Phase N Title

Key: `[ ]` pending task, `[x]` completed task, `[?]` needs validation, `[-]` closed task

## Parent and Phase

- Parent roadmap: `plans/future/...md`
- Phase: `N — Name`
- Parent checklist scope: `[items]`

## Entry Evidence

- Preceding archived child plan:
- Approved preceding acceptance report:
- Required readiness states:
- Required submodule pins:

## Scope

- Exact files to create:
- Exact files to modify:
- Supported platforms:
- Explicit exclusions:
- Network approval boundary:
- Package-manager approval boundary:
- Privilege approval boundary:
- Heavyweight-install approval boundary:

## Execution Plan

- [ ] 1. Atomic workstream.
  - [ ] 1.1 Atomic executable task with one completion condition.

## Verification

- [ ] Positive-path tests:
- [ ] Negative-path tests:
- [ ] Idempotence tests:
- [ ] Isolation and path-confinement tests:
- [ ] Interruption and safe-resume tests:
- [ ] Rollback and prior-state preservation tests:
- [ ] Submodule cleanliness checks:
- [ ] Platform-specific checks:
- [ ] Documentation and index checks:

## Rollback

- Complete prior state to preserve:
- Staging state safe to remove:
- Lock/pin restoration procedure:

## Stop Condition

State the evidence failure that prevents acceptance and downstream work.

## Acceptance Gate

- Acceptance report path:
- Required approver decision:
- Downstream phase prohibited until this plan is archived and its report is approved.
