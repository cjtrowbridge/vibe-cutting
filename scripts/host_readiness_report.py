#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER_TOOL_SOURCE = REPO_ROOT / "scripts" / "helper_tool.py"
SPEC = importlib.util.spec_from_file_location("helper_tool", HELPER_TOOL_SOURCE)
helper_tool = importlib.util.module_from_spec(SPEC)
sys.modules["helper_tool"] = helper_tool
SPEC.loader.exec_module(helper_tool)


class ReadinessError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_capture(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True, check=False)


def tools_root() -> Path:
    configured = os.environ.get("VIBE_CUTTING_TOOLS_ROOT")
    if configured:
        return Path(configured).resolve()
    marker = REPO_ROOT / ".tmp" / "bootstrap-phase1-last-root"
    if marker.is_file():
        return Path(marker.read_text(encoding="utf-8").strip()).resolve()
    return REPO_ROOT / ".tools"


def relative_or_name(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return path.name


def git_evidence() -> dict[str, Any]:
    result = run_capture(["git", "--version"])
    return {
        "version_text": result.stdout.strip(),
        "available": result.returncode == 0,
    }


def submodules() -> list[dict[str, Any]]:
    result = run_capture(["git", "submodule", "status", "--recursive"])
    records = []
    if result.returncode:
        return [{"path": "unknown", "clean": False, "error": result.stderr.strip()}]
    for line in result.stdout.splitlines():
        if not line:
            continue
        state = line[0]
        fields = line[1:].split()
        revision, path = fields[:2]
        dirty = run_capture(["git", "-C", path, "status", "--porcelain"]).stdout.strip()
        records.append({"path": path, "revision": revision, "state": state, "clean": not dirty})
    return records


def lock_hashes() -> dict[str, str]:
    paths = [
        REPO_ROOT / "setup" / "pixi.lock",
        REPO_ROOT / "setup" / "tools" / "boxes-requirements.lock",
        REPO_ROOT / "setup" / "tools" / "cq-gears-requirements.lock",
        REPO_ROOT / "third_party" / "freecad-gears" / "pixi.lock",
    ]
    return {str(path.relative_to(REPO_ROOT)): sha256(path) for path in paths if path.is_file()}


def environment_manager(root: Path) -> dict[str, Any]:
    pixi = root / "bin" / "pixi"
    data = {"name": "pixi", "path": relative_or_name(pixi), "available": pixi.is_file()}
    if pixi.is_file():
        result = run_capture([str(pixi), "--version"])
        data["version_text"] = result.stdout.strip() or result.stderr.strip()
        data["sha256"] = sha256(pixi)
    return data


def bootstrap_state(root: Path) -> str:
    marker = root / "state" / "base-ready.json"
    if not marker.is_file():
        return "uninitialized"
    try:
        return json.loads(marker.read_text(encoding="utf-8")).get("bootstrap_state", "base-ready")
    except json.JSONDecodeError:
        return "unknown"


def helper_reports() -> list[dict[str, Any]]:
    reports = []
    for tool in helper_tool.discover_tools().values():
        state = helper_tool.inspect_tool(tool)
        reports.append(
            {
                "id": state["id"],
                "display_name": state["display_name"],
                "provider_kind": state.get("provider_kind"),
                "ready": state["ready"],
                "source_revision": state["source_revision"],
                "expected_revision": state["expected_revision"],
                "pin_matches": state["pin_matches"],
                "source_clean": state["source_clean"],
                "license_present": state["license_present"],
                "readiness_states": state.get("readiness_states", []),
            }
        )
    return reports


def smoke_tests() -> list[dict[str, Any]]:
    candidates = [
        ("boxes", REPO_ROOT / ".tmp" / "boxes" / "provider-smoke" / "generated" / "smoke_0.svg"),
        ("cq_gears", REPO_ROOT / ".tmp" / "cq_gears" / "provider-smoke" / "spur.svg"),
        ("bosl2", REPO_ROOT / ".tmp" / "bosl2" / "provider-smoke" / "spur.svg"),
        ("freecad_gears", REPO_ROOT / ".tmp" / "freecad_gears" / "provider-smoke" / "involute_spur.json"),
        ("primitive_power_extender", REPO_ROOT / "output" / "primitive_power_extender_laser_0_1" / "build_manifest.json"),
    ]
    records = []
    for tool_id, path in candidates:
        records.append(
            {
                "id": tool_id,
                "path": str(path.relative_to(REPO_ROOT)),
                "present": path.is_file(),
                "sha256": sha256(path) if path.is_file() else None,
            }
        )
    return records


def blocked_capabilities(helpers: list[dict[str, Any]], smokes: list[dict[str, Any]]) -> list[dict[str, str]]:
    blocked = []
    for helper in helpers:
        if not helper["ready"]:
            blocked.append({"id": helper["id"], "reason": "helper is not ready; run setup/check and inspect logs"})
    for smoke in smokes:
        if not smoke["present"]:
            blocked.append({"id": smoke["id"], "reason": f"smoke artifact missing: {smoke['path']}"})
    return blocked


def report() -> dict[str, Any]:
    root = tools_root()
    helpers = helper_reports()
    smokes = smoke_tests()
    return {
        "schema_version": 1,
        "bootstrap_state": bootstrap_state(root),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "classification": "development-host",
        },
        "git": git_evidence(),
        "environment_manager": environment_manager(root),
        "python": {
            "version": platform.python_version(),
            "executable": relative_or_name(Path(sys.executable)),
        },
        "locks": lock_hashes(),
        "submodules": submodules(),
        "helper_tools": helpers,
        "smoke_tests": smokes,
        "blocked_capabilities": blocked_capabilities(helpers, smokes),
    }


def markdown(data: dict[str, Any]) -> str:
    lines = [
        "# Host Readiness",
        "",
        f"- Bootstrap state: `{data['bootstrap_state']}`",
        f"- Platform: `{data['platform']['system']} {data['platform']['machine']}`",
        f"- Git: `{data['git'].get('version_text', 'unknown')}`",
        f"- Environment manager: `{data['environment_manager'].get('version_text', 'missing')}`",
        f"- Python: `{data['python']['version']}`",
        f"- Submodules verified: `{len(data['submodules'])}`",
        f"- Helper tools inspected: `{len(data['helper_tools'])}`",
        f"- Smoke tests recorded: `{len(data['smoke_tests'])}`",
        f"- Blocked capabilities: `{len(data['blocked_capabilities'])}`",
        "",
        "## Helpers",
        "",
    ]
    for helper in data["helper_tools"]:
        lines.append(f"- `{helper['id']}` ready=`{helper['ready']}` provider=`{helper.get('provider_kind')}`")
    lines.extend(["", "## Smoke Tests", ""])
    for smoke in data["smoke_tests"]:
        lines.append(f"- `{smoke['id']}` present=`{smoke['present']}` path=`{smoke['path']}`")
    if data["blocked_capabilities"]:
        lines.extend(["", "## Blocked Capabilities", ""])
        for item in data["blocked_capabilities"]:
            lines.append(f"- `{item['id']}`: {item['reason']}")
    return "\n".join(lines) + "\n"


def write_reports(output_root: Path) -> dict[str, Any]:
    data = report()
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "host-readiness-full.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_root / "host-readiness-full.md").write_text(markdown(data), encoding="utf-8")
    return data


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description="Write full host-readiness reports.")
    result.add_argument("--output-root", default=".tools/reports/host-readiness")
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    output_root = Path(arguments.output_root)
    if not output_root.is_absolute():
        output_root = REPO_ROOT / output_root
    data = write_reports(output_root)
    print(json.dumps({"output_root": str(output_root.relative_to(REPO_ROOT)), "blocked": len(data["blocked_capabilities"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
