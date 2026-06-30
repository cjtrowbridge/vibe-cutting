# AGENTS Instructions

Read `./agents/RULES.md` in its entirety before doing anything in this repository. Follow all instructions in that file as though they are written directly here.

Use host-managed `./playbooks/`, `./references/`, `./templates/`, and `./scripts/` when present. Fall back to the corresponding paths under `./agents/` when a host copy is missing.

## Repository Structure

- `./agents/`: canonical agent policy and upstream framework defaults.
- `./third_party/vibe-modeling/`: read-only reference submodule; never copy, adapt, import, link, vendor, package, or require it at runtime.
- `./third_party/lasergrbl/`: read-only GPLv3 reference submodule; never copy, adapt, import, link, vendor, package, or require it at runtime.
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
