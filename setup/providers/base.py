from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import platform
import shutil
import tempfile
from typing import Any


PROVIDER_KINDS = {
    "pixi_environment",
    "openscad_library",
    "system_application",
    "manual_operator",
}

READINESS_STATES = (
    "registered",
    "dependencies-ready",
    "invocation-ready",
    "output-validated",
    "pipeline-integrated",
    "fabrication-approved",
)


class ProviderError(RuntimeError):
    pass


@dataclass(frozen=True)
class ProviderReport:
    kind: str
    state: str
    diagnostics: tuple[str, ...]
    environment_path: str
    working_directory: str
    platform: str
    platform_supported: bool
    environment_fingerprint: str
    lock_hashes: dict[str, str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "state": self.state,
            "diagnostics": list(self.diagnostics),
            "environment_path": self.environment_path,
            "working_directory": self.working_directory,
            "platform": self.platform,
            "platform_supported": self.platform_supported,
            "environment_fingerprint": self.environment_fingerprint,
            "lock_hashes": self.lock_hashes,
        }


class BaseProvider:
    kind = "base"
    allowed_environment_roots = (".tools/environments", ".tmp/helper-tools")

    def __init__(self, root: Path, manifest: dict[str, Any]):
        self.root = root.resolve()
        self.manifest = manifest
        self.provider = manifest["provider"]

    @property
    def tool_id(self) -> str:
        return self.manifest["id"]

    def repo_path(self, value: str, label: str) -> Path:
        path = Path(value)
        if path.is_absolute():
            raise ProviderError(f"{label} must be repository-relative: {value}")
        resolved = (self.root / path).resolve()
        try:
            resolved.relative_to(self.root)
        except ValueError as error:
            raise ProviderError(f"{label} escapes the repository: {value}") from error
        return resolved

    def require_environment_root(self) -> Path:
        environment = self.repo_path(self.provider["environment_path"], "provider environment path")
        for allowed_root in self.allowed_environment_roots:
            root = (self.root / allowed_root).resolve()
            try:
                environment.relative_to(root)
                return environment
            except ValueError:
                continue
        raise ProviderError(
            "provider environment path must be under "
            + " or ".join(self.allowed_environment_roots)
        )

    def platform_tag(self) -> str:
        system = platform.system().lower() or "unknown"
        machine = platform.machine().lower() or "unknown"
        return f"{system}-{machine}"

    def platform_supported(self) -> bool:
        platforms = self.provider.get("platforms")
        if not platforms:
            return True
        return self.platform_tag() in platforms

    def lock_hashes(self) -> dict[str, str]:
        setup = self.provider.get("setup", {})
        lock_files = []
        if "lock_file" in setup:
            lock_files.append(setup["lock_file"])
        lock_files.extend(setup.get("lock_files", []))
        hashes = {}
        for value in lock_files:
            path = self.repo_path(value, "provider lock file")
            hashes[str(path.relative_to(self.root))] = sha256_file(path) if path.is_file() else "missing"
        return hashes

    def environment_fingerprint(self) -> str:
        payload = {
            "kind": self.kind,
            "source_revision": self.manifest["source"]["pinned_revision"],
            "provider": self.provider,
            "lock_hashes": self.lock_hashes(),
        }
        return stable_hash(payload)

    def cache_root(self) -> Path:
        return self.repo_path(
            self.provider.get("setup", {}).get("cache_path", f".tools/cache/helpers/{self.tool_id}"),
            "provider cache path",
        )

    def temp_root(self) -> Path:
        return self.repo_path(
            self.provider.get("setup", {}).get("temp_path", f".tools/tmp/helpers/{self.tool_id}"),
            "provider temporary path",
        )

    def log_root(self) -> Path:
        return self.repo_path(
            self.provider.get("setup", {}).get("log_path", f".tools/logs/helpers/{self.tool_id}"),
            "provider log path",
        )

    def staging_root(self) -> Path:
        return self.repo_path(
            self.provider.get("setup", {}).get("staging_path", f".tools/staging/helpers/{self.tool_id}"),
            "provider staging path",
        )

    def cleanup_incomplete_staging(self) -> None:
        staging = self.staging_root()
        if staging.exists():
            shutil.rmtree(staging)
        staging.mkdir(parents=True, exist_ok=True)

    def prepare_scaffold(self) -> dict[str, Any]:
        if not self.platform_supported():
            raise ProviderError(f"provider platform is unsupported: {self.platform_tag()}")
        environment = self.require_environment_root()
        fingerprint = self.environment_fingerprint()
        self.cleanup_incomplete_staging()
        self.cache_root().mkdir(parents=True, exist_ok=True)
        self.temp_root().mkdir(parents=True, exist_ok=True)
        self.log_root().mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f"{self.tool_id}-", dir=self.staging_root()) as stage_text:
            stage = Path(stage_text)
            marker = {
                "schema_version": 1,
                "tool_id": self.tool_id,
                "provider_kind": self.kind,
                "source_revision": self.manifest["source"]["pinned_revision"],
                "environment_fingerprint": fingerprint,
                "lock_hashes": self.lock_hashes(),
                "platform": self.platform_tag(),
                "state": "registered",
            }
            (stage / "provider-ready.json").write_text(
                json.dumps(marker, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            environment.mkdir(parents=True, exist_ok=True)
            destination = environment / fingerprint
            if destination.exists():
                shutil.rmtree(destination)
            shutil.copytree(stage, destination)
        self.cleanup_incomplete_staging()
        return marker

    def smoke_test(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "provider_kind": self.kind,
            "platform_supported": self.platform_supported(),
            "environment_fingerprint": self.environment_fingerprint(),
        }

    def validate(self) -> ProviderReport:
        environment = self.require_environment_root()
        working_directory = self.repo_path(self.provider["working_directory"], "provider working directory")
        return ProviderReport(
            kind=self.kind,
            state="registered",
            diagnostics=tuple(self.diagnostics()),
            environment_path=str(environment.relative_to(self.root)),
            working_directory=str(working_directory.relative_to(self.root)),
            platform=self.platform_tag(),
            platform_supported=self.platform_supported(),
            environment_fingerprint=self.environment_fingerprint(),
            lock_hashes=self.lock_hashes(),
        )

    def diagnostics(self) -> tuple[str, ...]:
        return ("provider registered; setup hooks are scaffolded for later phases",)


def provider_for_manifest(root: Path, manifest: dict[str, Any]) -> BaseProvider:
    kind = manifest.get("provider", {}).get("kind")
    if kind == "pixi_environment":
        from .pixi import PixiEnvironmentProvider

        return PixiEnvironmentProvider(root, manifest)
    if kind == "openscad_library":
        from .openscad import OpenScadLibraryProvider

        return OpenScadLibraryProvider(root, manifest)
    if kind == "system_application":
        from .system_application import SystemApplicationProvider

        return SystemApplicationProvider(root, manifest)
    if kind == "manual_operator":
        from .manual_operator import ManualOperatorProvider

        return ManualOperatorProvider(root, manifest)
    raise ProviderError(f"unsupported helper provider kind: {kind}")


def validate_provider_manifest(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    return provider_for_manifest(root, manifest).validate().as_dict()


def stable_hash(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
