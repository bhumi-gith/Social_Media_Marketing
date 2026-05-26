# Advanced Middleware Usage

Advanced patterns for pre-compose middleware including composition, conditional processing, and multi-agent coordination.

## Conditional Processing

Apply different context based on input characteristics:

```python
async def conditional_context(input_data, context):
    """Load different context based on request type"""
    request_type = input_data.get("type", "general")
    session_id = context.get("session_id", "default")

    if request_type == "technical":
        # Load technical documentation from your external data source
        docs = await database.get_technical_docs()
        return {"docs": docs or [], "mode": "technical"}

    elif request_type == "billing":
        # Load account billing context from your external data source
        billing = await database.get_billing_context(session_id)
        return {"billing": billing or {}, "mode": "billing"}

    return {"mode": "general"}
```

## Chained Context Building

Build context incrementally across agents using Redis:

```python
# First agent's processor loads initial context
async def initial_context(input_data, context):
    return {"phase": "triage", "original_query": input_data.get("user_message")}

# Second agent's processor uses upstream yields passed automatically via input_data
async def enriched_context(input_data, context):
    # Upstream yields are automatically passed as input_data through the can_call chain
    return {
        "phase": "specialist",
        "triage_category": input_data.get("category"),
        "urgency": input_data.get("urgency")
    }
```

## Processor with External API Calls

Pre-compose is the right place for external data fetches because they run before the LLM call:

```python
import aiohttp

async def fetch_external_data(input_data, context):
    """Fetch real-time data before LLM processing"""
    query = input_data.get("query", "")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.example.com/data",
            params={"q": query},
            timeout=aiohttp.ClientTimeout(total=5)
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {"external_results": data["results"][:5]}

    return {"external_results": [], "fetch_failed": True}
```

## Pre-Compose with Scheduled Agents

When a scheduled agent wakes up, its pre-compose processors run with scheduling context:

```python
async def scheduled_context(input_data, context):
    """Build context for scheduled executions"""
    # context includes scheduling metadata for wake_up agents
    last_run = await database.get_last_health_check()

    return {
        "last_check": last_run,
        "check_type": "scheduled",
        "interval": "hourly"
    }

@pre_compose(context_processor=scheduled_context)
async def health_monitor(llm_response, input_data, context):
    # Store this run's timestamp in your external data source
    from datetime import datetime
    await database.set_last_health_check(datetime.now().isoformat())
    return llm_response
```

## Testing Processors

Processors are regular async functions and can be tested independently:

```python
import asyncio

async def test_context_processor():
    input_data = {"user_message": "Test query", "account_id": "acc_123"}
    context = {"session_id": "test_session", "agent_name": "test_agent"}

    result = await assemble_context(input_data, context)

    assert "account" in result
    assert "recent_orders" in result

asyncio.run(test_context_processor())
```

## Next Steps

- **[Guardrails](guardrails)** — Input/output validation
- **[Custom Middleware](custom)** — Writing processors
- **[Context Engineering](../runtime/context-engineering)** — Context management

---

*LeafMesh — Advanced middleware patterns*
