# Built-in Middleware

LeafMesh provides common pre-compose processor patterns that handle frequent middleware needs.

## Input Sanitization

Strip and normalize user input before LLM processing:

```python
async def sanitize_input(input_data, context):
    """Extract and clean user message"""
    message = input_data.get("user_message", "")
    # Strip whitespace and limit length
    cleaned = message.strip()[:4000]
    return cleaned
```

## History Injection

Conversation history is automatically loaded and injected into the LLM context by the platform. If you need additional historical context beyond the automatic injection, fetch it from your own data store in a pre-compose processor:

```python
async def inject_extra_history(input_data, context):
    """Load additional context from your data store."""
    session_id = context.get("session_id", "default")
    extra = await my_store.get_extra_history(session_id)
    if extra:
        return {"extra_context": extra, **input_data}
    return input_data
```

## External Data Fetch

Pull data from external systems before the LLM call:

```python
async def fetch_account_context(input_data, context):
    """Fetch account data for business context"""
    account_id = input_data.get("account_id")
    if not account_id:
        return {}

    account = await database.get_account(account_id)
    return {
        "account_tier": account.tier,
        "account_status": account.status,
        "recent_tickets": account.recent_tickets[:5]
    }
```

## Upstream Yields Injection

Load yields from a previous agent in the chain:

```python
async def load_upstream_yields(input_data, context):
    """Inject upstream agent's output as context"""
    # Upstream yields are automatically passed as input_data through the can_call chain.
    # If you need yields from a non-direct-upstream agent, access them from input_data
    # which accumulates yields from the chain, or use an external data source.
    triage_result = input_data.get("category") or input_data.get("triage_result")
    if triage_result:
        return {**input_data, "triage_result": triage_result}
    return input_data
```

## Combining Processors

Use all three processor slots together:

```python
@pre_compose(
    context_processor=fetch_account_context,    # business context
    input_processor=sanitize_input,             # current user input
    others_processor=load_upstream_yields       # supplementary signals
)
async def specialist_agent(llm_response, input_data, context):
    return llm_response
```

The platform routes each processor's output into the appropriate part of the LLM call automatically.

## Next Steps

- **[Custom Middleware](custom)** — Writing your own processors
- **[Advanced Usage](advanced)** — Composition patterns
- **[Guardrails](guardrails)** — Input/output validation

---

*LeafMesh — Common middleware patterns*
