# Playbook: Bootstrap a Fabrication Host

## Objective

Prepare a cloned repository on a host that has Git and a native shell but may not have Python, Pixi, Conda, OpenSCAD, FreeCAD, or helper dependencies.

## Procedure

1. Confirm the repo is clean with `git status -sb`.
2. Initialize submodules with `git submodule update --init --recursive`.
3. Run `setup/bootstrap.sh doctor` or `setup/bootstrap.ps1 doctor`.
4. If downloads are needed, rerun setup with the explicit allow-downloads flag.
5. Run `setup/bootstrap.* verify`.
6. Run `setup/bootstrap.* report` and review `.tools/reports/host-readiness/`.
7. Use `setup/bootstrap.* run -- scripts/helper_tool.py validate`.
8. Set up only the helpers needed for the task.
9. Run the relevant smoke tests before relying on helper outputs.

## Guardrails

- Do not install global packages to satisfy repo setup.
- Do not use privileged package managers as part of the happy path.
- Do not write into third-party submodules.
- Do not claim fabrication readiness from bootstrap success alone.
