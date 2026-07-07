# Playbook: Add and Validate a Callable Helper Tool

*Status: MVP*

## Objective

Add a third-party submodule as a capability-routed, subprocess-only helper without importing it into the host process or weakening host validation.

## Prerequisites

- An active approved plan naming the tool, capability, source, license, and expected outputs.
- A clean upstream repository with a stable commit to pin.
- Evidence that the tool materially reduces geometry, conversion, layout, or testing risk.
- Review of `references/helper-tool-contract.md` and `references/helper-runtime-providers.md`.

## Procedure

1. Classify the repository as a callable helper rather than a reference-only source, runtime library, or operator application.
2. Add it beneath `third_party/<id>/` as a submodule and record the exact commit.
3. Review its license, transitive dependencies, runtime requirements, CLI, output formats, determinism controls, side effects, and hardware capabilities.
4. Add `tool_adapters/<id>.json`; use schema-version `2` and `schemas/helper_adapter.schema.json` for new provider-based helpers unless the active plan explicitly approves a legacy schema-version `1` transition.
5. Declare narrow capabilities and explicit `use_for` and `avoid_for` guidance.
6. Restrict accepted outputs to formats the host can independently parse and validate, and declare exact output inventory expectations for provider adapters.
7. Add tool-specific documentation under `docs/tools/`.
8. Add a tool-specific playbook when correct use requires domain decisions beyond the generic contract.
9. Add contract tests for manifest loading, pin matching, path confinement, readiness, command construction, and fail-closed behavior.
10. Add provider readiness, request validation, output inventory, provenance, preservation, and deterministic smoke tests appropriate to the helper’s phase.
11. Update `AGENTS.md` routing and playbook indexes.

## Setup and Invocation

```bash
setup/bootstrap.sh run -- scripts/helper_tool.py validate
python3 scripts/helper_tool.py list
python3 scripts/helper_tool.py validate
python3 scripts/helper_tool.py describe <id>
python3 scripts/helper_tool.py check <id>
python3 scripts/helper_tool.py setup <id>
python3 scripts/helper_tool.py run <id> -- <tool arguments>
```

Request user approval before setup when dependency downloads may occur.

## Verification

- The source submodule is clean and matches the adapter pin.
- Setup writes only beneath the manifest’s declared repository-local environment, cache, log, staging, and temporary roots.
- Invocation occurs in a subprocess and never imports the helper into host code.
- The helper cannot write outside declared roots through the documented workflow.
- Provider requests reject repository escapes and roots not listed in `allowed_input_roots` or `allowed_output_roots`.
- Generated outputs are deterministic or normalized before use.
- Declared output inventories match actual outputs before host import.
- Host parsing rejects unsupported formats, operations, transforms, or malformed geometry.
- Existing authoritative outputs survive every failure.

## Failure

Stop on dirty source, pin mismatch, missing license, unsupported runtime, setup failure, nondeterministic output, parser mismatch, or an undeclared side effect. Do not loosen the adapter to make an incompatible tool appear ready.
