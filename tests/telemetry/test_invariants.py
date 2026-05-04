from pathlib import Path

from agenteval.telemetry.invariants import load_invariants


def test_load_invariants() -> None:
    config = load_invariants(Path("config/telemetry_journey_invariants.yaml"))
    assert config["journeys"][0]["name"] == "simple_rag_query"
