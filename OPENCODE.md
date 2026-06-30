# OPENCODE Instructions

Read `./agents/RULES.md` in its entirety before doing anything in this repository. Follow all instructions in that file as though they are written directly here.

Use host-managed `./playbooks/`, `./references/`, `./templates/`, and `./scripts/` when present. Fall back to the corresponding paths under `./agents/` when a host copy is missing.

For host-owned plans, run `python agents/scripts/regenerate_plan_indexes.py --repo-root .`.
