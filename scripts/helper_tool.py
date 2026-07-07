#!/usr/bin/env python3

import argparse
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from setup.providers import ProviderError, validate_provider_manifest as validate_provider_config

ADAPTER_DIR = REPO_ROOT / "tool_adapters"
INSTALL_MARKER = "install.json"
TOOL_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")
READINESS_STATES = {
    "registered",
    "dependencies-ready",
    "invocation-ready",
    "output-validated",
    "pipeline-integrated",
    "fabrication-approved",
}


class ToolError(RuntimeError):
    pass


def fail(message):
    raise ToolError(message)


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"Missing helper-tool adapter: {path}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid helper-tool adapter JSON at {path}: {exc}")


def safe_repo_path(value, label):
    path = Path(value)
    if path.is_absolute():
        fail(f"{label} must be repository-relative: {value}")
    resolved = (REPO_ROOT / path).resolve()
    try:
        resolved.relative_to(REPO_ROOT.resolve())
    except ValueError:
        fail(f"{label} escapes the repository: {value}")
    return resolved


def require_mapping(data, keys, label):
    if not isinstance(data, dict):
        fail(f"{label} must be an object.")
    missing = [key for key in keys if key not in data]
    if missing:
        fail(f"{label} is missing required fields: {', '.join(missing)}")


def validate_common_manifest(data, path, required_extra):
    require_mapping(
        data,
        [
            "schema_version",
            "id",
            "display_name",
            "tool_class",
            "source",
            "capabilities",
            "routing",
            "outputs",
            "safety",
            *required_extra,
        ],
        f"Adapter {path}",
    )
    tool_id = data["id"]
    if not isinstance(tool_id, str) or not TOOL_ID_PATTERN.fullmatch(tool_id):
        fail(f"Invalid helper-tool id in {path}: {tool_id!r}")
    if path.stem != tool_id:
        fail(f"Adapter filename must match its id: {path.name} != {tool_id}.json")
    if data["tool_class"] != "callable_helper":
        fail(f"Unsupported helper-tool class for {tool_id}: {data['tool_class']}")
    if not isinstance(data["capabilities"], list) or not data["capabilities"]:
        fail(f"Helper tool {tool_id} must declare capabilities.")

    source = data["source"]
    require_mapping(
        source,
        ["type", "path", "upstream", "pinned_revision", "license", "license_file"],
        f"Source for {tool_id}",
    )
    if source["type"] != "git_submodule":
        fail(f"Unsupported source type for {tool_id}: {source['type']}")
    if Path(source["path"]).parts[:1] != ("third_party",):
        fail(f"Source path for {tool_id} must be under third_party/.")
    if not REVISION_PATTERN.fullmatch(source["pinned_revision"]):
        fail(f"Invalid pinned revision for {tool_id}: {source['pinned_revision']}")
    source_path = safe_repo_path(source["path"], f"Source path for {tool_id}")
    license_path = safe_repo_path(
        str(Path(source["path"]) / source["license_file"]),
        f"License path for {tool_id}",
    )

    outputs = data["outputs"]
    require_mapping(outputs, ["accepted_formats", "primary_format", "operation_colors"], f"Outputs for {tool_id}")
    if outputs["primary_format"] not in outputs["accepted_formats"]:
        fail(f"Primary output format for {tool_id} must be accepted.")

    safety = data["safety"]
    require_mapping(
        safety,
        ["controls_hardware", "setup_may_use_network", "may_modify_source", "allowed_output_roots"],
        f"Safety contract for {tool_id}",
    )
    if safety["controls_hardware"]:
        fail(f"Helper tool {tool_id} may not control hardware.")
    if safety["may_modify_source"]:
        fail(f"Helper tool {tool_id} may not modify its source submodule.")
    for output_root in safety["allowed_output_roots"]:
        safe_repo_path(output_root, f"Allowed output root for {tool_id}")

    data["_adapter_path"] = path
    data["_source_path"] = source_path
    data["_license_path"] = license_path
    return data


def validate_legacy_manifest(data, path):
    tool = validate_common_manifest(data, path, ["runtime"])
    tool_id = tool["id"]

    runtime = tool["runtime"]
    require_mapping(
        runtime,
        [
            "kind",
            "python_minimum",
            "module",
            "install_source",
            "environment_path",
            "working_directory",
        ],
        f"Runtime for {tool_id}",
    )
    if runtime["kind"] != "python_module":
        fail(f"Unsupported runtime kind for {tool_id}: {runtime['kind']}")
    if runtime["install_source"] != tool["source"]["path"]:
        fail(f"Install source must match the submodule path for {tool_id}.")
    environment_path = safe_repo_path(runtime["environment_path"], f"Environment path for {tool_id}")
    expected_environment_root = (REPO_ROOT / ".tmp" / "helper-tools").resolve()
    try:
        environment_path.relative_to(expected_environment_root)
    except ValueError:
        fail(f"Environment path for {tool_id} must be under .tmp/helper-tools.")
    working_directory = safe_repo_path(runtime["working_directory"], f"Working directory for {tool_id}")

    tool["_environment_path"] = environment_path
    tool["_working_directory"] = working_directory
    tool["_adapter_model"] = "legacy_python_module"
    return tool


def validate_provider_adapter(data, path):
    tool = validate_common_manifest(data, path, ["provider", "readiness"])
    tool_id = tool["id"]
    provider = tool["provider"]
    require_mapping(
        provider,
        ["kind", "environment_path", "working_directory", "setup", "invocation"],
        f"Provider for {tool_id}",
    )
    if not isinstance(provider["setup"], dict):
        fail(f"Provider setup for {tool_id} must be an object.")
    if not isinstance(provider["invocation"], dict):
        fail(f"Provider invocation for {tool_id} must be an object.")
    if "allowed_input_roots" not in tool["safety"]:
        fail(f"Safety contract for {tool_id} is missing required fields: allowed_input_roots")
    for input_root in tool["safety"]["allowed_input_roots"]:
        safe_repo_path(input_root, f"Allowed input root for {tool_id}")
    outputs = tool["outputs"]
    if "inventory" not in outputs or not isinstance(outputs["inventory"], list):
        fail(f"Outputs for {tool_id} must declare an inventory list.")
    for item in outputs["inventory"]:
        require_mapping(item, ["path", "format", "required"], f"Output inventory item for {tool_id}")
        if item["format"] not in outputs["accepted_formats"]:
            fail(f"Output inventory format for {tool_id} is not accepted: {item['format']}")
    readiness = tool["readiness"]
    require_mapping(readiness, ["states", "fabrication_approved"], f"Readiness for {tool_id}")
    states = readiness["states"]
    if not isinstance(states, list) or not states:
        fail(f"Readiness states for {tool_id} must be a non-empty list.")
    unknown_states = [state for state in states if state not in READINESS_STATES]
    if unknown_states:
        fail(f"Unsupported readiness states for {tool_id}: {', '.join(unknown_states)}")
    if "registered" not in states:
        fail(f"Readiness states for {tool_id} must include registered.")
    if readiness["fabrication_approved"]:
        fail(f"Provider adapter {tool_id} may not claim fabrication approval in Phase 2.")
    try:
        report = validate_provider_config(REPO_ROOT, tool)
    except ProviderError as error:
        fail(f"Provider validation failed for {tool_id}: {error}")
    tool["_provider_report"] = report
    tool["_environment_path"] = safe_repo_path(provider["environment_path"], f"Environment path for {tool_id}")
    tool["_working_directory"] = safe_repo_path(provider["working_directory"], f"Working directory for {tool_id}")
    tool["_adapter_model"] = "provider"
    return tool


def validate_manifest(data, path):
    schema_version = data.get("schema_version")
    if schema_version == 1:
        return validate_legacy_manifest(data, path)
    if schema_version == 2:
        return validate_provider_adapter(data, path)
    fail(f"Unsupported helper-tool schema version in {path}: {schema_version}")


def discover_tools():
    if not ADAPTER_DIR.is_dir():
        fail(f"Missing helper-tool adapter directory: {ADAPTER_DIR}")
    tools = {}
    for path in sorted(ADAPTER_DIR.glob("*.json")):
        manifest = validate_manifest(load_json(path), path)
        if manifest["id"] in tools:
            fail(f"Duplicate helper-tool id: {manifest['id']}")
        tools[manifest["id"]] = manifest
    return tools


def get_tool(tool_id):
    tools = discover_tools()
    if tool_id not in tools:
        fail(f"Unknown helper tool {tool_id!r}. Available tools: {', '.join(tools) or 'none'}")
    return tools[tool_id]


def python_path_environment(site_packages=None):
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    if site_packages is not None:
        existing = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = (
            str(site_packages) if not existing else os.pathsep.join([str(site_packages), existing])
        )
    return environment


def run_capture(command, cwd=REPO_ROOT, site_packages=None):
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            env=python_path_environment(site_packages),
        )
    except OSError as exc:
        fail(f"Could not execute {' '.join(map(str, command))}: {exc}")
    return result


def source_revision(tool):
    result = run_capture(["git", "-C", str(tool["_source_path"]), "rev-parse", "HEAD"])
    if result.returncode:
        return None
    return result.stdout.strip()


def source_is_clean(tool):
    result = run_capture(["git", "-C", str(tool["_source_path"]), "status", "--porcelain"])
    return result.returncode == 0 and not result.stdout.strip()


def site_packages_path(environment_path):
    return environment_path / "site-packages"


def provider_fingerprint(tool):
    return tool["_provider_report"]["environment_fingerprint"]


def provider_environment_path(tool):
    return tool["_environment_path"] / provider_fingerprint(tool)


def provider_site_packages_path(tool):
    return provider_environment_path(tool) / "site-packages"


def provider_marker(tool):
    path = provider_environment_path(tool) / "provider-ready.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def manifest_sha256(tool):
    return hashlib.sha256(tool["_adapter_path"].read_bytes()).hexdigest()


def install_marker(tool):
    path = tool["_environment_path"] / INSTALL_MARKER
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def inspect_tool(tool):
    if tool.get("_adapter_model") == "provider":
        return inspect_provider_tool(tool)
    source_path = tool["_source_path"]
    revision = source_revision(tool) if source_path.is_dir() else None
    expected_revision = tool["source"]["pinned_revision"]
    site_packages = site_packages_path(tool["_environment_path"])
    marker = install_marker(tool)
    marker_matches = bool(
        marker
        and marker.get("tool_id") == tool["id"]
        and marker.get("source_revision") == expected_revision
        and marker.get("adapter_sha256") == manifest_sha256(tool)
    )
    import_ready = False
    import_error = None
    minimum_python = tuple(int(part) for part in tool["runtime"]["python_minimum"].split("."))
    python_compatible = sys.version_info[:2] >= minimum_python
    if site_packages.is_dir() and marker_matches and python_compatible:
        result = run_capture(
            [sys.executable, "-c", f"import {tool['runtime']['module'].split('.')[0]}"],
            site_packages=site_packages,
        )
        import_ready = result.returncode == 0
        if not import_ready:
            import_error = result.stderr.strip() or result.stdout.strip()
    state = {
        "id": tool["id"],
        "display_name": tool["display_name"],
        "source_path": str(tool["source"]["path"]),
        "source_present": source_path.is_dir(),
        "source_revision": revision,
        "expected_revision": expected_revision,
        "pin_matches": revision == expected_revision,
        "source_clean": source_is_clean(tool) if source_path.is_dir() else False,
        "license_present": tool["_license_path"].is_file(),
        "python_compatible": python_compatible,
        "environment_path": str(tool["runtime"]["environment_path"]),
        "environment_present": site_packages.is_dir(),
        "install_marker_matches": marker_matches,
        "installed_python": marker.get("python_version") if marker else None,
        "installed_package_count": len(marker.get("packages", [])) if marker else 0,
        "import_ready": import_ready,
        "import_error": import_error,
    }
    state["ready"] = all(
        [
            state["source_present"],
            state["pin_matches"],
            state["source_clean"],
            state["license_present"],
            state["python_compatible"],
            state["environment_present"],
            state["install_marker_matches"],
            state["import_ready"],
        ]
    )
    return state


def inspect_provider_tool(tool):
    source_path = tool["_source_path"]
    revision = source_revision(tool) if source_path.is_dir() else None
    expected_revision = tool["source"]["pinned_revision"]
    states = tool["readiness"]["states"]
    provider_report = tool["_provider_report"]
    marker = provider_marker(tool)
    marker_matches = bool(
        marker
        and marker.get("tool_id") == tool["id"]
        and marker.get("source_revision") == expected_revision
        and marker.get("adapter_sha256") == manifest_sha256(tool)
        and marker.get("environment_fingerprint") == provider_fingerprint(tool)
    )
    import_ready = False
    import_error = None
    module = tool["provider"]["invocation"].get("module")
    if marker_matches and module:
        result = run_capture(
            [sys.executable, "-c", f"import {module.split('.')[0]}"],
            site_packages=provider_site_packages_path(tool),
        )
        import_ready = result.returncode == 0
        if not import_ready:
            import_error = result.stderr.strip() or result.stdout.strip()
    elif marker_matches:
        import_ready = True
    state = {
        "id": tool["id"],
        "display_name": tool["display_name"],
        "adapter_model": "provider",
        "provider_kind": tool["provider"]["kind"],
        "source_path": str(tool["source"]["path"]),
        "source_present": source_path.is_dir(),
        "source_revision": revision,
        "expected_revision": expected_revision,
        "pin_matches": revision == expected_revision,
        "source_clean": source_is_clean(tool) if source_path.is_dir() else False,
        "license_present": tool["_license_path"].is_file(),
        "environment_path": str(tool["provider"]["environment_path"]),
        "readiness_states": states,
        "fabrication_approved": False,
        "provider_report": provider_report,
        "environment_present": provider_environment_path(tool).is_dir(),
        "install_marker_matches": marker_matches,
        "installed_python": marker.get("python_version") if marker else None,
        "installed_package_count": len(marker.get("packages", [])) if marker else 0,
        "import_ready": import_ready,
        "import_error": import_error,
        "ready": False,
    }
    state["registered"] = all(
        [
            state["source_present"],
            state["pin_matches"],
            state["source_clean"],
            state["license_present"],
            "registered" in states,
        ]
    )
    state["ready"] = state["registered"] and marker_matches and import_ready and "invocation-ready" in states
    return state


def public_manifest(tool):
    return {key: value for key, value in tool.items() if not key.startswith("_")}


def helper_request_hash(request):
    payload = json.dumps(request, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def path_is_within_roots(path, roots):
    resolved = path.resolve()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def validate_helper_request(tool, request):
    require_mapping(request, ["schema_version", "tool_id", "request_type", "inputs", "outputs"], "Helper request")
    if request["schema_version"] != 1:
        fail(f"Unsupported helper request schema version: {request['schema_version']}")
    if request["tool_id"] != tool["id"]:
        fail(f"Helper request tool_id does not match adapter: {request['tool_id']} != {tool['id']}")
    if not TOOL_ID_PATTERN.fullmatch(request["request_type"]):
        fail(f"Invalid helper request type: {request['request_type']}")
    if not isinstance(request["inputs"], list) or not isinstance(request["outputs"], list):
        fail("Helper request inputs and outputs must be lists.")
    input_roots = tool["safety"].get("allowed_input_roots", [tool["source"]["path"]])
    allowed_input_roots = [safe_repo_path(root, f"Allowed input root for {tool['id']}") for root in input_roots]
    allowed_output_roots = [
        safe_repo_path(root, f"Allowed output root for {tool['id']}") for root in tool["safety"]["allowed_output_roots"]
    ]
    for value in request["inputs"]:
        path = safe_repo_path(value, f"Request input for {tool['id']}")
        if not path_is_within_roots(path, allowed_input_roots):
            fail(f"Request input for {tool['id']} is outside allowed input roots: {value}")
    for value in request["outputs"]:
        path = safe_repo_path(value, f"Request output for {tool['id']}")
        if not path_is_within_roots(path, allowed_output_roots):
            fail(f"Request output for {tool['id']} is outside allowed output roots: {value}")
    return {
        "tool_id": tool["id"],
        "request_hash": helper_request_hash(request),
        "input_count": len(request["inputs"]),
        "output_count": len(request["outputs"]),
    }


def validate_output_inventory(tool, inventory):
    if not isinstance(inventory, list):
        fail("Helper output inventory must be a list.")
    allowed_output_roots = [
        safe_repo_path(root, f"Allowed output root for {tool['id']}") for root in tool["safety"]["allowed_output_roots"]
    ]
    accepted_formats = set(tool["outputs"]["accepted_formats"])
    normalized = []
    for item in inventory:
        require_mapping(item, ["path", "format", "sha256"], f"Output inventory item for {tool['id']}")
        if item["format"] not in accepted_formats:
            fail(f"Output format for {tool['id']} is not accepted: {item['format']}")
        if not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]):
            fail(f"Output hash for {tool['id']} is not a SHA-256 digest: {item['path']}")
        path = safe_repo_path(item["path"], f"Output path for {tool['id']}")
        if not path_is_within_roots(path, allowed_output_roots):
            fail(f"Output path for {tool['id']} is outside allowed roots: {item['path']}")
        normalized.append({**item, "path": str(path.relative_to(REPO_ROOT))})
    expected = tool["outputs"].get("inventory")
    if expected is not None:
        required = {item["path"] for item in expected if item.get("required")}
        present = {item["path"] for item in normalized}
        missing = sorted(required - present)
        if missing:
            fail(f"Output inventory for {tool['id']} is missing required outputs: {', '.join(missing)}")
    return normalized


def snapshot_authoritative_outputs(paths):
    snapshot = {}
    for path in paths:
        resolved = safe_repo_path(path, "Authoritative output path")
        snapshot[str(resolved.relative_to(REPO_ROOT))] = resolved.read_bytes() if resolved.exists() else None
    return snapshot


def restore_authoritative_outputs(snapshot):
    for relative, content in snapshot.items():
        path = safe_repo_path(relative, "Authoritative output path")
        if content is None:
            if path.exists():
                path.unlink()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)


def run_with_output_preservation(output_paths, operation):
    snapshot = snapshot_authoritative_outputs(output_paths)
    try:
        return operation()
    except Exception:
        restore_authoritative_outputs(snapshot)
        raise


def setup_tool(tool):
    if tool.get("_adapter_model") == "provider":
        driver = safe_repo_path(tool["provider"]["invocation"]["driver"], f"Provider driver for {tool['id']}")
        result = subprocess.run(
            [sys.executable, str(driver), "setup", "--manifest", str(tool["_adapter_path"])],
            cwd=REPO_ROOT,
            check=False,
        )
        if result.returncode:
            fail(f"Provider setup failed for {tool['id']} with exit code {result.returncode}.")
        state = inspect_tool(tool)
        if not state["ready"]:
            fail(f"Provider setup completed but {tool['id']} did not pass readiness checks.")
        return state
    state = inspect_tool(tool)
    for key, message in [
        ("source_present", "source submodule is missing"),
        ("pin_matches", "source revision does not match the adapter pin"),
        ("source_clean", "source submodule has local modifications"),
        ("license_present", "declared license file is missing"),
        ("python_compatible", "host Python does not meet the declared minimum version"),
    ]:
        if not state[key]:
            fail(f"Cannot set up {tool['id']}: {message}.")

    destination = tool["_environment_path"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{tool['id']}-", dir=destination.parent))
    logging.info("Creating isolated environment for %s", tool["id"])
    try:
        site_packages = site_packages_path(stage)
        site_packages.mkdir()
        command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--target",
            str(site_packages),
            str(tool["_source_path"]),
        ]
        logging.info("Installing %s from pinned local submodule", tool["id"])
        result = subprocess.run(command, cwd=REPO_ROOT, check=False)
        if result.returncode:
            fail(f"Dependency installation failed for {tool['id']} with exit code {result.returncode}.")
        package_result = run_capture(
            [
                sys.executable,
                "-m",
                "pip",
                "list",
                "--path",
                str(site_packages),
                "--format",
                "json",
                "--disable-pip-version-check",
            ]
        )
        if package_result.returncode:
            fail(f"Could not record installed dependency versions for {tool['id']}.")
        packages = sorted(
            json.loads(package_result.stdout),
            key=lambda package: package["name"].lower(),
        )
        marker = {
            "schema_version": 1,
            "tool_id": tool["id"],
            "source_revision": tool["source"]["pinned_revision"],
            "adapter_sha256": manifest_sha256(tool),
            "python_version": ".".join(map(str, sys.version_info[:3])),
            "packages": packages,
        }
        (stage / INSTALL_MARKER).write_text(
            json.dumps(marker, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if destination.exists():
            shutil.rmtree(destination)
        os.replace(stage, destination)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    state = inspect_tool(tool)
    if not state["ready"]:
        fail(f"Setup completed but {tool['id']} did not pass readiness checks.")
    return state


def run_tool(tool, arguments):
    if tool.get("_adapter_model") == "provider":
        state = inspect_tool(tool)
        if not state["ready"]:
            fail(f"Helper tool {tool['id']} is not ready. Run: setup/bootstrap.sh run -- scripts/helper_tool.py setup {tool['id']}")
        if arguments and arguments[0] == "--":
            arguments = arguments[1:]
        driver = safe_repo_path(tool["provider"]["invocation"]["driver"], f"Provider driver for {tool['id']}")
        result = subprocess.run(
            [sys.executable, str(driver), "run", "--manifest", str(tool["_adapter_path"]), "--", *arguments],
            cwd=REPO_ROOT,
            check=False,
        )
        if not source_is_clean(tool):
            fail(f"Helper tool {tool['id']} modified its source submodule; output is rejected.")
        return result.returncode
    state = inspect_tool(tool)
    if not state["ready"]:
        fail(f"Helper tool {tool['id']} is not ready. Run: setup/bootstrap.sh run -- scripts/helper_tool.py setup {tool['id']}")
    if arguments and arguments[0] == "--":
        arguments = arguments[1:]
    command = [
        sys.executable,
        "-m",
        tool["runtime"]["module"],
        *arguments,
    ]
    logging.info("Running helper tool %s at revision %s", tool["id"], state["source_revision"])
    result = subprocess.run(
        command,
        cwd=tool["_working_directory"],
        check=False,
        env=python_path_environment(site_packages_path(tool["_environment_path"])),
    )
    if not source_is_clean(tool):
        fail(f"Helper tool {tool['id']} modified its source submodule; output is rejected.")
    return result.returncode


def parse_args():
    parser = argparse.ArgumentParser(description="Discover, validate, set up, and invoke pinned helper tools.")
    parser.add_argument("--verbose", action="store_true")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="List registered helper tools.")
    subparsers.add_parser("validate", help="Validate all helper-tool adapter manifests.")
    describe_parser = subparsers.add_parser("describe", help="Print a helper-tool manifest.")
    describe_parser.add_argument("tool")
    check_parser = subparsers.add_parser("check", help="Inspect helper-tool readiness.")
    check_parser.add_argument("tool")
    report_parser = subparsers.add_parser("report", help="Print helper-tool readiness report.")
    report_parser.add_argument("tool", nargs="?")
    setup_parser = subparsers.add_parser("setup", help="Create an isolated environment and install dependencies.")
    setup_parser.add_argument("tool")
    run_parser = subparsers.add_parser("run", help="Invoke a ready helper tool.")
    run_parser.add_argument("tool")
    run_parser.add_argument("arguments", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )
    try:
        if args.command == "list":
            tools = discover_tools()
            payload = [
                {
                    "id": tool["id"],
                    "display_name": tool["display_name"],
                    "capabilities": tool["capabilities"],
                    "adapter_model": tool.get("_adapter_model", "legacy_python_module"),
                    "provider_kind": tool.get("provider", {}).get("kind"),
                    "ready": inspect_tool(tool)["ready"],
                }
                for tool in tools.values()
            ]
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.command == "validate":
            tools = discover_tools()
            payload = {
                "adapter_count": len(tools),
                "adapters": [
                    {
                        "id": tool["id"],
                        "schema_version": tool["schema_version"],
                        "adapter_model": tool.get("_adapter_model", "legacy_python_module"),
                        "provider_kind": tool.get("provider", {}).get("kind"),
                    }
                    for tool in tools.values()
                ],
            }
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        if args.command == "report":
            tools = discover_tools()
            selected = tools.values() if args.tool is None else [get_tool(args.tool)]
            payload = [inspect_tool(tool) for tool in selected]
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 0
        tool = get_tool(args.tool)
        if args.command == "describe":
            print(json.dumps(public_manifest(tool), indent=2, sort_keys=True))
            return 0
        if args.command == "check":
            state = inspect_tool(tool)
            print(json.dumps(state, indent=2, sort_keys=True))
            return 0 if state["ready"] else 1
        if args.command == "setup":
            state = setup_tool(tool)
            print(json.dumps(state, indent=2, sort_keys=True))
            return 0
        if args.command == "run":
            return run_tool(tool, args.arguments)
        fail(f"Unsupported command: {args.command}")
    except ToolError as exc:
        logging.error("%s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
