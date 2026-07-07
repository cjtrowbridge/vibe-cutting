# Reference: Callable Helper-Tool Contract

## Purpose

Define the common contract for third-party repositories that agents may invoke as separate tools without importing their code into the host process.

This contract is used with:

- `references/portable-helper-host-contract.md` for host prerequisites and installation boundaries.
- `references/helper-readiness-states.md` for evidence-bearing readiness claims.
- `references/managed-bootstrap-command-contract.md` for portable managed invocation.

The existing `python3 scripts/helper_tool.py` workflow is transitional. After Phase 1, agents invoke it through the managed `run` interface and must not depend on host Python.

## Tool Classes

- **Reference-only:** inspected for documented behavior but never executed or imported.
- **Callable helper:** invoked as a separate process through `scripts/helper_tool.py`; outputs are treated as untrusted inputs.
- **Runtime library:** imported into host code and subject to a separate license, dependency, and architecture decision.
- **Operator application:** used manually outside the build process to inspect, stream, or operate equipment.

A repository may have only the explicitly documented roles. Adding a callable-helper role does not grant runtime-library or hardware-control authority.

## Required Adapter Manifest

Every callable helper has one `tool_adapters/<id>.json` file. Schema-version `1` manifests are legacy Python-module helpers validated against `schemas/helper_tool.schema.json`. Schema-version `2` manifests are provider-based helpers validated against `schemas/helper_adapter.schema.json`. New helpers should use schema-version `2` unless an active plan explicitly accepts a legacy transition.

Every manifest must declare:

- Stable ID and display name.
- Source submodule path, upstream URL, pinned revision, license, and license file.
- Capabilities and positive/negative routing guidance.
- Runtime provider or legacy runtime kind, setup metadata, invocation metadata, environment path, and working directory.
- Accepted output formats and any semantic operation mapping.
- Exact output inventory requirements when using provider schema-version `2`.
- Hardware, network, source-modification, and output-root boundaries.
- Provider schema-version `2` input-root boundaries.

## Invocation Contract

Agents must:

1. Select tools by declared capability.
2. Run `setup/bootstrap.* run -- scripts/helper_tool.py validate` and `setup/bootstrap.* run -- scripts/helper_tool.py check <id>` after portable bootstrap exists; use direct Python commands only as the documented transitional development workflow.
3. Request approval before `setup` when the manifest says setup may use the network.
4. Invoke the tool only through the managed helper dispatcher.
5. Write outputs only beneath the manifest’s allowed output roots.
6. Treat generated files as untrusted until parsed and validated by the host pipeline.
7. Record tool ID, pinned revision, arguments/config hash, and output hashes in build provenance.

Agents must not:

- Import callable-helper packages into the host Python process.
- Execute scripts directly from a helper submodule.
- Modify helper source, install generated files into the helper repository, or silently use a dirty submodule.
- Allow a helper to select machine recipes, bypass host bounds checks, generate authoritative G-code, or control hardware unless a separately approved role explicitly permits it.
- Silently fall back to a different helper or backend.

## Provider Contract

Provider schema-version `2` supports:

- `pixi_environment`
- `openscad_library`
- `system_application`
- `manual_operator`

See `references/helper-runtime-providers.md` for routing and readiness semantics. Phase 2 provider scaffolding validates manifests, paths, readiness states, output inventories, request roots, and preservation behavior; later phases migrate individual helpers into real provider environments.

## Environment Contract

Provider helpers install fingerprinted environments beneath `.tools/environments/<id>/`. Legacy schema-version `1` helpers may still install beneath `.tmp/helper-tools/<id>/` only when an active migration plan explicitly permits that temporary path. Either environment is accepted only when:

- The source submodule exists and is clean.
- Its checked-out commit matches the manifest pin.
- The declared license file exists.
- The host runtime meets the minimum version.
- The install marker matches both the source revision and adapter-manifest hash.
- The install marker records the host Python version and resolved package versions.
- A subprocess import check succeeds.

## Update Contract

Updating a helper requires:

1. Record the old and proposed revisions.
2. Review upstream license, dependencies, CLI, output format, and behavior changes.
3. Update the submodule and adapter pin together.
4. Recreate the isolated environment.
5. Re-run contract, golden-output, parser, bounds, and determinism tests.
6. Update routing and tool-specific documentation when capabilities change.
7. Preserve rollback to the prior submodule and manifest revisions.

## Failure Contract

Fail closed when the source is missing, dirty, unpinned, improperly licensed, not installed, incompatible, or unable to produce a valid declared output. Preserve existing authoritative outputs and never replace them with partial helper output.
