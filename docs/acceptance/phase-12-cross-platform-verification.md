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
| Linux x86-64 | `ubuntu-latest` bootstrap job | Passed in GitHub Actions run `28882090219`; artifact `host-readiness-Linux-X64` | Not claimed |
| Windows x86-64 | `windows-latest` PowerShell bootstrap job | Passed in GitHub Actions run `28882090219`; artifact `host-readiness-Windows-X64` | Not claimed |
| macOS hosted runner | `macos-latest` bootstrap job | Passed in GitHub Actions run `28882090219`; artifact `host-readiness-macOS-ARM64` | Not claimed |

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
gh run view 28882090219
```

## Readiness Decision

The repository now has passing cross-platform bootstrap CI for Linux x86-64, Windows x86-64, and the current macOS hosted-runner architecture. CI artifacts are host/toolchain readiness evidence only; they are not material, machine, or fabrication approval.

## Known Limitations

- Hosted macOS runner architecture depends on GitHub Actions runner availability.
- Linux ARM64 and macOS Intel remain pending until matching clean-host evidence is recorded.
- Heavyweight FreeCAD helper checks are manual opt-in and non-blocking by default.
- CI cannot validate physical laser behavior, material settings, operator setup, ventilation, focus, fixturing, or LaserGRBL streaming.
