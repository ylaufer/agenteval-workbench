# Quickstart: Trace Ingestion Adapters

Get started with trace ingestion in 5 minutes.

## Installation

```bash
# Already installed if you have AgentEval
pip install -e .
```

## Quick Examples

### Example 1: Ingest a LangChain Trace

**Step 1**: Export your LangChain trace

```python
from langchain.callbacks.tracers import LangChainTracer
import json

tracer = LangChainTracer()
# ... run your agent with tracer ...
# After execution:
with open("langchain_trace.json", "w") as f:
    json.dump(tracer.runs[0].dict(), f, indent=2)
```

**Step 2**: Convert to AgentEval format

```bash
agenteval-ingest langchain_trace.json \
  --adapter langchain \
  --output data/cases/case_001/trace.json
```

**Step 3**: Add other required files

```bash
# Add prompt
echo "Your original agent prompt" > data/cases/case_001/prompt.txt

# Add expected outcome
cat > data/cases/case_001/expected_outcome.md << 'EOF'
---
primary_failure: None
severity: Low
tags: []
---

# Expected Outcome

The agent should successfully retrieve weather data and provide a response.
EOF
```

**Step 4**: Validate and evaluate

```bash
# Validate the complete case
agenteval-validate-dataset --repo-root .

# Run evaluation
agenteval-eval-runner

# Generate report
agenteval-eval-report
```

---

### Example 2: Ingest OpenTelemetry Traces

**Step 1**: Export OTel trace as JSON

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import json

# Configure OTel to export JSON
exporter = OTLPSpanExporter(
    endpoint="http://localhost:4318/v1/traces",  # Not used in offline mode
)

# Or use console exporter for debugging
console_exporter = ConsoleSpanExporter()

# ... instrument your agent ...
# Export spans to file manually or via collector
```

**Step 2**: Convert

```bash
agenteval-ingest otel_trace.json \
  --adapter otel \
  --output data/cases/case_002/trace.json
```

---

### Example 3: Ingest OpenAI API Responses

**Step 1**: Save your conversation

```python
import openai
import json

messages = [
    {"role": "user", "content": "What's the weather in Seattle?"},
]

response = openai.ChatCompletion.create(
    model="gpt-4o",
    messages=messages,
    tools=[{"type": "function", "function": {...}}],
)

# Save full conversation including tool calls
conversation = {
    "messages": messages + [response.choices[0].message]
}

# If there were tool calls, add tool responses
if response.choices[0].message.get("tool_calls"):
    # ... handle tool calls ...
    # conversation["messages"].append(tool_response)
    pass

with open("openai_trace.json", "w") as f:
    json.dump(conversation, f, indent=2)
```

**Step 2**: Convert

```bash
agenteval-ingest openai_trace.json \
  --adapter openai \
  --output data/cases/case_003/trace.json
```

---

### Example 4: Custom Format with Generic Adapter

**Step 1**: Create mapping configuration

```yaml
# my_mapping.yaml
version: "1.0"
metadata:
  format_name: "My Custom Agent"
  description: "Internal agent trace format"

mappings:
  steps:
    source_path: "$.events[*]"
    fields:
      step_type:
        from: "type"
        transform: "map"
        map:
          "reasoning": "thought"
          "action": "tool_call"
          "result": "observation"
      content:
        from: "data.message"
      timestamp:
        from: "timestamp"
        transform: "iso8601"
      tool_name:
        from: "data.tool"
        required_for: ["tool_call"]
      metadata:
        from: "context"
```

**Step 2**: Test mapping (dry-run)

```bash
agenteval-ingest my_trace.json \
  --adapter generic \
  --mapping my_mapping.yaml \
  --dry-run
```

**Step 3**: Convert

```bash
agenteval-ingest my_trace.json \
  --adapter generic \
  --mapping my_mapping.yaml \
  --output data/cases/case_004/trace.json
```

---

### Example 5: Bulk Ingest Directory

**Step 1**: Organize traces

```
exports/
├── trace_001.json
├── trace_002.json
├── trace_003.json
└── trace_004.json
```

**Step 2**: Bulk convert

```bash
agenteval-ingest ./exports/ \
  --adapter langchain \
  --output-dir data/cases/
```

This will create `case_001/`, `case_002/`, etc. with `trace.json` files.

**Step 3**: Add prompt and expected outcome to each case

```bash
for dir in data/cases/case_*/; do
  echo "Add your prompt" > "${dir}prompt.txt"
  cat > "${dir}expected_outcome.md" << 'EOF'
---
primary_failure: None
severity: Low
tags: []
---
# Expected Outcome
[Describe expected behavior]
EOF
done
```

---

## Common Workflows

### Workflow 1: Evaluate Production Agent Traces

1. **Export traces** from your production agent framework
2. **Convert** using appropriate adapter
3. **Add context**: Write `prompt.txt` and `expected_outcome.md`
4. **Validate**: Run `agenteval-validate-dataset`
5. **Evaluate**: Run `agenteval-eval-runner`
6. **Analyze**: Review reports and identify failures

### Workflow 2: Compare Agent Versions

1. **Export traces** from both versions (v1 and v2)
2. **Ingest** into separate case directories
3. **Evaluate** both sets
4. **Compare**: Use run comparison to see delta

### Workflow 3: Build Custom Benchmark

1. **Collect traces** from various failure scenarios
2. **Ingest** using appropriate adapters
3. **Categorize** by failure type in `expected_outcome.md`
4. **Validate** entire dataset
5. **Share**: Package as benchmark for team

---

## Troubleshooting

### "No adapter can handle input"

**Problem**: None of the adapters recognize your trace format

**Solutions**:
1. Check if your framework is supported (OTel, LangChain, CrewAI, OpenAI)
2. Use `--verbose` to see why each adapter rejected the input
3. Use the generic adapter with a custom mapping
4. Request a new adapter (file an issue)

### "Conversion failed: missing required field"

**Problem**: Input trace is missing data the adapter expects

**Solutions**:
1. Check that you exported the complete trace (not partial)
2. Verify your framework version is compatible
3. Use `--verbose` to see exactly which field is missing
4. Update your export code to include all required fields

### "Schema validation failed"

**Problem**: Converted trace doesn't match AgentEval schema

**Solutions**:
1. This is usually an adapter bug - file an issue
2. Check if your input has unusual structure
3. Try the generic adapter with explicit mappings

### "Security scan failed"

**Problem**: Converted trace contains secrets, URLs, or absolute paths

**Solutions**:
1. Sanitize your input trace before ingestion
2. Use generic adapter with transform rules to redact sensitive fields
3. Check your agent's output - it may be leaking sensitive data

---

## Next Steps

- Read the [Usage Guide](../docs/ingestion_usage.md) for detailed adapter documentation
- See [Mapping Reference](../docs/generic_mapping.md) for generic adapter configuration
- Browse [Example Mappings](../examples/mappings/) for common patterns
- Check [Troubleshooting](../docs/ingestion_troubleshooting.md) for detailed error guides
