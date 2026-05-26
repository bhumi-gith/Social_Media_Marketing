# Testing Framework

Strategies and patterns for testing LeafMesh agent systems.

## Unit Testing Intelligence Functions

Intelligence functions are regular async Python functions — test them directly:

```python
import asyncio
import pytest

# Test the intelligence function in isolation
async def test_specialist_handler():
    llm_response = {
        "analysis": "The issue is a network timeout",
        "confidence": 0.85
    }
    input_data = {"category": "technical", "urgency": 8}
    context = {"session_id": "test_session", "agent_name": "specialist"}

    result = await specialist_handler(llm_response, input_data, context)

    assert "analysis" in result
    assert result["confidence"] == 0.85

asyncio.run(test_specialist_handler())
```

## Unit Testing Pre-Compose Processors

```python
async def test_context_processor():
    input_data = {"user_message": "Test query", "account_id": "acc_123"}
    context = {"session_id": "test_session"}

    result = await my_context_processor(input_data, context)

    assert "account_tier" in result
    assert result["account_tier"] in ["free", "pro", "enterprise"]
```

## Unit Testing Custom Tools

```python
async def test_calculator_tool():
    result = await calculator(expression="2 + 3")
    assert result == {"result": 5}

async def test_lookup_tool():
    result = await lookup_account(account_id="acc_123")
    assert "tier" in result
    assert "status" in result
```

## Integration Testing Agent Chains

Test complete agent execution with real LLM calls:

```python
async def test_triage_to_specialist_chain():
    leafmesh = LeafMesh.from_yaml("test_config.yaml")
    await leafmesh.start()

    result = await leafmesh.mesh_call(
        "triage_agent",
        input_data={"user_message": "Production database is down"},
        session_id="integration_test_001"
    )

    # Verify triage classified correctly
    assert result.get("urgency", 0) >= 7

    # Verify the specialist was reached by checking the mesh result yield —
    # ``mesh_call`` returns the full chain output, so downstream agent
    # contributions are visible directly without an external REST query.
    assert "specialist_response" in result

    await leafmesh.stop()
```

## Testing Yields Schema Compliance

Verify that agent outputs match their declared yields:

```python
async def test_yields_compliance():
    leafmesh = LeafMesh.from_yaml("config.yaml")
    await leafmesh.start()

    result = await leafmesh.mesh_call(
        "classifier",
        input_data={"user_message": "Test input"},
        session_id="schema_test"
    )

    # Verify all declared yields are present
    assert isinstance(result.get("category"), str)
    assert isinstance(result.get("confidence"), (int, float))
    assert isinstance(result.get("summary"), str)

    await leafmesh.stop()
```

## Testing Condition Evaluation

Test can_call conditions without LLM calls:

```python
def test_condition_evaluation():
    """Test can_call conditions by running agents and checking routing."""
    # Define test input that should trigger the condition
    test_data = {"message": "My server is down and I need urgent help"}

    # Run through the mesh — if condition "urgency >= 7" is met,
    # the specialist agent should be called automatically
    result = await leafmesh.mesh_call("support_request", test_data, session_id="condition_test")

    # Verify the specialist was reached by checking its yields
    assert result.get("specialist_response") is not None
    assert evaluator.evaluate("urgency >= 7 and category == 'billing'", yields) == False
```

## Test Configuration

Use a separate test configuration with lower costs:

```yaml
# test_config.yaml
name: "test_system"
architecture: "managed_mesh"

agents:
  triage_agent:
    model: "gpt-4o-mini"      # Use cheaper model for tests
    max_tokens: 200             # Limit token usage
    # ... same structure as production

redis:
  host: "localhost"
  port: 6379
  db: 1                        # Use separate Redis DB for tests
```

## Test Cleanup

```python
async def cleanup_test_session(leafmesh, session_id):
    """Erase all session state after a test."""
    await leafmesh.erase_session(session_id)
```

`erase_session` removes the session record, conversation history, agent outputs, and any pending callbacks tied to the session. For full-test-suite cleanup, use a dedicated Redis DB (e.g. `db: 1` in your test config) and flush it between runs.

## Next Steps

- **[Debugging Tools](debugging)** — Debugging techniques
- **[Best Practices](best-practices)** — Development guidelines
- **[Agent Development](../agents/development)** — Agent building guide

---

*LeafMesh — Testing multi-agent systems*
