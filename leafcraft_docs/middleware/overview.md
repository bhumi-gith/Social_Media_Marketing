# Middleware Overview

Middleware in LeafMesh refers to the processing layers that sit between incoming requests and agent execution. The primary middleware system is the **pre-compose pipeline**, which provides deterministic data transformation before the LLM sees any input.

## Pre-Compose Pipeline

The `@pre_compose()` decorator attaches three optional processors to an intelligence function:

```python
from leafmesh import LeafMesh, pre_compose

leafmesh = LeafMesh.from_yaml("config.yaml")

async def build_context(input_data, context):
    """Assemble business context from external systems"""
    account = await fetch_account(context.get("account_id"))
    return {"tier": account.tier, "history": account.tickets}

async def clean_input(input_data, context):
    """Extract and sanitize the user message"""
    return input_data.get("user_message", "").strip()

async def add_metadata(input_data, context):
    """Attach supplementary data"""
    return {"timestamp": datetime.now().isoformat()}

@pre_compose(
    context_processor=build_context,
    input_processor=clean_input,
    others_processor=add_metadata
)
async def my_agent(llm_response, input_data, context):
    return llm_response
```

## Processing Flow

```
Incoming Request
    │
    ├── context_processor → enriches business context
    ├── input_processor   → cleans the user input
    └── others_processor  → attaches supplementary data
    │
    ▼
Platform assembles the message array for the LLM
    │
    ▼
LLM Call → Yields Parsing → Intelligence Function
```

Each processor enriches the context that the platform delivers to your agent. You don't manage the wiring yourself — the platform feeds the processed values into the right place when constructing the LLM call.

## Three Processor Types

| Processor | Role | Used For |
|-----------|------|----------|
| `context_processor` | Business context, external data | System-level context that frames the agent's reasoning |
| `input_processor` | User input extraction/cleaning | The current request the LLM will respond to |
| `others_processor` | Attachments, metadata | Supplementary signals (timestamps, flags, etc.) |

Each processor is an `async` function receiving `(input_data, context)` and returning transformed data. Processors run before the LLM call, so they are fully deterministic.

## Why Middleware Matters

Pre-compose processors solve a fundamental problem: LLMs work best with well-structured context, but raw input is often messy. By separating context assembly from LLM execution:

- Business logic stays in Python, not in prompts
- External data fetches happen before the LLM call (no tool-calling round trips)
- Input validation is deterministic, not LLM-dependent
- Context is reproducible for testing and debugging

## Next Steps

- **[Built-in Middleware](builtin)** — Standard processors
- **[Custom Middleware](custom)** — Writing your own processors
- **[Advanced Usage](advanced)** — Composition patterns
- **[Guardrails](guardrails)** — Input/output validation

---

*LeafMesh — Deterministic pre-processing for LLM agents*
