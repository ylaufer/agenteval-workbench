from pathlib import Path

from agenteval.dataset.generator import generate_case


def main() -> None:
    case_dir = generate_case(
        case_id="demo_case",
        output_dir=Path("data/cases"),
        overwrite=True,
    )

    print(f"Demo case created at {case_dir}")


if __name__ == "__main__":
    main()
