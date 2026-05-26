# Memory Retrieval

Retrieving stored data in LeafMesh is handled automatically through the agent pipeline. Upstream agent yields are passed as `input_data` to downstream agents, and conversation history is loaded into the LLM context automatically.

## Automatic Retrieval

When an agent executes, LeafMesh automatically:
- Injects recent conversation history into the LLM prompt
- Passes upstream agent yields as `input_data` to downstream agents via `can_call`
- Provides session metadata through the `context` parameter

## Accessing Yields in Intelligence Functions

When agent B is called by agent A via `can_call`, agent A's yields arrive as `input_data`:

```python
async def checker(llm_response, input_data, context):
    session_id = context.get("session_id", "default")

    # Upstream agent yields are available directly in input_data
    solver_answer = input_data.get("answer")
    solver_steps = input_data.get("steps", [])

    return {
        "is_correct": solver_answer == 42,
        "steps_count": len(solver_steps)
    }
```

## Accessing Data via Pre-Compose

Load additional data before the LLM sees the request:

```python
from leafmesh import pre_compose

async def load_context(input_data, context):
    """Enrich input data before LLM processing"""
    source = input_data.get("source", "default")
    # Add any extra context needed for the LLM
    return {**input_data, "analysis_mode": "detailed"}

@pre_compose(input_processor=load_context)
async def analyzer(llm_response, input_data, context):
    return llm_response
```

## Inspecting Sessions

Browse sessions and conversation history in **Studio's Sessions tab**, or query them via the platform's REST API.

## Next Steps

- **[Redis Integration](redis-integration)** — Redis configuration
- **[State Management](state-management)** — State patterns
- **[Short-Term Memory](short-term)** — Session management

---

*LeafMesh — Automatic data retrieval*
