# Agent Development

Practical guide for building, testing, and organizing agents in LeafMesh.

## Development Workflow

1. **Define agents in YAML** — prompts, yields, can_call rules
2. **Write intelligence functions** — deterministic Python logic
3. **Test locally** — run against a local Redis instance
4. **Iterate** — adjust prompts, conditions, and logic

## File Organization

For systems with more than 3 agents, organize into separate files:

```
my_system/
├── config.yaml              # Agent definitions
├── main.py                  # Entry point
├── agency/
│   ├── __init__.py
│   ├── agency_client.py     # LeafMesh init + agent registration
│   ├── solver_agent.py      # Solver intelligence
│   ├── checker_agent.py     # Checker intelligence
│   └── tools/
│       └── database.py      # Custom tool definitions
```

### Agent Files

```python
# agency/solver_agent.py
# Function name "solver" matches the YAML agent name — auto_discover finds it
async def solver(llm_response, input_data, context):
    return llm_response
```

```python
# agency/agency_client.py
from leafmesh import LeafMesh

async def initialize(config_path: str):
    leafmesh = LeafMesh.from_yaml(config_path)
    await leafmesh.start()
    # auto_discover in YAML config handles agent registration
    # Set auto_discover: true and agents_dir in your config.yaml
    return leafmesh
```

## Writing Intelligence Functions

### Function Signature

```python
# Function name matches the YAML agent name — auto_discover finds it
async def agent_name(llm_response: dict, input_data: dict, context: dict) -> dict:
    """
    llm_response: Parsed LLM output (empty dict for programmatic agents)
    input_data:   Data from caller or upstream agent's yields
    context:      {"session_id": "...", "agent_name": "..."}

    Returns: dict matching the agent's yields schema
    """
    return llm_response
```

### Pattern: Deterministic Override

Replace the LLM response for cases where you can compute the answer:

```python
# Function name "solver" matches the YAML agent name — auto_discover finds it
async def solver(llm_response, input_data, context):
    import re
    problem = input_data.get("problem", "")
    numbers = re.findall(r'-?\d+\.?\d*', problem)

    if len(numbers) == 2 and "+" in problem:
        a, b = float(numbers[0]), float(numbers[1])
        return {"answer": a + b, "confidence": 1.0}

    return llm_response  # Fall back to LLM
```

### Pattern: Enrichment

Add computed fields to the LLM response:

```python
# Function name "reporter" matches the YAML agent name — auto_discover finds it
async def reporter(llm_response, input_data, context):
    record_count = input_data.get("record_count", 0)
    error_count = len(input_data.get("errors", []))
    grade = "A" if error_count == 0 else "B" if error_count < 3 else "C"

    return {
        "summary": llm_response.get("summary", ""),
        "quality_grade": grade
    }
```

### Pattern: Stateful Tracking

Track state across calls using yields and session context:

```python
# Function name "stateful_agent" matches the YAML agent name — auto_discover finds it
async def stateful_agent(llm_response, input_data, context):
    # Use input_data from upstream agents and context for session awareness
    previous_count = input_data.get("call_count", 0)

    return {**llm_response, "call_count": previous_count + 1}
```

State persistence (sessions, yields, agent data) is handled automatically by the mesh and stored in Redis. You can query state via the REST API at `:18820`.

## Testing

### Unit Testing Intelligence Functions

Intelligence functions are regular async Python functions. Test them directly:

```python
import pytest

@pytest.mark.asyncio
async def test_solver_addition():
    result = await solver_logic(
        llm_response={"answer": 5},
        input_data={"problem": "2 + 3"},
        context={"session_id": "test"}
    )
    assert result["answer"] == 5.0
    assert result["confidence"] == 1.0


@pytest.mark.asyncio
async def test_solver_fallback():
    """Complex problems fall back to LLM response"""
    llm_response = {"answer": 42, "confidence": 0.8}
    result = await solver_logic(
        llm_response=llm_response,
        input_data={"problem": "What is the meaning of life?"},
        context={"session_id": "test"}
    )
    assert result == llm_response
```

### Integration Testing

```python
@pytest.mark.asyncio
async def test_full_pipeline():
    leafmesh = LeafMesh.from_yaml("test_config.yaml")
    await leafmesh.start()

    try:
        result = await leafmesh.mesh_call(
            "solver",
            input_data={"problem": "2 + 1"},
            session_id="integration_test"
        )
        assert "answer" in result
    finally:
        await leafmesh.stop()
```

## Debugging

### Inspect Session State

Query the REST API to inspect session state. LeafMesh runs a FastAPI server on port `18820`:

```bash
# Session data
curl http://localhost:18820/session/{session_id}

# Agent yields
curl http://localhost:18820/yields/{session_id}/{agent_name}

# Mesh communications
curl http://localhost:18820/mesh/{session_id}
```

You can also use `leafmesh.get_usage_analytics()` and `leafmesh.get_llm_cache_stats()` for aggregated runtime statistics.

### Common Issues

| Problem | Cause | Fix |
|---------|-------|-----|
| Agent not found | Function name doesn't match YAML agent name | Ensure function name matches agent name exactly |
| Empty response | Intelligence function not found by auto_discover | Ensure function is in the agents_dir and name matches YAML |
| can_call not triggering | Condition doesn't match yields | Check yield field names and types |
| Timeout errors | LLM provider slow or unreachable | Check API keys, network connectivity |

## Next Steps

- **[Agent Types](overview)** — All four agent types in detail
- **[Testing](../development/testing)** — Testing framework guide
- **[Debugging](../development/debugging)** — Debugging tools and techniques

---

*LeafMesh — Build, test, iterate*
