# AGENTS Instructions

Read `./agents/RULES.md` in its entirety before doing anything in this repository. Follow all instructions in that file as though they are written directly here.

Use host-managed `./playbooks/`, `./references/`, `./templates/`, and `./scripts/` when present. Fall back to the corresponding paths under `./agents/` when a host copy is missing.

## Repository Structure

- `./agents/`: canonical agent policy and upstream framework defaults.
- `./third_party/vibe-modeling/`: read-only reference submodule; never copy, adapt, import, link, vendor, package, or require it at runtime.
- `./third_party/lasergrbl/`: read-only GPLv3 reference submodule; never copy, adapt, import, link, vendor, package, or require it at runtime.
- `./third_party/boxes/`: pinned GPLv3 callable-helper submodule; invoke only through `scripts/helper_tool.py`, never import it into the host process or modify its source.
- `./tool_adapters/`: machine-readable capability, invocation, output, safety, license, and pin contracts for callable helpers.
- `./plans/`, `./journal/`, `./kanban/`, and `./downtime/reports/`: host-owned operational state.
- `./playbooks/`, `./references/`, `./templates/`, and `./scripts/`: host-managed framework copies.

## Maintenance Commands

For host-owned plans:

```bash
python3 agents/scripts/regenerate_plan_indexes.py --repo-root .
python3 agents/scripts/regenerate_plan_indexes.py --check --repo-root .
```

Initialize or update all submodules:

```bash
git submodule update --init --recursive
```

## Portable Bootstrap Contract

Git 2.31+ and the platform-native shell or PowerShell are the only development tools the portable bootstrap may assume. Do not assume host Python, Pixi, Conda, OpenSCAD, FreeCAD, or helper dependencies.

Before implementing or changing bootstrap behavior, read:

- `references/portable-helper-host-contract.md`
- `references/helper-readiness-states.md`
- `references/managed-bootstrap-command-contract.md`
- `docs/decisions/0001-portable-helper-bootstrap-and-provider-model.md`

Use the managed bootstrap for portable host setup and repository Python commands:

```text
./setup/bootstrap.sh doctor
./setup/bootstrap.sh --allow-downloads setup
./setup/bootstrap.sh run -- <repo-command>
.\setup\bootstrap.ps1 doctor
.\setup\bootstrap.ps1 -AllowDownloads setup
.\setup\bootstrap.ps1 run -- <repo-command>
```

`setup/bootstrap.sh` is runtime-qualified on the development Linux x86-64 host. `setup/bootstrap.ps1` and non-x86-64 platforms are pinned but still require clean-host qualification before being treated as fully validated.

Execute the helper-stack roadmap through one bounded child plan per phase. Use `templates/helper-stack-phase-plan.md`, produce an acceptance report from `templates/helper-stack-phase-acceptance-report.md`, archive the accepted child plan, and continue only under user-approved phase authority.

Inspect and prepare callable helper tools:

```bash
setup/bootstrap.sh run -- scripts/helper_tool.py list
setup/bootstrap.sh run -- scripts/helper_tool.py validate
setup/bootstrap.sh run -- scripts/helper_tool.py check boxes
setup/bootstrap.sh run -- scripts/helper_tool.py setup boxes
```

Helper setup may download dependencies. Obtain approval before running it when network access is not already authorized.

## Helper-Tool Routing

Before authoring a design, use `references/geometry-backend-selection.md` and `references/helper-runtime-providers.md`, then select the smallest appropriate backend:

- Use native Python geometry for simple flat shapes, repeated objects, and supported native designs.
- Use the OpenSCAD adapter for pinned-font shaping, CSG, or projected assemblies.
- Use Boxes.py for fitted panel assemblies, boxes, trays, shelves, enclosures, racks, finger joints, dovetails, living hinges, gears, and other capabilities declared in `tool_adapters/boxes.json`.
- Combine helper structural geometry with native or OpenSCAD engraving only at the host operation-model boundary.

Callable helpers generate untrusted source geometry. The host pipeline always retains ownership of operation mapping, machine/material recipes, bounds, ordering, previews, manifests, G-code, artifact installation, and readiness claims. Never use helper-generated G-code as the authoritative machine artifact without a separately approved adapter and validation plan.

Provider-based helper adapters use schema-version `2` and declare one of `pixi_environment`, `openscad_library`, `system_application`, or `manual_operator`. `boxes` is a provider helper. Schema-version `1` adapters are supported only as transitional legacy helpers when an active migration plan explicitly permits them. Run `setup/bootstrap.sh run -- scripts/helper_tool.py validate` before relying on helper routing.

## Laser Playbooks

- `playbooks/how_to_add_a_new_laser_design.md`
- `playbooks/how_to_build_and_audit_a_laser_job.md`
- `playbooks/how_to_create_and_validate_a_machine_profile.md`
- `playbooks/how_to_generate_and_validate_grbl_gcode.md`
- `playbooks/how_to_author_openscad_laser_geometry.md`
- `playbooks/how_to_create_and_iterate_merit_badge_sheets.md`
- `playbooks/how_to_add_and_validate_a_helper_tool.md`
- `playbooks/how_to_use_boxes_for_laser_geometry.md`

Use the relevant laser playbook before changing designs, profiles, build behavior, or G-code generation.

## Helper References

- `references/helper-tool-contract.md`
- `references/geometry-backend-selection.md`
- `references/helper-runtime-providers.md`
- `references/portable-helper-host-contract.md`
- `references/helper-readiness-states.md`
- `references/managed-bootstrap-command-contract.md`

## Helper Templates

- `templates/helper-stack-phase-plan.md`
- `templates/helper-stack-phase-acceptance-report.md`
