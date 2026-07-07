# Host Bootstrap

This repository assumes Git and a native shell, then prepares everything else inside repository-local `.tools/` storage.

## Linux and macOS

```bash
git submodule update --init --recursive
setup/bootstrap.sh doctor
setup/bootstrap.sh --allow-downloads setup
setup/bootstrap.sh verify
setup/bootstrap.sh run -- scripts/laser_build.py --help
```

## Windows PowerShell

```powershell
git submodule update --init --recursive
setup/bootstrap.ps1 doctor
setup/bootstrap.ps1 -AllowDownloads setup
setup/bootstrap.ps1 verify
setup/bootstrap.ps1 run -- scripts/laser_build.py --help
```

## Rules

- Downloads require the explicit allow-downloads flag.
- The bootstrap never invokes privileged system package managers.
- Managed tools write under `.tools/`, `.tmp/`, `output/`, or `revisions/` according to their manifests.
- Third-party submodules must remain clean and pinned.
- Use `setup/bootstrap.* run -- ...` on clean hosts instead of host Python.

## Common Commands

```bash
setup/bootstrap.sh run -- scripts/helper_tool.py validate
setup/bootstrap.sh run -- scripts/helper_tool.py list
setup/bootstrap.sh run -- scripts/helper_tool.py check boxes
setup/bootstrap.sh run -- scripts/helper_tool.py check cq_gears
setup/bootstrap.sh run -- scripts/helper_tool.py check bosl2
setup/bootstrap.sh run -- scripts/helper_tool.py check freecad_gears
```

## Troubleshooting

- Run `doctor` before downloads to confirm platform and Git status.
- Run `report` after setup to write host-readiness evidence.
- Run `repair` when staged setup was interrupted.
- If setup asks for approval, do not bypass it with global installs; rerun with the explicit allow-downloads flag after reviewing the source.
