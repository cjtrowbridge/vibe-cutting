from __future__ import annotations

from .base import BaseProvider


class OpenScadLibraryProvider(BaseProvider):
    kind = "openscad_library"
    allowed_environment_roots = (".tools/environments", ".tmp/helper-tools")

    def diagnostics(self) -> tuple[str, ...]:
        return (
            "openscad library provider registered",
            "executable detection and library path binding are scaffolded for later phases",
        )
