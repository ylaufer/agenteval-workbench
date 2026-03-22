from pathlib import Path

from agenteval.core.execution import build_demo_trace, save_trace


def main() -> None:
    trace = build_demo_trace(
        "What is the capital of France?",
        task_id="demo_case",
    )

    output_path = Path("data/cases/demo_case/trace.json")
    save_trace(trace, output_path)

    print(f"Trace written to {output_path}")


if __name__ == "__main__":
    main()
