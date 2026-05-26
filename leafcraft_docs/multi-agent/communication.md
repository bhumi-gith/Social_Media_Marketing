# Agent Communication

How agents exchange data through the managed mesh in LeafMesh.

## Yields-Based Data Flow

Agents communicate through structured yields. When Agent A calls Agent B, Agent A's yields become Agent B's `input_data`:

```yaml
agents:
  classifier:
    yields:
      category: "string"
      confidence: "number"
    can_call:
      - agent: "handler"
        condition: "confidence > 0.8"

  handler:
    yields:
      result: "string"
```

```python
async def handler(llm_response, input_data, context):
    # input_data = classifier's yields: {category: "...", confidence: 0.9}
    category = input_data.get("category")
    return llm_response
```

## Communication Patterns

### Sequential Chain

```yaml
# A → B → C (each calls the next)
agents:
  step_1:
    can_call:
      - agent: "step_2"
        condition: "status == 'ready'"
  step_2:
    can_call:
      - agent: "step_3"
        condition: "status == 'ready'"
  step_3:
    yields:
      final_result: "string"
```

### Fan-Out (One to Many)

```yaml
agents:
  coordinator:
    can_call:
      - agent: "analyst_a"
        condition: "true"
        call_immediately: true
      - agent: "analyst_b"
        condition: "true"
        call_immediately: true
```

Or via direct mesh calls in an intelligence function:

```python
async def coordinator(llm_response, input_data, context):
    import asyncio
    session_id = context.get("session_id", "default")

    results = await asyncio.gather(
        leafmesh.mesh_call("coordinator", "analyst_a", input_data, session_id=session_id),
        leafmesh.mesh_call("coordinator", "analyst_b", input_data, session_id=session_id)
    )

    return {"analyst_a": results[0], "analyst_b": results[1]}
```

### Conditional Branching

```yaml
agents:
  router:
    yields:
      request_type: "string"
    can_call:
      - agent: "technical_support"
        condition: "request_type == 'technical'"
      - agent: "billing_support"
        condition: "request_type == 'billing'"
      - agent: "general_support"
        condition: "request_type not in ['technical', 'billing']"
```

### Human Gating

```yaml
agents:
  processor:
    can_call:
      - agent: "human_reviewer"
        condition: "risk_level == 'high'"

  human_reviewer:
    agent_type: "human"
    can_call:
      - agent: "executor"
        condition: "approval == 'approved'"
```

## Direct Mesh Calls

Intelligence functions can make direct mesh calls for dynamic routing:

```python
async def dynamic_router(llm_response, input_data, context):
    session_id = context.get("session_id", "default")
    target = llm_response.get("recommended_agent", "default_handler")

    result = await leafmesh.mesh_call(
        "dynamic_router", target, input_data, session_id=session_id
    )
    return result
```

## Session Context in Communication

All agents in the same session share state automatically through the mesh. When Agent A calls Agent B, Agent A's yields become Agent B's `input_data`. This is the primary mechanism for passing data between agents.

For querying session state externally, use the REST API at `:18820`:

```bash
# Query session data
curl http://localhost:18820/session/{session_id}

# Query a specific agent's yields
curl http://localhost:18820/yields/{session_id}/{agent_name}
```

Yields from each agent are auto-persisted and auto-passed to downstream agents. You do not need to manage this manually.

## Next Steps

- **[Coordination Patterns](coordination)** — Automatic oversight and intervention
- **[Mesh Architecture](mesh-architecture)** — Routing infrastructure
- **[Message Routing](../messages/routing)** — Condition evaluation details

---

*LeafMesh — Agent-to-agent data exchange*
