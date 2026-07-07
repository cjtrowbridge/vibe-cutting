from __future__ import annotations

from .base import BaseProvider


class SystemApplicationProvider(BaseProvider):
    kind = "system_application"
    allowed_environment_roots = (".tools/environments", ".tmp/helper-tools")

    def diagnostics(self) -> tuple[str, ...]:
        return (
            "system application provider registered",
            "automatic privileged installation is prohibited; diagnostics must give manual remediation",
        )
