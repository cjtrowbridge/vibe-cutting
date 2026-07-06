# Helper Tools

Callable helper tools are separately maintained third-party repositories that extend design capabilities without becoming part of the host Python process. They remain pinned submodules and run through `scripts/helper_tool.py`.

## Why This Layer Exists

Laser design spans several specialized domains: fitted structures, geometry projection, font shaping, nesting, image tracing, and more. A capability registry lets the project adopt focused upstream tools without forcing every feature into `scripts/laser_build.py` or coupling the core to one library.

## Commands

```bash
python3 scripts/helper_tool.py list
python3 scripts/helper_tool.py describe boxes
python3 scripts/helper_tool.py check boxes
python3 scripts/helper_tool.py setup boxes
python3 scripts/helper_tool.py run boxes -- --list
```

`setup` installs the pinned local submodule and its dependencies beneath `.tmp/helper-tools/<id>/`. It may download dependencies. The environment is disposable, records resolved Python/package provenance, and is invalidated when the source pin or adapter manifest changes.

## Trust Boundary

Helper output is never authoritative by itself. The host pipeline must parse it, map semantic operations, normalize coordinates, enforce machine and stock bounds, attach recipes, generate previews and G-code, and audit the final artifact set.

Helper tools cannot control hardware through this interface. They run only when their source is present, clean, correctly pinned, licensed as declared, installed, and importable in the isolated environment.

## Adding Tools

Each tool needs:

- A submodule under `third_party/`.
- A manifest under `tool_adapters/`.
- A pinned revision and license record.
- Capability and routing guidance.
- Accepted output contracts.
- Tests and tool-specific documentation.

See `playbooks/how_to_add_and_validate_a_helper_tool.md`.
