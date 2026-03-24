"""OpenTelemetry OTLP JSON adapter."""

from __future__ import annotations

from datetime import datetime

from agenteval.ingestion.base import TraceAdapter, map_step_type, parse_timestamp
from agenteval.schemas.trace import Trace

# Mapping from OTel span kinds to AgentEval step types
SPAN_KIND_TO_STEP_TYPE = {
    "SPAN_KIND_INTERNAL": "thought",  # Internal processing/reasoning
    "SPAN_KIND_CLIENT": "tool_call",  # Outbound call to external service
    "SPAN_KIND_SERVER": "observation",  # Inbound response (rare in agent traces)
    "SPAN_KIND_PRODUCER": "tool_call",  # Message producer
    "SPAN_KIND_CONSUMER": "observation",  # Message consumer
}


class OTelAdapter:
    """Adapter for OpenTelemetry OTLP JSON traces."""

    def can_handle(self, raw: dict) -> bool:
        """Check if input is an OTel trace.

        Args:
            raw: Parsed JSON object

        Returns:
            True if this looks like an OTel trace
        """
        try:
            return (
                "resourceSpans" in raw
                and isinstance(raw["resourceSpans"], list)
                and len(raw["resourceSpans"]) > 0
            )
        except (KeyError, TypeError):
            return False

    def convert(self, raw: dict) -> Trace:
        """Convert OTel trace to AgentEval format.

        Args:
            raw: OTel OTLP JSON trace

        Returns:
            AgentEval Trace dict

        Raises:
            ValueError: If conversion fails
        """
        if not self.can_handle(raw):
            raise ValueError("Input is not a valid OTel trace")

        steps = []
        actor_id = None

        # Extract spans from nested structure
        for resource_span in raw["resourceSpans"]:
            # Try to extract service name as actor_id
            if not actor_id:
                for attr in resource_span.get("resource", {}).get("attributes", []):
                    if attr.get("key") == "service.name":
                        actor_id = attr.get("value", {}).get("stringValue")
                        break

            for scope_span in resource_span.get("scopeSpans", []):
                for span in scope_span.get("spans", []):
                    step = self._convert_span(span)
                    if actor_id:
                        step["actor_id"] = actor_id
                    steps.append(step)

        # Sort steps by timestamp (deterministic ordering)
        steps.sort(key=lambda s: s["timestamp"])

        # Extract traceId for metadata
        trace_id = "unknown"
        if raw["resourceSpans"] and raw["resourceSpans"][0].get("scopeSpans"):
            scope_spans = raw["resourceSpans"][0]["scopeSpans"]
            if scope_spans and scope_spans[0].get("spans"):
                trace_id = scope_spans[0]["spans"][0].get("traceId", "unknown")

        # Get timestamp from first step
        timestamp = steps[0]["timestamp"] if steps else datetime.now().isoformat() + "Z"

        # Build trace matching AgentEval schema
        trace: Trace = {
            "task_id": trace_id,  # Use OTel traceId as task_id
            "user_prompt": "Ingested from OpenTelemetry trace",  # Placeholder
            "model_version": "unknown",  # Not available in OTel traces
            "steps": steps,
            "metadata": {
                "timestamp": timestamp,
                "environment": {
                    "source": "otel",
                    "otel_trace_id": trace_id,
                    "otel_version": "1.0",
                },
            },
        }

        return trace

    def _convert_span(self, span: dict) -> dict:
        """Convert a single OTel span to an AgentEval step.

        Args:
            span: OTel span dict

        Returns:
            AgentEval step dict

        Raises:
            ValueError: If span is missing required fields
        """
        if "spanId" not in span:
            raise ValueError("Span missing required field 'spanId'")

        if "startTimeUnixNano" not in span:
            raise ValueError("Span missing required field 'startTimeUnixNano'")

        # Determine step type from span kind
        span_kind = span.get("kind", "SPAN_KIND_INTERNAL")
        step_type = map_step_type(span_kind, SPAN_KIND_TO_STEP_TYPE)

        # Extract content from attributes
        content = self._extract_content(span, step_type)

        # Build step matching AgentEval schema
        step = {
            "step_id": span["spanId"],
            "type": step_type,  # Required: use "type" not "step_type"
            "content": content,
            "timestamp": parse_timestamp(int(span["startTimeUnixNano"])),
            "event_id": span["spanId"],  # Optional: stable event identifier
        }

        # Add parent relationship
        if span.get("parentSpanId"):
            step["parent_event_id"] = span["parentSpanId"]

        # Add latency if available
        if "endTimeUnixNano" in span:
            start_ns = int(span["startTimeUnixNano"])
            end_ns = int(span["endTimeUnixNano"])
            latency_ms = (end_ns - start_ns) / 1_000_000  # Convert nanos to millis
            step["latency_ms"] = round(latency_ms, 2)

        # Add tool name if this is a tool call
        if step_type == "tool_call":
            tool_name = self._extract_tool_name(span)
            if tool_name:
                step["tool_name"] = tool_name

        return step

    def _extract_content(self, span: dict, step_type: str) -> str:
        """Extract content from span attributes.

        Args:
            span: OTel span dict
            step_type: Determined step type

        Returns:
            Content string
        """
        attributes = span.get("attributes", [])

        # Look for common attribute keys based on step type
        if step_type == "thought":
            for attr in attributes:
                if attr.get("key") in ["thought", "reasoning", "message"]:
                    return attr.get("value", {}).get("stringValue", "")

        elif step_type == "tool_call":
            for attr in attributes:
                if attr.get("key") == "tool.input":
                    return attr.get("value", {}).get("stringValue", "")

        elif step_type == "observation":
            for attr in attributes:
                if attr.get("key") == "tool.output":
                    return attr.get("value", {}).get("stringValue", "")

        elif step_type == "final_answer":
            for attr in attributes:
                if attr.get("key") in ["answer", "response", "output"]:
                    return attr.get("value", {}).get("stringValue", "")

        # Fallback: use span name
        return span.get("name", "")

    def _extract_tool_name(self, span: dict) -> str | None:
        """Extract tool name from span attributes.

        Args:
            span: OTel span dict

        Returns:
            Tool name or None
        """
        attributes = span.get("attributes", [])
        for attr in attributes:
            if attr.get("key") == "tool.name":
                return attr.get("value", {}).get("stringValue")

        # Fallback to span name
        return span.get("name")

    def validate_mapping(self, raw: dict) -> list[str]:
        """Validate OTel trace and return warnings.

        Args:
            raw: OTel trace dict

        Returns:
            List of warning messages
        """
        warnings = []

        if not self.can_handle(raw):
            warnings.append("Input does not appear to be a valid OTel trace")
            return warnings

        # Check for service name (becomes actor_id)
        has_service_name = False
        for resource_span in raw.get("resourceSpans", []):
            for attr in resource_span.get("resource", {}).get("attributes", []):
                if attr.get("key") == "service.name":
                    has_service_name = True
                    break

        if not has_service_name:
            warnings.append("No 'service.name' attribute found (actor_id will be empty)")

        return warnings
