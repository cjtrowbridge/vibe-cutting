from __future__ import annotations

from .base import BaseProvider


class ManualOperatorProvider(BaseProvider):
    kind = "manual_operator"
    allowed_environment_roots = (".tools/environments", ".tmp/helper-tools")

    def diagnostics(self) -> tuple[str, ...]:
        return (
            "manual operator provider registered",
            "human-operated tools can produce reference evidence but cannot claim fabrication approval",
        )
