# Custom Middleware

Build custom pre-compose processors for domain-specific data transformation needs.

## Processor Interface

Every processor is an async function with the same signature:

```python
async def my_processor(input_data: dict, context: dict) -> dict | str:
    """
    Args:
        input_data: The original request data passed to leafmesh.mesh_call()
        context: Execution context with session_id, agent info, etc.

    Returns:
        Transformed data (dict or string)
    """
    return transformed_data
```

The `context` dict contains:

| Key | Description |
|-----|-------------|
| `session_id` | Current session identifier |
| `agent_name` | Name of the agent being executed |
| `entry_point` | Entry point name if triggered via API |

## Example: Rate Limiting Context

```python
async def rate_limit_context(input_data, context):
    """Add rate limiting info to system context"""
    session_id = context.get("session_id", "default")

    # Track request count using your external store (e.g., database, cache)
    count = await rate_limiter.increment(session_id)  # Your rate limiting service

    return {
        "request_number": count,
        "rate_limit": 100,
        "remaining": max(0, 100 - count)
    }
```

## Example: Multi-Source Data Assembly

```python
async def assemble_context(input_data, context):
    """Pull from multiple data sources"""
    import asyncio

    account_id = input_data.get("account_id")

    # Fetch from multiple sources in parallel
    account_task = database.get_account(account_id)
    orders_task = database.get_recent_orders(account_id, limit=5)

    account, orders = await asyncio.gather(account_task, orders_task)

    return {
        "account": {"tier": account.tier, "since": account.created_at},
        "recent_orders": [{"id": o.id, "status": o.status} for o in orders]
    }
```

## Example: Input Validation Processor

```python
async def validate_input(input_data, context):
    """Validate and extract required fields"""
    message = input_data.get("user_message", "")

    if not message or not message.strip():
        return "No message provided. Please describe your request."

    # Enforce length limits
    if len(message) > 10000:
        message = message[:10000] + "... [truncated]"

    return message.strip()
```

## Attaching to Agents

```python
@pre_compose(
    context_processor=assemble_context,
    input_processor=validate_input,
    others_processor=rate_limit_context
)
async def my_agent(llm_response, input_data, context):
    return llm_response
```

## Error Handling

If a processor raises an exception, the agent execution fails with a descriptive error. Processors should handle their own errors gracefully:

```python
async def safe_context(input_data, context):
    """Processor with error handling"""
    try:
        data = await external_api.fetch()
        return {"external_data": data}
    except Exception:
        # Return empty context rather than failing the agent
        return {"external_data": None, "data_unavailable": True}
```

## Next Steps

- **[Advanced Usage](advanced)** — Composition patterns
- **[Guardrails](guardrails)** — Input/output validation
- **[Built-in Middleware](builtin)** — Standard processors

---

*LeafMesh — Custom pre-processing logic*
