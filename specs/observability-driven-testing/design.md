# Design

Modules:
- models: internal trace schema
- loader: JSON ingestion
- redaction: value and field redaction
- validators: semantic checks
- invariants: YAML spec parser
- engine: conformance evaluator
- reporters: markdown summary

Flow:
load raw -> redact -> normalize -> validate -> evaluate invariants -> report
