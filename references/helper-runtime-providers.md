# Reference: Helper Runtime Providers

## Purpose

Helper runtime providers describe how a callable helper is prepared and invoked without making that helper part of the host codebase. Provider adapters are schema-version `2` manifests. Boxes.py is the first migrated provider helper.

## Provider Types

- `pixi_environment`: A repository-local Pixi environment for Python/CAD tools that need Conda-style dependency solving.
- `openscad_library`: A pinned OpenSCAD library or executable binding used to generate or inspect geometry through OpenSCAD.
- `system_application`: A locally installed application that cannot be vendored or installed automatically; setup reports exact remediation instead of using privileged installers.
- `manual_operator`: A human-operated tool that can produce reference evidence but cannot claim automated fabrication readiness.

## Provider Readiness

Readiness states are evidence-bearing and cumulative only when the provider proves each layer:

- `registered`: Manifest, source pin, license, provider kind, roots, and safety contract validate.
- `dependencies-ready`: Required local environment or application dependencies are present and fingerprinted.
- `invocation-ready`: A typed request can invoke the provider without path escapes or undeclared side effects.
- `output-validated`: Declared output inventory, formats, hashes, and semantic mappings validate.
- `pipeline-integrated`: Host import/normalization into semantic operations is tested.
- `fabrication-approved`: Physical process evidence exists; Phase 2 provider manifests must not claim this state.

## Agent Routing Rules

1. Prefer native geometry when it fully satisfies the design.
2. Select helpers only by declared capabilities and `use_for`/`avoid_for` guidance.
3. Validate provider manifests before setup or invocation.
4. Treat every helper output as untrusted until the host pipeline parses, normalizes, bounds-checks, and audits it.
5. Preserve prior authoritative outputs on every helper failure.
6. Never let helper providers own machine profiles, material recipes, operation ordering, G-code authority, readiness claims, or hardware control.

## Phase Boundaries

Phase 2 provides schemas, validation, provider scaffolding, readiness reports, and failure-preservation utilities. It does not migrate Boxes.py, install helper dependencies, or create fabrication-approved provider outputs.
