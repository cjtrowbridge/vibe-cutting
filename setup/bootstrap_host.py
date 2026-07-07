#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys
from typing import Any, Sequence


MINIMUM_GIT_VERSION = (2, 31, 0)
BOOTSTRAP_STATES = {
    "uninitialized",
    "manager-ready",
    "base-ready",
    "tools-partial",
    "tools-ready",
    "verified",
}


class BootstrapError(RuntimeError):
    pass


def repo_root() -> Path:
    configured = os.environ.get("VIBE_CUTTING_REPO_ROOT")
    root = Path(configured) if configured else Path(__file__).resolve().parents[1]
    return root.resolve()


def tools_root(root: Path) -> Path:
    configured = os.environ.get("VIBE_CUTTING_TOOLS_ROOT")
    path = Path(configured) if configured else root / ".tools"
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise BootstrapError(f"tools root escapes repository: {resolved}") from error
    return resolved


def run_command(
    arguments: Sequence[str],
    *,
    root: Path,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(arguments),
        cwd=root,
        check=check,
        capture_output=capture_output,
        text=True,
    )


def parse_git_version(output: str) -> tuple[int, int, int]:
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", output)
    if not match:
        raise BootstrapError(f"unable to parse Git version: {output.strip()}")
    return tuple(int(part or 0) for part in match.groups())


def git_evidence(root: Path) -> dict[str, Any]:
    try:
        path = shutil.which("git")
        if not path:
            raise FileNotFoundError("git")
        version_text = run_command(["git", "--version"], root=root).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise BootstrapError("Git 2.31.0 or newer is required") from error
    version = parse_git_version(version_text)
    if version < MINIMUM_GIT_VERSION:
        raise BootstrapError(
            f"Git {'.'.join(map(str, version))} is too old; Git 2.31.0 or newer is required"
        )
    return {
        "exec_path": path,
        "version": ".".join(map(str, version)),
        "version_text": version_text,
    }


def lock_hash(root: Path) -> str:
    path = root / "setup" / "pixi.lock"
    if not path.is_file():
        raise BootstrapError("setup/pixi.lock is missing")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def submodule_evidence(root: Path) -> list[dict[str, Any]]:
    result = run_command(
        ["git", "submodule", "status", "--recursive"],
        root=root,
        check=False,
    )
    if result.returncode:
        raise BootstrapError(result.stderr.strip() or "unable to inspect submodules")
    records: list[dict[str, Any]] = []
    for state, revision, path in parse_submodule_status(result.stdout):
        dirty = run_command(
            ["git", "-C", path, "status", "--porcelain"],
            root=root,
        ).stdout.strip()
        if dirty:
            raise BootstrapError(f"submodule is dirty: {path}")
        records.append({"path": path, "revision": revision, "clean": True})
    return records


def parse_submodule_status(output: str) -> list[tuple[str, str, str]]:
    records: list[tuple[str, str, str]] = []
    for line in output.splitlines():
        if not line:
            continue
        state = line[0]
        fields = line[1:].strip().split()
        if len(fields) < 2:
            raise BootstrapError(f"malformed submodule status: {line}")
        revision, path = fields[:2]
        if state == "-":
            raise BootstrapError(f"submodule is uninitialized: {path}")
        if state == "+":
            raise BootstrapError(f"submodule revision does not match gitlink: {path}")
        if state == "U":
            raise BootstrapError(f"submodule has merge conflicts: {path}")
        records.append((state, revision, path))
    return records


def initialize_submodules(root: Path) -> None:
    run_command(["git", "submodule", "sync", "--recursive"], root=root, capture_output=False)
    run_command(
        ["git", "submodule", "update", "--init", "--recursive"],
        root=root,
        capture_output=False,
    )


def report_data(root: Path, tools: Path, state: str) -> dict[str, Any]:
    if state not in BOOTSTRAP_STATES:
        raise BootstrapError(f"invalid bootstrap state: {state}")
    return {
        "schema_version": 1,
        "bootstrap_state": state,
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "git": git_evidence(root),
        "pixi": {
            "version": os.environ.get("VIBE_CUTTING_PIXI_VERSION", "unknown"),
            "lock_sha256": lock_hash(root),
        },
        "python": {
            "executable": str(Path(sys.executable).resolve()),
            "version": platform.python_version(),
        },
        "tools_root": str(tools),
        "submodules": submodule_evidence(root),
    }


def write_report(root: Path, tools: Path, state: str) -> dict[str, Any]:
    data = report_data(root, tools, state)
    report_root = tools / "reports" / "host-readiness"
    report_root.mkdir(parents=True, exist_ok=True)
    json_path = report_root / "host-readiness.json"
    markdown_path = report_root / "host-readiness.md"
    json_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# Host Readiness",
        "",
        f"- Bootstrap state: `{data['bootstrap_state']}`",
        f"- Platform: `{data['platform']['system']} {data['platform']['machine']}`",
        f"- Git: `{data['git']['version']}`",
        f"- Pixi: `{data['pixi']['version']}`",
        f"- Python: `{data['python']['version']}`",
        f"- Lock SHA-256: `{data['pixi']['lock_sha256']}`",
        f"- Submodules verified: `{len(data['submodules'])}`",
    ]
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return data


def state_marker(tools: Path) -> Path:
    return tools / "state" / "base-ready.json"


def write_state(tools: Path, data: dict[str, Any]) -> None:
    marker = state_marker(tools)
    marker.parent.mkdir(parents=True, exist_ok=True)
    staged = marker.with_suffix(".json.tmp")
    staged.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    staged.replace(marker)


def require_base_state(tools: Path) -> None:
    marker = state_marker(tools)
    if not marker.is_file():
        raise BootstrapError("managed base state is missing; run setup first")


def command_setup(root: Path, tools: Path) -> int:
    initialize_submodules(root)
    data = write_report(root, tools, "base-ready")
    write_state(tools, data)
    print("base-ready")
    return 0


def command_verify(root: Path, tools: Path) -> int:
    require_base_state(tools)
    data = write_report(root, tools, "verified")
    print(json.dumps(data, sort_keys=True))
    return 0


def command_report(root: Path, tools: Path) -> int:
    require_base_state(tools)
    data = write_report(root, tools, "verified")
    print(json.dumps(data, indent=2, sort_keys=True))
    return 0


def resolve_repo_command(root: Path, arguments: Sequence[str]) -> tuple[Path, list[str]]:
    if not arguments:
        raise BootstrapError("run requires a repository command")
    command = Path(arguments[0])
    if command.is_absolute():
        raise BootstrapError("run command must be repository-relative")
    resolved = (root / command).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as error:
        raise BootstrapError("run command escapes repository") from error
    if not resolved.is_file():
        raise BootstrapError(f"run command does not exist: {relative}")
    if relative.parts[0] in {"third_party", "agents"}:
        raise BootstrapError(f"direct submodule execution is prohibited: {relative}")
    if resolved.suffix != ".py" or relative.parts[0] not in {"scripts", "setup"}:
        raise BootstrapError(f"unsupported managed command: {relative}")
    return resolved, list(arguments[1:])


def command_run(root: Path, tools: Path, arguments: Sequence[str]) -> int:
    require_base_state(tools)
    command, delegated = resolve_repo_command(root, arguments)
    environment = os.environ.copy()
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [sys.executable, str(command), *delegated],
        cwd=root,
        env=environment,
    )
    return completed.returncode


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Managed vibe-cutting bootstrap orchestrator")
    subparsers = result.add_subparsers(dest="command", required=True)
    subparsers.add_parser("setup")
    subparsers.add_parser("repair")
    subparsers.add_parser("verify")
    subparsers.add_parser("report")
    run = subparsers.add_parser("run")
    run.add_argument("arguments", nargs=argparse.REMAINDER)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    root = repo_root()
    tools = tools_root(root)
    try:
        if arguments.command in {"setup", "repair"}:
            return command_setup(root, tools)
        if arguments.command == "verify":
            return command_verify(root, tools)
        if arguments.command == "report":
            return command_report(root, tools)
        if arguments.command == "run":
            delegated = arguments.arguments
            if delegated and delegated[0] == "--":
                delegated = delegated[1:]
            return command_run(root, tools, delegated)
    except (BootstrapError, subprocess.CalledProcessError) as error:
        print(f"vibe-cutting bootstrap: {error}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
