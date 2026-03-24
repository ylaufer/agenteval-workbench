"""CLI for trace ingestion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from agenteval.ingestion import auto_detect_adapter, get_adapter_by_name
from agenteval.ingestion.base import check_file_size, fail_fast_validator

# Use simple ASCII characters for Windows compatibility
CHECK = "OK"
WARN = "WARNING"
ERROR = "ERROR"
FAIL = "FAILED"


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser.

    Returns:
        Configured argument parser
    """
    parser = argparse.ArgumentParser(
        prog="agenteval-ingest",
        description="Convert traces from external agent frameworks to AgentEval format",
    )

    parser.add_argument(
        "input",
        type=str,
        help="Path to input trace file or directory",
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output file path (required for single file ingestion)",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        help="Output directory (required for bulk ingestion)",
    )

    parser.add_argument(
        "--adapter",
        type=str,
        default="auto",
        choices=["auto", "otel", "langchain", "crewai", "openai", "generic"],
        help="Adapter to use (default: auto-detect)",
    )

    parser.add_argument(
        "--mapping",
        type=str,
        help="Mapping config file (required for generic adapter)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate mapping without converting",
    )

    parser.add_argument(
        "--repo-root",
        type=str,
        help="Repository root (auto-detected from git if not specified)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed conversion logs",
    )

    return parser


def ingest_single_file(
    input_path: Path,
    output_path: Path,
    adapter_name: str,
    mapping_path: Path | None,
    dry_run: bool,
    verbose: bool,
) -> int:
    """Ingest a single trace file.

    Args:
        input_path: Input file path
        output_path: Output file path
        adapter_name: Adapter to use ("auto" for auto-detection)
        mapping_path: Path to mapping config (for generic adapter)
        dry_run: If True, validate only without writing output
        verbose: If True, show detailed logs

    Returns:
        Exit code (0 = success, non-zero = error)
    """
    try:
        # Check file size
        can_continue, size_message = check_file_size(input_path)
        if not can_continue:
            print(f"ERROR: {size_message}", file=sys.stderr)
            return 8  # File size exceeds hard limit

        if size_message and verbose:
            print(f"[WARN] {size_message}")

        # Load input
        with open(input_path, "r", encoding="utf-8") as f:
            raw = json.load(f)

        if verbose:
            print(f"[OK] Loaded input file: {input_path}")

        # Get adapter
        if adapter_name == "auto":
            adapter = auto_detect_adapter(raw)
            if not adapter:
                print(
                    f"ERROR: No adapter can handle input file: {input_path}",
                    file=sys.stderr,
                )
                print("\nTried adapters: (none registered yet)", file=sys.stderr)
                print("\nHints:", file=sys.stderr)
                print("  - For OpenTelemetry: check for 'resourceSpans' field", file=sys.stderr)
                print("  - For LangChain: check for 'runs' field", file=sys.stderr)
                print("  - For CrewAI: check for 'tasks' field", file=sys.stderr)
                print("  - For OpenAI: check for 'messages' array", file=sys.stderr)
                print(
                    "  - For custom formats: use --adapter generic --mapping <config>",
                    file=sys.stderr,
                )
                return 3  # No adapter can handle input
            if verbose:
                print(f"[OK] Detected format: {adapter.__class__.__name__}")
        else:
            adapter = get_adapter_by_name(adapter_name)
            if not adapter:
                print(f"ERROR: Adapter '{adapter_name}' not found", file=sys.stderr)
                return 3
            if verbose:
                print(f"[OK] Using adapter: {adapter.__class__.__name__}")

        # Validate mapping (collect warnings)
        warnings = adapter.validate_mapping(raw)
        if warnings:
            for warning in warnings:
                print(f"[WARN] Warning: {warning}")

        if dry_run:
            print("[OK] Dry-run validation succeeded")
            return 0

        # Convert
        trace = adapter.convert(raw)
        if verbose:
            step_count = len(trace.get("steps", []))
            print(f"[OK] Converted to {step_count} steps")

        # Validate (fail-fast on schema errors)
        try:
            fail_fast_validator(trace)
            if verbose:
                print("[OK] Validated against trace schema")
        except ValueError as e:
            print(f"ERROR: Schema validation failed: {e}", file=sys.stderr)
            return 5  # Schema validation failed

        # Write output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(trace, f, indent=2)

        print(f"[OK] Wrote trace to {output_path}")
        return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2  # Input file not found
    except ValueError as e:
        print(f"ERROR: Conversion failed: {e}", file=sys.stderr)
        return 4  # Conversion failed
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        if verbose:
            import traceback

            traceback.print_exc()
        return 1  # General error


def ingest_bulk(
    input_dir: Path,
    output_dir: Path,
    adapter_name: str,
    mapping_path: Path | None,
    verbose: bool,
) -> int:
    """Ingest multiple trace files from a directory.

    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        adapter_name: Adapter to use
        mapping_path: Path to mapping config (for generic adapter)
        verbose: If True, show detailed logs

    Returns:
        Exit code (0 = all succeeded, 1 = some failed)
    """
    # Find all JSON files in input directory
    json_files = list(input_dir.glob("*.json"))

    if not json_files:
        print(f"ERROR: No JSON files found in {input_dir}", file=sys.stderr)
        return 2

    print(f"Found {len(json_files)} trace files in {input_dir}")

    success_count = 0
    failure_count = 0

    # TODO: Add progress bar (tqdm) - T010
    for i, input_file in enumerate(json_files, 1):
        if verbose:
            print(f"\n[{i}/{len(json_files)}] Processing {input_file.name}...")

        # Create output filename (case_NNN/trace.json)
        output_subdir = output_dir / f"case_{i:03d}"
        output_file = output_subdir / "trace.json"

        # Process file (continue on errors)
        exit_code = ingest_single_file(
            input_file,
            output_file,
            adapter_name,
            mapping_path,
            dry_run=False,
            verbose=False,  # Suppress verbose in bulk mode
        )

        if exit_code == 0:
            success_count += 1
            print(f"[OK] Converted {input_file.name} → {output_file}")
        else:
            failure_count += 1
            print(f"[FAIL] Failed {input_file.name}")

    # Print summary
    print(f"\nSummary: [OK] {success_count}/{len(json_files)} traces converted successfully. {failure_count} failed.")

    return 0 if failure_count == 0 else 1


def main(argv: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)

    # Validate input
    if not input_path.exists():
        print(f"ERROR: Input path not found: {input_path}", file=sys.stderr)
        return 2

    # Determine mode: single file or bulk
    if input_path.is_file():
        # Single file mode
        if not args.output:
            print("ERROR: --output is required for single file ingestion", file=sys.stderr)
            return 1

        output_path = Path(args.output)
        mapping_path = Path(args.mapping) if args.mapping else None

        return ingest_single_file(
            input_path,
            output_path,
            args.adapter,
            mapping_path,
            args.dry_run,
            args.verbose,
        )

    elif input_path.is_dir():
        # Bulk mode
        if not args.output_dir:
            print("ERROR: --output-dir is required for bulk ingestion", file=sys.stderr)
            return 1

        output_dir = Path(args.output_dir)
        mapping_path = Path(args.mapping) if args.mapping else None

        return ingest_bulk(
            input_path,
            output_dir,
            args.adapter,
            mapping_path,
            args.verbose,
        )

    else:
        print(f"ERROR: Input must be a file or directory: {input_path}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
