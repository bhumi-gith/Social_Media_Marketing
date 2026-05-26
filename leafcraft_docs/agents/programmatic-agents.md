# Programmatic Agents

Programmatic agents are pure Python agents that skip the LLM call entirely. They participate in the mesh identically to LLM agents — same yields, can_call rules, and condition evaluation — but their logic is deterministic and free.

## Configuration

```yaml
agents:
  validator:
    name: "validator"
    agent_type: "programmatic"
    yields:
      is_valid: "boolean"
      errors: "array"
      cleaned_records: "array"
    can_call:
      - agent: "processor"
        condition: "is_valid == true"
```

Set `agent_type: "programmatic"` in YAML. No `model` or `prompt` fields are needed.

## Intelligence Function

For programmatic agents, the intelligence function **is** the agent. No LLM call is made. The `llm_response` parameter is an empty dict.

```python
# Function name "validator" matches the YAML agent name — auto_discover finds it
async def validator(llm_response, input_data, context):
    """Pure Python validation — no LLM call"""

    records = input_data.get("records", [])
    errors = []
    cleaned = []

    for i, record in enumerate(records):
        if "name" not in record:
            errors.append(f"Record {i}: missing 'name'")
        elif "value" not in record:
            errors.append(f"Record {i}: missing 'value'")
        elif not isinstance(record["value"], (int, float)):
            errors.append(f"Record {i}: 'value' must be a number")
        else:
            cleaned.append(record)

    return {
        "is_valid": len(cleaned) > 0,
        "errors": errors,
        "cleaned_records": cleaned
    }
```

## Execution Pipeline

```
Input Data
    │
    ▼
Pre-compose pipeline (if registered)
    │
    ▼
Intelligence function runs directly
    │  (llm_response is {}, no LLM call)
    ▼
Auto-store yields in Redis
    │
    ▼
can_call evaluation
    │
    ▼
Downstream agents (via mesh)
```

The same pipeline as LLM agents, minus the LLM call. Pre-compose, yields storage, and can_call evaluation all work identically.

## Receiving Conversation History (Opt-In)

Programmatic agents are stateless by default — they get whatever the
caller passes as `input_data` and nothing else. When you want the
agent to see prior conversation turns (e.g. for context-aware
summarisation, domain-specific retrieval, or follow-up routing
decisions), opt in via the YAML:

```yaml
agents:
  followup_router:
    name: "followup_router"
    agent_type: "programmatic"
    receive_conversation_history: true
    history_limit: 30   # default 20, range 1-200
    inputs:
      latest_message: "string"
    yields:
      route_to: "string"
```

When `receive_conversation_history: true`, the SDK injects the last
`history_limit` turns into `context["_conversation_history"]` — the
intelligence function reads it the same way it reads `chain_history`.
The default is **off** to keep payloads small for stateless functions
that don't need it.

The Studio "Inputs & Outputs" panel and Playground agent inspector
both expose a single toggle for this; flip it on and the YAML field
appears automatically.

## When to Use Programmatic Agents

| Use Case | Why Not LLM |
|----------|-------------|
| Data validation | Rules are deterministic — no reasoning needed |
| Calculations | Math is exact — LLMs approximate |
| API calls | HTTP requests don't need language understanding |
| Data transformation | Formatting, normalization, aggregation |
| System integration | File operations, database queries |
| Cost-sensitive operations | LLM calls cost money per token |

## Example: Data Pipeline

A pipeline where programmatic agents handle deterministic work and an LLM agent only handles the summary:

```yaml
agents:
  validator:
    name: "validator"
    agent_type: "programmatic"
    yields:
      is_valid: "boolean"
      cleaned: "array"
    can_call:
      - agent: "transformer"
        condition: "is_valid == true"

  transformer:
    name: "transformer"
    agent_type: "programmatic"
    yields:
      transformed: "array"
      stats: "object"
    can_call:
      - agent: "reporter"
        condition: "transformed != []"

  reporter:
    name: "reporter"
    model: "gpt-4o-mini"          # Only this agent uses an LLM
    temperature: 0.3
    prompt: |
      Summarize the data processing results.
    yields:
      summary: "string"
```

```python
# Function name "transformer" matches the YAML agent name — auto_discover finds it
async def transformer(llm_response, input_data, context):
    """Normalize and aggregate — pure Python"""
    records = input_data.get("cleaned", [])
    values = [r["value"] for r in records]

    mean = sum(values) / len(values) if values else 0
    transformed = [{"name": r["name"], "normalized": r["value"] / max(values)} for r in records]

    return {
        "transformed": transformed,
        "stats": {"mean": round(mean, 2), "count": len(values)}
    }
```

Total LLM calls: **1** (only the reporter). Validator and transformer are free.

## Stateful Programmatic Agents

Track state across calls using yields. The mesh automatically persists yields in Redis and passes them as `input_data` to downstream agents:

```python
# Function name "stateful_collector" matches the YAML agent name — auto_discover finds it
async def stateful_collector(llm_response, input_data, context):
    """Programmatic agent that tracks collection state via yields"""
    previous_count = input_data.get("collection_number", 0)

    return {
        "data": input_data.get("readings", []),
        "collection_number": previous_count + 1,
        "source": "sensor_1"
    }
```

Session state, yields, and mesh communications are managed automatically. Query state via the REST API at `:18820`.

## Using Tools in Programmatic Agents

Programmatic agents can have tools listed in YAML, but since there's no LLM to decide when to use them, you call tools directly from the intelligence function:

```python
# Function name "collector" matches the YAML agent name — auto_discover finds it
async def collector(llm_response, input_data, context):
    """Use tools directly in a programmatic agent"""
    from datetime import datetime

    # Direct implementation — no LLM needed
    return {
        "data": {"readings": [1, 2, 3]},
        "source": "database",
        "timestamp": datetime.now().isoformat()
    }
```

## Next Steps

- **[Agent Types](overview)** — All four agent types
- **[Data Pipeline Example](../examples/data-pipeline)** — Full programmatic pipeline
- **[Agent Configuration](../api-reference/agent-config)** — YAML reference

---

*LeafMesh — Deterministic agents, zero LLM cost*
