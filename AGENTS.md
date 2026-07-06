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

The target managed invocation is:

```text
./setup/bootstrap.sh run -- <repo-command>
.\setup\bootstrap.ps1 run -- <repo-command>
```

Until Phase 1 implements those launchers, `python3 scripts/helper_tool.py` remains a transitional development-host command and must not be described as clean-host portable.

Execute the helper-stack roadmap through one bounded child plan per phase. Use `templates/helper-stack-phase-plan.md`, produce an acceptance report from `templates/helper-stack-phase-acceptance-report.md`, archive the accepted child plan, and obtain approval before promoting the next phase.

Inspect and prepare callable helper tools:

```bash
python3 scripts/helper_tool.py list
python3 scripts/helper_tool.py check boxes
python3 scripts/helper_tool.py setup boxes
```

Helper setup may download dependencies. Obtain approval before running it when network access is not already authorized.

## Helper-Tool Routing

Before authoring a design, use `references/geometry-backend-selection.md` and select the smallest appropriate backend:

- Use native Python geometry for simple flat shapes, repeated objects, and supported native designs.
- Use the OpenSCAD adapter for pinned-font shaping, CSG, or projected assemblies.
- Use Boxes.py for fitted panel assemblies, boxes, trays, shelves, enclosures, racks, finger joints, dovetails, living hinges, gears, and other capabilities declared in `tool_adapters/boxes.json`.
- Combine helper structural geometry with native or OpenSCAD engraving only at the host operation-model boundary.

Callable helpers generate untrusted source geometry. The host pipeline always retains ownership of operation mapping, machine/material recipes, bounds, ordering, previews, manifests, G-code, artifact installation, and readiness claims. Never use helper-generated G-code as the authoritative machine artifact without a separately approved adapter and validation plan.

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
- `references/portable-helper-host-contract.md`
- `references/helper-readiness-states.md`
- `references/managed-bootstrap-command-contract.md`

## Helper Templates

- `templates/helper-stack-phase-plan.md`
- `templates/helper-stack-phase-acceptance-report.md`
