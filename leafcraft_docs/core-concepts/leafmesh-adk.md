# LeafMesh Class

The `LeafMesh` class is the entry point for all LeafMesh operations. It loads YAML configuration, initializes components, and provides methods for processing requests, calling agents, and managing the system lifecycle.

## Quick Start

```python
from leafmesh import LeafMesh

# Load configuration
leafmesh = LeafMesh.from_yaml("config.yaml")

# Optionally add business logic (function name = agent name)
async def solver(llm_response, input_data, context):
    return llm_response

# Start, process, stop
await leafmesh.start()
result = await leafmesh.mesh_call(
    "solver",
    input_data={"problem": "What is 2 + 3?"},
    session_id="demo"
)
await leafmesh.stop()
```

## Construction

Two ways to create a LeafMesh instance:

```python
# From YAML file (recommended)
leafmesh = LeafMesh.from_yaml("config.yaml")

# From Python dictionary
leafmesh = LeafMesh.from_dict({
    "name": "my_swarm",
    "architecture": "managed_mesh",
    "redis": {"host": "localhost", "port": 6379},
    "agents": {
        "solver": {
            "name": "solver",
            "model": "gpt-4o-mini",
            "prompt": "You solve math problems.",
            "yields": {"answer": "number"}
        }
    }
})
```

Both methods validate the configuration before returning.

## Lifecycle

```python
await leafmesh.start()   # Initialize the platform and register agents
# ... process requests ...
await leafmesh.stop()    # Shut down cleanly, completing in-flight requests
```

`start()` brings the platform online — connections, agent registration, scheduling. `stop()` shuts it down cleanly, completing in-flight requests before closing connections.

## Core Methods

### mesh_call()

The primary entry point. Sends data through the full agent pipeline.

```python
result = await leafmesh.mesh_call(
    "triage",                         # Target agent or entry point
    input_data={"message": "..."},    # Data passed to the agent
    session_id="user_123"             # Session for state continuity
)
```

The pipeline: load session → pre-compose → prompt assembly → LLM call → yields parsing → intelligence function → auto-store → can_call evaluation → downstream agents.

### mesh_call() — Agent-to-Agent

Direct agent-to-agent communication from within intelligence functions.

```python
async def coordinator(llm_response, input_data, context):
    result = await leafmesh.mesh_call(
        from_agent="coordinator",
        to_agent="verifier",
        data={"claim": llm_response.get("claim")},
        session_id=context.get("session_id", "default")
    )
    return {"verified": result.get("is_valid", False)}
```

### Intelligence Functions

Register a Python function to enhance or replace an agent's LLM response. The function name must match the agent name in YAML:

```python
async def checker(llm_response, input_data, context):
    # llm_response: parsed LLM output (empty dict for programmatic agents)
    # input_data: data from the caller or upstream agent
    # context: {"session_id": "...", "agent_name": "..."}
    return {"is_correct": True, "explanation": "Verified."}
```

## State & Events

State (sessions, yields, mesh communications) is managed automatically. Browse it through **Studio's Sessions and Activity tabs**, or query it via the REST API (e.g., `GET /api/sessions/{session_id}`, `GET /api/sessions/{session_id}/yields`).

## Scheduling

Schedule agents for periodic execution, or manage schedules at runtime:

```yaml
# In YAML
agents:
  collector:
    wake_up: "*/5 * * * *"    # Every 5 minutes
```

```python
# At runtime
leafmesh.schedule_agent("collector", "every 60 seconds")
leafmesh.unschedule_agent("collector")
```

## Auto-Discovery

Find and register intelligence functions from files:

```python
count = leafmesh.discover("./agency/", "*_agent.py")
# Imports each matching file and registers functions by name
```

## Analytics

```python
# Aggregated usage statistics
analytics = await leafmesh.get_usage_analytics()

# LLM cache performance
cache_stats = await leafmesh.get_llm_cache_stats()

# Swarm status
status = leafmesh.get_status()

# Agent list
agents = leafmesh.list_agents()
```

## Error Handling

```python
from leafmesh import LeafMeshError, ConfigError, AgentError

try:
    leafmesh = LeafMesh.from_yaml("config.yaml")
    await leafmesh.start()
    result = await leafmesh.mesh_call(
        "solver",
        input_data={"message": "Hello"},
        session_id="s1"
    )
except ConfigError as e:
    print(f"Bad configuration: {e}")
except AgentError as e:
    print(f"Agent error: {e}")
except LeafMeshError as e:
    print(f"LeafMesh error: {e}")
finally:
    await leafmesh.stop()
```

## Next Steps

- **[Core API Reference](../api-reference/core-adk)** — Full method signatures and parameter details
- **[Architecture](architecture)** — Control plane internals
- **[Agent Types](../agents/overview)** — LLM, programmatic, human, external agents
- **[Quick Start](../getting-started/quickstart)** — Build your first system in 5 minutes

---

*LeafMesh — One class, full orchestration*
