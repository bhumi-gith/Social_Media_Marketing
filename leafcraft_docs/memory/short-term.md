# Session & State Management

LeafMesh uses Redis as its persistence layer for all session state, conversation history, agent yields, and mesh communications. All state management is handled automatically by LeafMesh.

## How State Works

All state management is **automatic**. When you call `leafmesh.mesh_call()`, LeafMesh:

1. Creates or loads a session (keyed by `session_id`)
2. Loads recent conversation history for context
3. Executes the agent pipeline (pre-compose, LLM call, intelligence function)
4. Auto-stores the agent's yields
5. Records the conversation entry (role, content, timestamp, agent name)
6. Stores mesh communications if `can_call` rules trigger downstream agents

You do not need to explicitly save or load state — LeafMesh handles it.

## Redis Configuration

```yaml
redis:
  host: "localhost"
  port: 6379
  db: 0
  password: null
  auto_storage: true       # Auto-persist yields and conversation (default: true)
  default_ttl: 3600        # 1 hour for general data
  session_ttl: 7200        # 2 hours for sessions
  cluster_mode: false      # Enable for Redis Cluster
  cluster_nodes: []        # Cluster node addresses
```

When `auto_storage` is enabled (default), every agent execution, mesh call, and coordination decision is persisted without explicit save calls.

## Session Lifecycle

### Creating and Using Sessions

Sessions are created automatically on first use:

```python
# First call creates the session
result = await leafmesh.mesh_call(
    "solver",
    input_data={"message": "What is 2 + 2?"},
    session_id="user_123"
)

# Second call reuses the same session — the agent has conversation history
result2 = await leafmesh.mesh_call(
    "solver",
    input_data={"message": "Now multiply that by 3"},
    session_id="user_123"
)
```

The agent receives recent conversation history as context automatically. The platform assembles it as user/assistant turns in the message array sent to the LLM.

### Session Data Structure

Each session stores structured conversation records:

```python
{
    "role": "user|assistant|system",
    "content": "The message content",
    "timestamp": "2026-02-26T10:30:00Z",
    "agent_name": "solver",
    "type": "user_message|agent_response|mesh_call|tool_result"
}
```

The `type` field distinguishes between direct user messages, agent LLM responses, inter-agent mesh communications, and tool execution results. The `agent_name` field provides attribution for every message.

### Inspecting Sessions

Browse session state via **Studio's Sessions tab**, or query it via the platform's REST API.

## Using Context in Intelligence Functions

The `context` parameter in intelligence functions provides access to session information:

```python
async def stateful_agent(llm_response, input_data, context):
    """Access session state within an intelligence function"""

    session_id = context.get("session_id", "default")
    yields = context.get("yields", {})

    return {
        "answer": llm_response.get("answer", ""),
        "has_history": len(yields) > 0
    }
```

## Auto-Stored Agent Yields

When an agent produces structured output (parsed from the LLM response according to the `yields` schema), the yields are **automatically stored in Redis** with session association. Downstream agents in the chain can access these yields through `input_data`.

```yaml
agents:
  # Step 1: Solver stores its yields automatically
  solver:
    name: "solver"
    model: "gpt-4o-mini"
    yields:
      answer: "number"
      steps: "array"
    can_call:
      - agent: "checker"
        condition: "answer >= 0"

  # Step 2: Checker receives solver's yields as input_data
  checker:
    name: "checker"
    model: "gpt-4o-mini"
    yields:
      is_correct: "boolean"
      explanation: "string"
```

When the solver completes, its yields (`answer`, `steps`) are:
1. Stored in Redis under the session
2. Passed as `input_data` to the checker via the mesh call

The checker's intelligence function receives the solver's output directly:

```python
async def checker(llm_response, input_data, context):
    # input_data contains the solver's yields
    claimed_answer = input_data.get("answer")  # From solver
    steps = input_data.get("steps", [])        # From solver

    # Verify independently
    return {
        "is_correct": True,
        "explanation": f"Verified answer: {claimed_answer}"
    }
```

## Automatic Persistence

### What Gets Stored Automatically

| Data | TTL |
|------|-----|
| Session metadata | `session_ttl` (default 7200s) |
| Conversation history | `session_ttl` |
| Agent yields | `default_ttl` (default 3600s) |
| Mesh communications | `default_ttl` |
| Coordination analyses | `default_ttl` |
| Coordination decisions | `default_ttl` |

## Inspecting State

Browse session state in **Studio's Sessions tab**, or query it via the platform's REST API.

This gives you the complete picture — every step is recorded as structured data.

## Persistence vs. Observability

LeafMesh enforces a clean boundary:

| Concern | Storage | Purpose |
|---------|---------|---------|
| Sessions, yields, mesh calls | **Redis** | Business-logic state the system needs to function |
| Traces, metrics, latency | **Observability layer** | Operational monitoring and debugging |

Traces are never stored in Redis. Business state is never stored in the tracing system. This separation means:

- Redis can be tuned for throughput (business-critical data)
- Observability backend can be tuned for query performance (operational analysis)
- Scaling one does not affect the other
- Data retention policies for each concern are independent

## Next Steps

- **[Architecture Guide](../core-concepts/architecture)** — How Redis fits into the control plane
- **[Agent Configuration](../api-reference/agent-config)** — Full YAML reference for session settings
- **[Monitoring Patterns](../advanced/yield-monitoring)** — Using session state for adaptive monitoring

---

*LeafMesh — Automatic state management, zero boilerplate*
