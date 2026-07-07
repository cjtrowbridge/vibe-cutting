# Helper Tools

Callable helper tools are separately maintained third-party repositories that extend design capabilities without becoming part of the host Python process. They remain pinned submodules and run through `scripts/helper_tool.py`.

Provider-based adapters are the default helper model. Boxes.py is the first migrated provider helper.

## Why This Layer Exists

Laser design spans several specialized domains: fitted structures, geometry projection, font shaping, nesting, image tracing, and more. A capability registry lets the project adopt focused upstream tools without forcing every feature into `scripts/laser_build.py` or coupling the core to one library.

## Commands

```bash
setup/bootstrap.sh run -- scripts/helper_tool.py validate
setup/bootstrap.sh run -- scripts/helper_tool.py list
setup/bootstrap.sh run -- scripts/helper_tool.py describe boxes
setup/bootstrap.sh run -- scripts/helper_tool.py check boxes
setup/bootstrap.sh run -- scripts/helper_tool.py setup boxes
setup/bootstrap.sh run -- scripts/helper_tool.py run boxes -- --list
```

`setup` installs the pinned local submodule and its dependencies beneath `.tools/environments/<id>/<fingerprint>/`. It may download dependencies. The environment is repository-local, records resolved Python/package provenance, and is invalidated when the source pin, adapter manifest, or lock hash changes.

## Provider Adapter Model

Schema-version `2` helper adapters declare a runtime provider:

- `pixi_environment` for managed Conda-style environments.
- `openscad_library` for OpenSCAD libraries or executable bindings.
- `system_application` for locally installed applications with manual remediation.
- `manual_operator` for human-operated reference tools.

Provider adapters declare allowed input roots, output roots, exact output inventories, readiness states, setup metadata, invocation metadata, and provenance fields.

Readiness states are `registered`, `dependencies-ready`, `invocation-ready`, `output-validated`, `pipeline-integrated`, and `fabrication-approved`. Phase 2 adapters must not claim fabrication approval.

## Trust Boundary

Helper output is never authoritative by itself. The host pipeline must parse it, map semantic operations, normalize coordinates, enforce machine and stock bounds, attach recipes, generate previews and G-code, and audit the final artifact set.

Helper tools cannot control hardware through this interface. They run only when their source is present, clean, correctly pinned, licensed as declared, installed, and importable in the isolated environment.

## Adding Tools

Each tool needs:

- A submodule under `third_party/`.
- A manifest under `tool_adapters/`; use schema-version `2` for new provider-based helpers.
- A pinned revision and license record.
- Capability and routing guidance.
- A provider kind and readiness-state contract.
- Accepted output contracts.
- Tests and tool-specific documentation.

See `playbooks/how_to_add_and_validate_a_helper_tool.md`.

## Current Provider Helpers

- Boxes.py: fitted panel structures and reproducible SVG source geometry.
- CadQuery + CQ_Gears: planar spur gear, ring gear, rack, and gear-mesh source profiles for mechanism planning.
- BOSL2: OpenSCAD comparison profiles for spur gears, ring gears, and racks.
