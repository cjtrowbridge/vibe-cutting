# Phase 12 Acceptance Report: Cross-Platform Verification

## Scope

- Parent roadmap: `plans/past/2026-07-06-09-17-37_build-portable-helper-tool-bootstrap-and-mechanism-stack.md`
- Child plan: `plans/past/2026-07-06-22-03-12_add-cross-platform-verification.md`
- Parent checklist items: `15.1` through `15.6`

## Implemented Artifacts

- `.github/workflows/cross-platform-bootstrap.yml`
- `docs/ci-verification.md`
- `docs/toolchain-support-matrix.md`
- `docs/acceptance/phase-12-cross-platform-verification.md`

## Platform Coverage

| Platform | CI Coverage | Evidence Status | Fabrication Readiness |
|---|---|---|---|
| Linux x86-64 | `ubuntu-latest` bootstrap job | Pending first remote workflow run | Not claimed |
| Windows x86-64 | `windows-latest` PowerShell bootstrap job | Pending first remote workflow run | Not claimed |
| macOS hosted runner | `macos-latest` bootstrap job | Pending first remote workflow run | Not claimed |

## Verification Commands

Local repository verification:

```bash
python3 agents/scripts/regenerate_plan_indexes.py --repo-root .
python3 -m unittest discover -s tests -v
git diff --check
python3 agents/scripts/regenerate_plan_indexes.py --check --repo-root .
```

CI verification after push:

```bash
gh run list --workflow cross-platform-bootstrap.yml --limit 5
```

## Readiness Decision

The repository now has cross-platform bootstrap CI scaffolding and artifact publication. Non-local platforms remain evidence-pending until GitHub Actions runs succeed. CI artifacts are host/toolchain readiness evidence only; they are not material, machine, or fabrication approval.

## Known Limitations

- Hosted macOS runner architecture depends on GitHub Actions runner availability.
- Heavyweight FreeCAD helper checks are manual opt-in and non-blocking by default.
- CI cannot validate physical laser behavior, material settings, operator setup, ventilation, focus, fixturing, or LaserGRBL streaming.
