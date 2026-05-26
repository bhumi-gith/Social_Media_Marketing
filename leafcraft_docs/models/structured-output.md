# Structured Output

LeafMesh enforces structured output through the `yields` schema. Every agent declares its output structure in YAML, and LeafMesh parses the LLM response to extract matching fields with correct types.

## Yields Schema

```yaml
agents:
  analyzer:
    name: "analyzer"
    model: "gpt-4o"
    prompt: |
      Analyze the data and report findings.
    yields:
      anomaly_count: "number"
      severity: "string"
      summary: "string"
      flagged_items: "array"
      metadata: "object"
      is_critical: "boolean"
```

## Supported Types

| Type | Description | Example Value |
|------|-------------|---------------|
| `string` | Text data | `"High severity detected"` |
| `number` | Integer or float | `42`, `3.14` |
| `boolean` | True/false | `true`, `false` |
| `array` | List of values | `[1, 2, 3]`, `["a", "b"]` |
| `object` | Nested key-value | `{"key": "value"}` |

## How Parsing Works

1. The LLM receives the yields schema as part of its prompt
2. The LLM generates a response that includes the requested fields
3. LeafMesh parses the response, extracting values and coercing types
4. Parsed yields are persisted and used for `can_call` evaluation

```
LLM Response (raw text/JSON)
    │
    ▼
Yields Parser
    │  Extracts fields matching the schema
    │  Coerces types (string → number, etc.)
    ▼
Structured Dict
    │  {"anomaly_count": 3, "severity": "high", ...}
    ▼
can_call Evaluation
    │  "anomaly_count > 0" → true → trigger downstream
    ▼
Intelligence Function
    │  Receives parsed yields as llm_response
```

## Schema Enforcement

The yields schema prevents **structural hallucination** — wrong format, missing fields, type violations. It does not prevent **semantic hallucination** (correctly formatted but factually wrong outputs).

What yields parsing catches:
- Missing required fields
- Wrong data types (string where number expected)
- Malformed JSON or unparseable output

What it does not catch:
- Factually incorrect values
- Plausible but wrong classifications
- Reasonable-looking but fabricated data

## Combining with Intelligence Functions

Use intelligence functions to add semantic validation on top of structural validation:

```python
async def analyzer(llm_response, input_data, context):
    """Add semantic checks to the structured output"""

    anomaly_count = llm_response.get("anomaly_count", 0)
    readings = input_data.get("readings", [])

    # Sanity check: anomaly count can't exceed total readings
    if anomaly_count > len(readings):
        anomaly_count = len(readings)

    # Recompute severity deterministically
    ratio = anomaly_count / max(len(readings), 1)
    severity = "high" if ratio > 0.2 else "low" if ratio > 0 else "none"

    return {
        "anomaly_count": anomaly_count,
        "severity": severity,
        "summary": llm_response.get("summary", ""),
        "flagged_items": llm_response.get("flagged_items", []),
        "metadata": {"total_readings": len(readings)},
        "is_critical": severity == "high"
    }
```

## Ground Truth Anchoring

The combination of three mechanisms reduces hallucination surface area:

| Mechanism | What It Controls |
|-----------|-----------------|
| **Yields** (structural) | Response must match declared schema |
| **Pre-compose** (deterministic) | Python code controls what the LLM sees |
| **Tools** (external data) | Real data from databases and APIs |

None is sufficient alone. Together they significantly reduce the surface area for hallucination.

## Next Steps

- **[Agent Configuration](../api-reference/agent-config)** — Full yields schema reference
- **[LLM Agents](../agents/llm-agents)** — How yields integrate in the pipeline
- **[Tools](../tools/overview)** — Ground truth through external data

---

*LeafMesh — Structured output, type-safe routing*
