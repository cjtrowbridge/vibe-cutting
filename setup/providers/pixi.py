from __future__ import annotations

from .base import BaseProvider


class PixiEnvironmentProvider(BaseProvider):
    kind = "pixi_environment"
    allowed_environment_roots = (".tools/environments",)

    def diagnostics(self) -> tuple[str, ...]:
        return (
            "pixi environment provider registered",
            "environment creation is deferred to tool-specific Phase 3+ setup drivers",
        )
