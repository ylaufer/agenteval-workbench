from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .models import ConformanceResult


def write_json_report(result: ConformanceResult, path: str | Path) -> None:
    Path(path).write_text(json.dumps({
        "journey": result.journey,
        "passed": result.passed,
        "failures": result.failures,
        "metrics": result.metrics,
    }, indent=2), encoding="utf-8")


def write_markdown_report(result: ConformanceResult, path: str | Path) -> None:
    lines = [
        f"# Conformance Report: {result.journey}",
        "",
        f"- Passed: {result.passed}",
        "",
        "## Metrics",
    ]
    if result.metrics:
        lines.extend([f"- {k}: {v}" for k, v in result.metrics.items()])
    else:
        lines.append("- (none)")
    lines += ["", "## Failures"]
    if result.failures:
        lines.extend([f"- {failure}" for failure in result.failures])
    else:
        lines.append("- None")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write a telemetry conformance report.")
    parser.add_argument("--result-json", required=True, help="Path to a conformance result JSON file")
    parser.add_argument("--output-dir", required=True, help="Directory to write report files into")
    args = parser.parse_args()

    result_path = Path(args.result_json)
    if not result_path.exists():
        print(f"error: result file not found: {result_path}", file=sys.stderr)
        sys.exit(1)

    raw = json.loads(result_path.read_text(encoding="utf-8"))
    result = ConformanceResult(
        journey=raw["journey"],
        passed=raw["passed"],
        failures=raw["failures"],
        metrics=raw.get("metrics", {}),
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = result_path.stem
    write_json_report(result, out_dir / f"{stem}.report.json")
    write_markdown_report(result, out_dir / f"{stem}.report.md")
    print(f"reports written to {out_dir}")
