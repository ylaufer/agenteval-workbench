from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import yaml  # type: ignore[import-untyped]


def load_invariants(path: str | Path) -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(Path(path).read_text(encoding="utf-8")))
