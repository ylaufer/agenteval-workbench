from __future__ import annotations

from agenteval.core.runner import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            [
                "--dataset-dir",
                "data/cases",
                "--output-dir",
                "reports",
            ]
        )
    )
