# Data Processing Pipeline

A complete LeafMesh example that chains four agents to validate, transform, enrich, and report on incoming data. This demonstrates programmatic agents, LLM agents, conditional routing, and the pre-compose pipeline.

## Pipeline Overview

```
Raw Data Input
    │
    ▼
┌─────────────┐  condition: is_valid == true  ┌──────────────┐
│  Validator   │────────────────────────────▶  │  Transformer  │
│ (programmatic)│                               │ (programmatic) │
│              │  condition: is_valid == false  │               │
│ yields:      │───────▶ [pipeline stops]      │ yields:       │
│  is_valid    │                               │  transformed  │
│  errors      │                               │  record_count │
└─────────────┘                               └───────┬───────┘
                                                       │
                                    condition: record_count > 0
                                                       │
                                                       ▼
                                              ┌──────────────┐
                                              │   Reporter    │
                                              │  (gpt-4o-mini)│
                                              │               │
                                              │ yields:       │
                                              │  summary      │
                                              │  quality_grade│
                                              └──────────────┘
```

Three agents, fully declarative routing. The validator and transformer are programmatic (no LLM calls). The reporter uses an LLM to generate a human-readable summary.

## YAML Configuration

Create `data_pipeline.yaml`:

```yaml
name: "data_pipeline"
version: "1.0.0"
architecture: "managed_mesh"

redis:
  host: "localhost"
  port: 6379
  db: 0
  session_ttl: 3600

manager:
  enabled: true
  model: "gpt-4o-mini"
  coordination_rules:
    max_response_time: 30

mesh:
  call_timeout: 60
  max_retries: 2

# Observability: auto-enabled by LEAFMESH_LICENSE_KEY (no YAML config needed)

agents:
  # Step 1: Validate incoming data (no LLM)
  validator:
    name: "validator"
    agent_type: "programmatic"
    yields:
      is_valid: "boolean"
      errors: "array"
      cleaned_records: "array"
      raw_count: "number"
    can_call:
      - agent: "transformer"
        condition: "is_valid == true"
        call_immediately: true

  # Step 2: Transform and aggregate (no LLM)
  transformer:
    name: "transformer"
    agent_type: "programmatic"
    yields:
      transformed: "array"
      record_count: "number"
      aggregations: "object"
    can_call:
      - agent: "reporter"
        condition: "record_count > 0"

  # Step 3: Generate human-readable summary (LLM)
  reporter:
    name: "reporter"
    model: "gpt-4o-mini"
    temperature: 0.3
    max_tokens: 500
    prompt: |
      You summarize data processing results.
      Given aggregated data, write a brief, clear report.
      Include the record count, key statistics, and a quality grade (A/B/C/D/F).
    yields:
      summary: "string"
      quality_grade: "string"
```

## Python Implementation

Create `data_pipeline.py`:

```python
import asyncio
from datetime import datetime
from leafmesh import LeafMesh

leafmesh = LeafMesh.from_yaml("data_pipeline.yaml")


# --- Agent 1: Validator ---
# Function name "validator" matches the YAML agent name — auto_discover finds it

async def validator(llm_response, input_data, context):
    """Validate incoming records — pure Python, no LLM"""

    records = input_data.get("records", [])
    errors = []
    cleaned = []

    for i, record in enumerate(records):
        record_errors = []

        # Check required fields
        if "name" not in record:
            record_errors.append(f"Record {i}: missing 'name'")
        if "value" not in record:
            record_errors.append(f"Record {i}: missing 'value'")
        elif not isinstance(record["value"], (int, float)):
            record_errors.append(f"Record {i}: 'value' must be a number, got {type(record['value']).__name__}")

        # Check value range
        if "value" in record and isinstance(record["value"], (int, float)):
            if record["value"] < 0 or record["value"] > 10000:
                record_errors.append(f"Record {i}: value {record['value']} out of range [0, 10000]")

        if record_errors:
            errors.extend(record_errors)
        else:
            cleaned.append(record)

    return {
        "is_valid": len(cleaned) > 0,
        "errors": errors,
        "cleaned_records": cleaned,
        "raw_count": len(records)
    }


# --- Agent 2: Transformer ---
# Function name "transformer" matches the YAML agent name — auto_discover finds it

async def transformer(llm_response, input_data, context):
    """Transform and aggregate validated records — pure Python"""

    records = input_data.get("cleaned_records", [])

    if not records:
        return {"transformed": [], "record_count": 0, "aggregations": {}}

    # Normalize values to 0-100 scale
    values = [r["value"] for r in records]
    max_val = max(values) if values else 1
    min_val = min(values) if values else 0
    range_val = max_val - min_val if max_val != min_val else 1

    transformed = []
    for record in records:
        normalized = ((record["value"] - min_val) / range_val) * 100
        transformed.append({
            "name": record["name"],
            "original_value": record["value"],
            "normalized_value": round(normalized, 2),
            "timestamp": datetime.now().isoformat()
        })

    # Compute aggregations
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std_dev = variance ** 0.5

    return {
        "transformed": transformed,
        "record_count": len(transformed),
        "aggregations": {
            "mean": round(mean, 2),
            "std_dev": round(std_dev, 2),
            "min": min_val,
            "max": max_val,
            "count": len(values)
        }
    }


# --- Agent 3: Reporter (LLM generates summary) ---
# Function name "reporter" matches the YAML agent name — auto_discover finds it

async def reporter(llm_response, input_data, context):
    """Enhance the LLM summary with computed quality grade"""

    record_count = input_data.get("record_count", 0)
    aggregations = input_data.get("aggregations", {})
    errors_from_validation = input_data.get("errors", [])

    # Compute quality grade based on data characteristics
    error_ratio = len(errors_from_validation) / max(record_count + len(errors_from_validation), 1)

    if error_ratio == 0 and record_count >= 5:
        grade = "A"
    elif error_ratio < 0.1 and record_count >= 3:
        grade = "B"
    elif error_ratio < 0.3:
        grade = "C"
    elif error_ratio < 0.5:
        grade = "D"
    else:
        grade = "F"

    # Use LLM summary if available, otherwise generate one
    summary = llm_response.get("summary", "")
    if not summary:
        summary = (
            f"Processed {record_count} records. "
            f"Mean: {aggregations.get('mean', 'N/A')}, "
            f"StdDev: {aggregations.get('std_dev', 'N/A')}. "
            f"Quality grade: {grade}."
        )

    return {
        "summary": summary,
        "quality_grade": grade
    }


# --- Main Entry Point ---

async def main():
    print("=== Data Processing Pipeline ===\n")

    await leafmesh.start()
    print("Pipeline started: validator -> transformer -> reporter\n")

    # Test 1: Valid data
    print("--- Test 1: Valid data ---")
    result = await leafmesh.mesh_call(
        "validator",
        input_data={
            "records": [
                {"name": "sensor_a", "value": 42},
                {"name": "sensor_b", "value": 87},
                {"name": "sensor_c", "value": 15},
                {"name": "sensor_d", "value": 63},
                {"name": "sensor_e", "value": 91}
            ]
        },
        session_id="pipeline_test"
    )
    print(f"Result: {result}\n")

    # Test 2: Mixed valid and invalid
    print("--- Test 2: Mixed data ---")
    result2 = await leafmesh.mesh_call(
        "validator",
        input_data={
            "records": [
                {"name": "good_1", "value": 50},
                {"value": 100},                      # Missing name
                {"name": "bad_value", "value": "abc"}, # Non-numeric value
                {"name": "good_2", "value": 75}
            ]
        },
        session_id="pipeline_test_2"
    )
    print(f"Result: {result2}\n")

    # Test 3: Empty data
    print("--- Test 3: Empty data ---")
    result3 = await leafmesh.mesh_call(
        "validator",
        input_data={"records": []},
        session_id="pipeline_test_3"
    )
    print(f"Result: {result3}\n")

    await leafmesh.stop()
    print("=== Pipeline complete ===")


if __name__ == "__main__":
    asyncio.run(main())
```

## How the Pipeline Executes

When you send 5 sensor records to the validator:

### Stage 1: Validator (Programmatic)
1. No LLM call — `validator()` runs directly
2. Checks each record for required fields (`name`, `value`) and valid ranges
3. Returns `is_valid: true` with 5 cleaned records and 0 errors
4. `can_call` condition `is_valid == true` triggers the transformer

### Stage 2: Transformer (Programmatic)
1. No LLM call — `transformer()` runs directly
2. Normalizes values to 0-100 scale
3. Computes aggregations (mean, std_dev, min, max)
4. Returns `record_count: 5` with transformed records
5. `can_call` condition `record_count > 0` triggers the reporter

### Stage 3: Reporter (LLM)
1. The LLM receives the reporter's prompt and yields schema and generates a summary of the processing results
2. `reporter()` intelligence function computes the quality grade
3. Returns the summary and grade
4. No `can_call` rules — pipeline terminates

Total LLM calls: **1** (only the reporter). The validator and transformer are pure Python.

## Expected Output

```
=== Data Processing Pipeline ===

Pipeline started: validator -> transformer -> reporter

--- Test 1: Valid data ---
Result: {'summary': 'Processed 5 sensor readings...', 'quality_grade': 'A'}

--- Test 2: Mixed data ---
Result: {'summary': 'Processed 2 valid records out of 4...', 'quality_grade': 'C'}

--- Test 3: Empty data ---
Result: {'is_valid': False, 'errors': [], 'cleaned_records': [], 'raw_count': 0}
```

Test 3 stops at the validator — `is_valid == false` means the transformer is never called.

## Adding Pre-Compose for Data Enrichment

Use the pre-compose pipeline to enrich data before the LLM sees it:

```python
from leafmesh import pre_compose

async def load_historical_baseline(input_data, context):
    """Pull baseline statistics from an external source before the LLM analyzes"""
    source = input_data.get("source", "default")
    # Load baseline from your external database or API
    baseline = await database.get_baseline(source)
    if baseline:
        return {**input_data, "baseline": baseline}
    return input_data

@pre_compose(input_processor=load_historical_baseline)
async def reporter(llm_response, input_data, context):
    # input_data now includes the loaded baseline
    baseline = input_data.get("baseline", {})
    # ... compare current aggregations against historical baseline
    return {"summary": llm_response.get("summary", ""), "quality_grade": "A"}
```

## Key Patterns

| Pattern | Where |
|---------|-------|
| Programmatic agents | Validator and transformer — zero LLM cost for deterministic work |
| Conditional routing | `is_valid == true` gates the transformer; `record_count > 0` gates the reporter |
| Mixed agent types | Programmatic agents for data processing, LLM agent for summarization |
| Intelligence functions | Function name matches YAML agent name — auto_discover wires them |
| Pre-compose | Optional data enrichment before the LLM call |

## Next Steps

- **[Math Pipeline](yield-monitoring)** — Simpler 3-agent example with verification
- **[Customer Service Bot](customer-service-bot)** — Multi-tier support with human escalation
- **[Monitoring Patterns](../advanced/yield-monitoring)** — Scheduled data collection with alerts
- **[Architecture Guide](../core-concepts/architecture)** — How LeafMesh orchestrates agents

---

*LeafMesh — Mix programmatic and LLM agents in one pipeline*
