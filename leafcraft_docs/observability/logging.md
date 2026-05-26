# Logging

All internal LeafMesh logs are automatically sent to the LeafCraft dashboard. To make **your own logs** — inside agent files, `main.py`, or any custom module — also appear in your dashboard, use `LeafMeshLogger`.

## Quick Start

```python
from leafmesh import LeafMeshLogger

logger = LeafMeshLogger(__name__)

logger.info("This appears in your LeafCraft dashboard")
```

That's it. Any log emitted through `LeafMeshLogger` is automatically:

- Sent to the LeafCraft dashboard alongside traces and metrics
- Tagged with `trace_id` and `span_id` for correlation with active spans
- Formatted consistently with all other LeafMesh logs

## Why Not `logging.getLogger()`?

Python's standard `logging.getLogger()` creates loggers that **will not** appear in your LeafCraft dashboard.

```python
# DON'T — invisible to the dashboard
import logging
logger = logging.getLogger(__name__)
logger.info("This stays local only")

# DO — sent to the dashboard
from leafmesh import LeafMeshLogger
logger = LeafMeshLogger(__name__)
logger.info("This appears in your LeafCraft dashboard")
```

| Feature | `logging.getLogger()` | `LeafMeshLogger` |
|---------|----------------------|-------------------|
| Console output | Yes | Yes |
| File output | No (unless configured) | Yes (automatic) |
| LeafCraft dashboard | No | Yes |
| Trace correlation | No | Yes (`trace_id`, `span_id`) |
| Consistent formatting | No | Yes |

## Usage in Agent Files

Use `LeafMeshLogger` at the top of your agent files. The logger name should match the module name.

```python
# agency/researcher_agent.py
from leafmesh import LeafMeshLogger

logger = LeafMeshLogger(__name__)

async def researcher_agent(llm_response, input_data, context):
    query = input_data.get("query", "")
    logger.info(f"Starting research for: {query}")

    # Your agent logic...
    results = await do_research(query)

    if not results:
        logger.warning(f"No results found for: {query}")
        return {"results": [], "status": "empty"}

    logger.info(f"Research complete — {len(results)} results found")
    return {"results": results}
```

## Usage in main.py

```python
# main.py
import asyncio
from leafmesh import LeafMesh, LeafMeshLogger

logger = LeafMeshLogger("main")

async def main():
    leafmesh = LeafMesh.from_yaml("configs/config.yaml")
    await leafmesh.start()
    logger.info("Application started successfully")

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await leafmesh.stop()

asyncio.run(main())
```

## Usage in Utility Modules

For shared utilities, helper functions, or service modules:

```python
# utils/data_processor.py
from leafmesh import LeafMeshLogger

logger = LeafMeshLogger(__name__)

def process_order(order_data: dict) -> dict:
    logger.info(f"Processing order {order_data.get('id')}")

    if not order_data.get("items"):
        logger.warning(f"Empty order received: {order_data.get('id')}")
        return {"status": "rejected", "reason": "no items"}

    # Process...
    logger.info(f"Order {order_data.get('id')} processed successfully")
    return {"status": "completed"}
```

## Structured Metadata

Pass a dictionary as the second argument to attach structured key-value pairs to the log message:

```python
logger.info("Order processed", {"order_id": "ORD-123", "total": 49.99, "items": 3})
# Output: Order processed | order_id=ORD-123 | total=49.99 | items=3

logger.error("Payment failed", {"order_id": "ORD-456", "provider": "stripe", "error_code": "card_declined"})
# Output: Payment failed | order_id=ORD-456 | provider=stripe | error_code=card_declined
```

The metadata is included in the log message and visible in your LeafCraft dashboard, making it searchable and filterable.

## Log Levels

| Method | Level | When to Use |
|--------|-------|-------------|
| `logger.debug(msg)` | DEBUG | Verbose diagnostic info (not sent to dashboard by default) |
| `logger.info(msg)` | INFO | Normal operations — agent started, request processed |
| `logger.warning(msg)` | WARNING | Something unexpected but recoverable — missing data, fallback used |
| `logger.error(msg)` | ERROR | Something failed — highlighted as error in your dashboard |

## Trace Correlation

When logs are emitted during an active span (inside a `mesh_call`, agent execution, or LLM call), `LeafMeshLogger` automatically attaches trace context:

```
13:17:06 [INFO] agency.researcher_agent: Starting research | trace_id=abc123 | span_id=def456
```

In the LeafCraft dashboard, this means you can:

1. Find a slow trace in the tracing view
2. Click into it to see all spans
3. See your application logs alongside LeafMesh logs, correlated to the exact span

## Log Output

Every `LeafMeshLogger` instance writes to three destinations:

| Destination | Format | Purpose |
|-------------|--------|---------|
| Console | Rich formatting (colors, icons) | Developer experience during local dev |
| File | `logs/leafmesh_YYYY-MM-DD.log` | Local debugging and persistence |
| LeafCraft dashboard | Automatic | Search, filter, alerting, trace correlation |

### Log File Location

By default, log files are written to `./logs/` in the current working directory. Override with:

```bash
export LEAFMESH_LOG_DIR="/var/log/myapp"
```

## Best Practices

**Do** use one logger per module at the top of the file:

```python
from leafmesh import LeafMeshLogger
logger = LeafMeshLogger(__name__)
```

**Do** use f-strings for log messages:

```python
logger.info(f"Agent {agent_name} processed {count} items in {duration:.2f}s")
```

**Don't** use printf-style formatting — it will cause errors:

```python
# WRONG — will crash
logger.info("Agent %s processed %d items", agent_name, count)

# RIGHT — use f-strings
logger.info(f"Agent {agent_name} processed {count} items")
```

**Don't** log sensitive data (API keys, passwords, PII):

```python
# WRONG
logger.info(f"Authenticating with key: {api_key}")

# RIGHT
logger.info("Authenticating with external service")
```

---

*LeafMesh — Every log in your dashboard*
