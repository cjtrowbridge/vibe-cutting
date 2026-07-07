# Reference: Mechanism Validation Contract

## Purpose

Define how agents represent and validate laser-native mechanisms before generating fabrication artifacts.

## Required Inputs

- A mechanism graph matching `schemas/mechanism_graph.schema.json`.
- Parts matching `schemas/mechanism_part.schema.json`.
- A stackup matching `schemas/mechanism_stackup.schema.json`.
- Helper-geometry provenance when a helper influenced any profile.

## Required Checks

Agents must run `scripts/mechanism_validate.py` and require a passing report before a mechanism design is considered buildable. The report must be preserved in the artifact set for `mechanism_sheet` builds.

## Authority Boundary

The mechanism validator owns logical and geometric consistency checks. It does not own:

- Helper installation or routing.
- Machine/material recipes.
- Physical fabrication readiness.
- G-code streaming.
- Empirical fit or strength approval.

## Failure Rule

If any check fails, stop and fix the mechanism graph or design parameters. Do not bypass validation by removing parts, meshes, helper provenance, or operations from the graph.
