# LeafMesh Class

The main entry point for LeafMesh. Manages the complete lifecycle of a multi-agent system.

## Import

```python
from leafmesh import LeafMesh
```

## Construction

### `LeafMesh.from_yaml(path: str) -> LeafMesh`

Load configuration from a YAML file:

```python
leafmesh = LeafMesh.from_yaml("configs/config.yaml")
```

Validates: file existence, size (< 10MB), YAML syntax, required fields, Pydantic models, UTF-8 encoding.

### `LeafMesh.from_dict(config: dict) -> LeafMesh`

```python
leafmesh = LeafMesh.from_dict({
    "name": "my_system",
    "architecture": "managed_mesh",
    "agents": { ... }
})
```

### `LeafMesh(config: Optional[LeafMeshConfig] = None)`

Direct construction. If no config provided, creates a default `LeafMeshConfig()`.

### Context Manager

```python
async with LeafMesh.from_yaml("config.yaml") as leafmesh:
    result = await leafmesh.mesh_call("support_request", data, session_id="s1")
```

## Lifecycle Methods

### `await leafmesh.start()`

Initializes all internal components, connects to Redis, registers agents from YAML configuration, starts the API server on port 18820, and begins processing requests.

```python
await leafmesh.start()
```

### `await leafmesh.stop()`

Graceful shutdown. Drains in-flight requests (30s timeout), stops the API server, and disconnects from Redis.

```python
await leafmesh.stop()
```

## Request Processing

### `await leafmesh.mesh_call(entry_point_name, data, session_id=None) -> Any`

Route a request through a configured entry point:

```python
result = await leafmesh.mesh_call(
    "support_request",                       # Entry point name from YAML
    {"user_message": "My API is down"},      # Input data
    session_id="session_001"
)
```

This is the primary way to send requests into the system. The entry point maps to a target agent, which triggers the full pipeline: pre-compose → prompt assembly → LLM call → tool execution → yields parsing → can_call evaluation → intelligence function → downstream mesh routing.

### `await leafmesh.rerun_agent(agent_name, session_id, *, feedback=None, reason="user_request", new_input=None) -> dict`

Re-run a single agent inside an existing session, optionally with feedback so it can self-correct (`leafmesh >= 1.0.299`). Use this to:

* Wire a "Rerun" button in your own UI
* Build custom retry rules outside Manager's analysis-driven path
* Trigger a deterministic rerun from a debugging script

Routes through the same Manager retry path used by strict yields enforcement and analysis-driven retries. See [Manager — Retry & Rerun](../core-concepts/manager#retry-and-rerun) for the full flow.

```python
# Simple retrigger — same input as last time, no feedback
result = await leafmesh.rerun_agent(
    agent_name="advisor_agent",
    session_id="session-1777755-wrh93qrf",
)

# Retrigger with feedback (e.g. the caller spotted a bad shape)
result = await leafmesh.rerun_agent(
    agent_name="advisor_agent",
    session_id="session-1777755-wrh93qrf",
    feedback={
        "previous_output": {"recommendation": "vague answer"},
        "error": "Recommendation lacks specific action items",
        "expected_shape": {"recommendation": "string", "action_items": "list"},
    },
    reason="schema_mismatch",
)

# Retrigger with brand-new input (deliberately steer the agent)
result = await leafmesh.rerun_agent(
    agent_name="processor_agent",
    session_id="session-1777755-wrh93qrf",
    new_input={"message": "Now check my refund instead", "request_type": "refund"},
)
```

| Argument | Type | Default | Description |
|---|---|---|---|
| `agent_name` | string | — | Agent to re-run (must be registered in this mesh). |
| `session_id` | string | — | Session this rerun belongs to. |
| `feedback` | dict | `None` | Merged into the agent's input as `_rerun_context` so it can see what went wrong. Common keys: `previous_output`, `error`, `expected_shape`. |
| `reason` | string | `"user_request"` | Audit string surfaced in retry telemetry. Common values: `user_request`, `schema_mismatch`, `manager_intervention`, `frontend_rerun_button`, `agent_error`. |
| `new_input` | dict | `None` | Explicit input. When omitted, the SDK fetches the agent's most recent stored input from `auto_store_agent_input`. |

The feedback is rendered per-agent-type — LLM agents get a correction note in their prompt, human agents see it surfaced in their inbox/channel UI, external connectors receive `data._rerun_context`, programmatic agents receive `input_data._rerun_context`. The same dispatch handles every type, so feedback semantics are uniform.

Returns dispatch metadata (the actual agent execution is asynchronous — subscribe to events on `session_id` for the result):

```python
{
    "status": "dispatched",
    "agent": "advisor_agent",
    "session_id": "session-1777755-wrh93qrf",
    "input_source": "stored_original" | "new_input",
    "reason": "user_request",
}
```

The same operation is exposed in **Studio's Sessions tab** as a per-agent rerun button (with optional feedback / new input). Both the Python method and the Studio button route through the same Manager retry path, so feedback rendering is consistent across surfaces.

## Agent Registration

### Intelligence Functions

Register a post-LLM intelligence function. The function name must match the agent name in YAML — `leafmesh.discover()` finds them automatically:

```python
async def my_agent(llm_response, input_data, context):
    # 3-param: receives LLM response, input, and context
    return llm_response
```

### `@pre_compose(...)`

Standalone decorator for pre-LLM processing. Runs deterministic Python before the LLM call:

```python
from leafmesh import pre_compose

@pre_compose(input_processor=lambda data: {**data, "extra": "data"})
async def my_agent(llm_response, input_data, context):
    return llm_response
```

### `leafmesh.discover(directory=".", pattern="*_agent.py", recursive=False)`

Auto-discover and register intelligence functions from files. Functions are matched to agents by name — the function name must match the agent name in YAML:

```python
leafmesh.discover("./agents", pattern="*_agent.py", recursive=True)
```

## Function Composition

### `leafmesh.chain(*functions)`

Chain multiple functions into a pipeline:

```python
pipeline = leafmesh.chain(validate, process, format_output)
```

### `leafmesh.conditional_chain(condition_func, *functions)`

Chain that only executes if condition is met.

### `leafmesh.chain_with_results(*functions)`

Chain that collects results from all functions.

### `leafmesh.compose(**processors)`

Composition decorator for modular components.

## Evolution

> **Removed from the runtime SDK in v2.1.54.** The in-process
> `leafmesh.evolve_mesh_architecture()` method now raises with a
> pointer to the standalone evolution service. Operators kick off
> runs from Studio — see [Evolutionary Optimization](../advanced/evolutionary-optimization).

## Analytics & Monitoring

| Method | Returns |
|--------|---------|
| `leafmesh.get_usage_analytics()` | Aggregated event statistics |
| `leafmesh.get_llm_cache_stats()` | Cache hit rates, savings, size |
| `leafmesh.get_status()` | System status dictionary |
| `leafmesh.list_agents()` | List of registered agent names |

Analytics are also available via the REST API (see below).

## REST API Endpoints (Port 18820)

LeafMesh API server runs at `http://127.0.0.1:18820`.

### Mesh & Webhook

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| POST | `/api/mesh/request` | Submit a request via an entry point |
| GET | `/api/mesh/entry_points` | List configured entry points |
| POST | `/api/mesh/stream` | Stream a mesh request (SSE) |
| POST | `/webhook/{entry_point}` | Webhook ingress — new task or human response |
| POST | `/callback/{agent_name}` | External-system callback for `mode: callback` connectors |

### YAML / Agent CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/yaml/config` | Full mesh config (agents, brokers, entry points, manager, redis, etc.) |
| PATCH | `/api/yaml/config` | Partial config update (deep-merged) — pass `{"updates": {...}, "save_to_disk": false}` |
| POST | `/api/yaml/validate` | Validate a YAML body without applying |
| POST | `/api/yaml/load` | Reload from a YAML body |
| GET | `/api/yaml/agents` | List agents |
| GET | `/api/yaml/agents/{name}` | Get one agent |
| POST | `/api/yaml/agents` | Create an agent |
| PATCH | `/api/yaml/agents/{name}` | Partial agent update |
| DELETE | `/api/yaml/agents/{name}` | Delete an agent |

### Broker CRUD (BRD-021)

Top-level `brokers:` are managed independently of agents — the same connection serves any number of `listen_events` subscriptions.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/yaml/brokers` | List all brokers (secrets redacted) |
| GET | `/api/yaml/brokers/{name}` | Get one broker (secrets redacted) |
| POST | `/api/yaml/brokers/{name}` | Create or replace a broker |
| PATCH | `/api/yaml/brokers/{name}` | Partial broker update — preserves the `type` discriminator |
| DELETE | `/api/yaml/brokers/{name}` | Delete a broker. If any agent's `listen_events` references it, the response includes an `orphan_warnings` field listing affected agents (allow-with-warning, not fail-closed) |

**Response shape:**

```json
{
  "success": true,
  "data": {
    "name": "prod_kafka",
    "broker": {
      "type": "kafka",
      "bootstrap_servers": ["kafka-1:9092"],
      "sasl_password": "***REDACTED***"
    }
  },
  "metadata": { "version": "1.0.318" }
}
```

**Secret redaction:** `sasl_password`, `aws_secret_access_key`, `aws_session_token`, `password`, and any field matching the existing redaction rules are returned as `"***REDACTED***"` on GET responses. PATCH requests that omit a previously-set secret retain the stored value (no inadvertent erasure).

### Listener Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/system/event-listeners` | Live listener status — broker, source, state, in-flight count, last-success timestamp, retry/DLQ counters |

**Response shape:**

```json
{
  "success": true,
  "data": {
    "listeners": [
      {
        "agent": "order_processor",
        "listener": "order_processor.0",
        "broker": "prod_kafka",
        "source": { "topic": "orders.new", "group_id": "order-processor-v1" },
        "state": "running",
        "in_flight": 2,
        "last_success_ts": "2026-05-09T10:30:12Z",
        "counters": {
          "received": 1284,
          "dispatched": 1276,
          "filtered": 6,
          "retried": 12,
          "dead_lettered": 2
        }
      }
    ]
  }
}
```

States: `running`, `paused` (config reload in progress), `failed` (broker connection lost — auto-reconnect retrying), `stopped` (SDK shutting down).

## Next Steps

- **[Agent Classes](agents)** — Agent API reference
- **[Configuration API](configuration)** — Config reference
- **[Event System](events)** — Events and real-time monitoring

---

*LeafMesh — LeafMesh class reference*
