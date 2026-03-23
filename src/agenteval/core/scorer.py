"""Auto-scoring orchestrator and CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agenteval.core.evaluators import EvaluatorRegistry
from agenteval.core.loader import load_rubric, load_trace
from agenteval.core.tagger import tag_trace
from agenteval.core.types import AutoEvaluation, DimensionScoreResult, Rubric
from agenteval.dataset.validator import _get_repo_root, _safe_resolve_within


def default_registry() -> EvaluatorRegistry:
    """Create a registry with all built-in evaluators.

    Rule-based evaluators (tool_use, security_safety) are always included.
    LLM-based evaluators are included only when an API key env var is set
    (ANTHROPIC_API_KEY or OPENAI_API_KEY).
    """
    import os

    from agenteval.core.evaluators.tool_use import ToolUseEvaluator
    from agenteval.core.evaluators.security import SecurityEvaluator

    registry = EvaluatorRegistry()
    registry.register(ToolUseEvaluator())
    registry.register(SecurityEvaluator())

    # Optionally register LLM evaluators for subjective dimensions
    _register_llm_evaluators(registry, os.environ)

    return registry


def _register_llm_evaluators(
    registry: EvaluatorRegistry,
    environ: dict[str, str],
) -> None:
    """Register LLM evaluators if an API key is available."""
    from agenteval.core.evaluators.llm_evaluator import LLMEvaluator
    from agenteval.core.evaluators.llm_provider import AnthropicProvider, OpenAIProvider

    # Subjective dimensions that benefit from LLM evaluation
    llm_dimensions = ("accuracy", "completeness", "reasoning_quality", "ui_grounding")

    provider = None
    if environ.get(AnthropicProvider.ENV_KEY):
        provider = AnthropicProvider()
    elif environ.get(OpenAIProvider.ENV_KEY):
        provider = OpenAIProvider()

    if provider is None:
        return

    for dim_name in llm_dimensions:
        registry.register(LLMEvaluator(provider=provider, dimension_name=dim_name))


def score_case(
    case_dir: Path,
    rubric: Rubric,
    registry: EvaluatorRegistry | None = None,
) -> dict[str, Any]:
    """Score a single case. Returns AutoEvaluation dict.

    If registry is None, uses the default registry with all built-in evaluators.
    Loads trace.json from case_dir, scores all registered dimensions,
    returns structured auto-evaluation dict.
    """
    if registry is None:
        registry = default_registry()

    trace_path = case_dir / "trace.json"
    trace = load_trace(trace_path=trace_path)
    auto_tags = tag_trace(trace)

    dim_results = registry.score_all(trace, rubric)

    # Include unregistered dimensions as unevaluated
    registered = set(dim_results.keys())
    for dim in rubric.dimensions:
        if dim.name not in registered:
            dim_results[dim.name] = DimensionScoreResult(
                dimension_name=dim.name,
                score=None,
                weight=dim.weight,
                scale=dim.scale,
                evidence_step_ids=(),
                notes="No evaluator registered for this dimension.",
                evaluator_type="rule",
                error="no_evaluator",
            )

    now = datetime.now(timezone.utc).isoformat()
    case_id = case_dir.name

    evaluation = AutoEvaluation(
        case_id=case_id,
        scoring_type="auto",
        rubric_version=rubric.version,
        dimensions=dim_results,
        auto_tags=auto_tags,
        metadata={"timestamp": now, "model": None},
    )
    return _to_json_compatible(asdict(evaluation))


def _to_json_compatible(obj: Any) -> Any:
    """Convert tuples to lists recursively for JSON schema compatibility."""
    if isinstance(obj, dict):
        return {k: _to_json_compatible(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_compatible(item) for item in obj]
    return obj


def score_dataset(
    dataset_dir: Path,
    output_dir: Path,
    rubric_path: Path | None = None,
    registry: EvaluatorRegistry | None = None,
) -> list[dict[str, Any]]:
    """Score all cases in a dataset directory.

    Writes {case_id}.auto_evaluation.json to output_dir for each case.
    Returns list of AutoEvaluation dicts.
    """
    repo_root = _get_repo_root()
    if rubric_path is None:
        rubric_path = repo_root / "rubrics" / "v1_agent_general.json"

    rubric = load_rubric(rubric_path=rubric_path)

    if registry is None:
        registry = default_registry()

    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    case_dirs = sorted(
        (entry for entry in dataset_dir.iterdir() if entry.is_dir()),
        key=lambda p: p.name,
    )

    for case_dir in case_dirs:
        trace_path = case_dir / "trace.json"
        if not trace_path.exists():
            continue
        try:
            result = score_case(case_dir, rubric, registry)
            out_path = output_dir / f"{case_dir.name}.auto_evaluation.json"
            out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            results.append(result)
        except Exception as exc:
            print(f"{case_dir.name}: scoring error: {exc}", file=sys.stderr)

    return results


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for agenteval-auto-score."""
    parser = argparse.ArgumentParser(description="Auto-score benchmark cases.")
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=None,
        help="Path to dataset directory (default: data/cases)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for auto-evaluation files (default: reports)",
    )
    parser.add_argument(
        "--rubric",
        type=str,
        default=None,
        help="Path to rubric JSON file",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["rule", "llm", "all"],
        default="rule",
        help="Scoring strategy filter (default: rule)",
    )

    args = parser.parse_args(argv)
    repo_root = _get_repo_root()

    dataset_dir = Path(args.dataset_dir) if args.dataset_dir else repo_root / "data" / "cases"
    output_dir = Path(args.output_dir) if args.output_dir else repo_root / "reports"
    rubric_path = Path(args.rubric) if args.rubric else None

    dataset_dir = _safe_resolve_within(repo_root, dataset_dir)
    output_dir = _safe_resolve_within(repo_root, output_dir)
    if rubric_path is not None:
        rubric_path = _safe_resolve_within(repo_root, rubric_path)

    if not dataset_dir.exists():
        print(f"Error: Dataset directory not found: {dataset_dir}", file=sys.stderr)
        return 2

    registry = default_registry()

    results = score_dataset(
        dataset_dir=dataset_dir,
        output_dir=output_dir,
        rubric_path=rubric_path,
        registry=registry,
    )

    if not results:
        print("No cases found to score.")
        return 0

    # Print summary
    failed_cases = 0
    print(f"\nAuto-scored {len(results)} case(s):")
    for r in results:
        dims = r.get("dimensions", {})
        scored = sum(1 for d in dims.values() if isinstance(d, dict) and d.get("score") is not None)
        total = len(dims)
        scored_names = [
            f"{name}={d['score']}"
            for name, d in dims.items()
            if isinstance(d, dict) and d.get("score") is not None
        ]
        detail = ", ".join(scored_names) if scored_names else "none"
        print(f"  {r['case_id']}: {scored}/{total} dimensions scored ({detail})")
        if scored == 0:
            failed_cases += 1

    print(f"\nResults written to {output_dir}")

    return 1 if failed_cases > 0 else 0
