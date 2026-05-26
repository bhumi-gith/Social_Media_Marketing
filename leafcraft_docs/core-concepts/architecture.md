# LeafMesh Architecture

LeafMesh implements a **managed mesh architecture** that separates the control plane (routing, validation, oversight) from the data plane (agents executing tasks). This separation is the foundation of everything the system does.

## Control Plane / Data Plane

**Data plane**: Agents — they call LLMs, run tools, and produce outputs.
**Control plane**: Everything else — routing, policy enforcement, observation, intervention, persistence, health management, and event infrastructure.

The critical rule: **agents never communicate directly**. When Agent A's output triggers a call to Agent B, the output flows through the control plane — yields are parsed, conditions are evaluated, the platform classifies the event and checks for problems, and only then is Agent B invoked.

```
┌──────────────────────────────────────────────────────────────────────┐
│                  LeafMesh Control Plane (MANAGED_MESH)               │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   External Input                                                     │
│       │                                                              │
│       ▼                                                              │
│   ┌──────────────┐   ┌──────────────┐   ┌─────────────────────────┐  │
│   │ Entry Points │   │ Pre-Compose  │   │ Prompt Assembly         │  │
│   │ (YAML-defined│──▶│ Pipeline     │──▶│ (system + yields schema │  │
│   └──────────────┘   └──────────────┘   │  + conversation history)│  │
│                                          └───────────┬─────────────┘ │
│                                                      ▼               │
│   ┌──────────────┐   ┌──────────────┐   ┌─────────────────────────┐  │
│   │ LLM Providers│   │ Provider     │   │ YAML Agents             │  │
│   │ (OpenAI,     │◀──│ Layer        │◀──│ (yields, can_call,      │  │
│   │  Anthropic,  │   │ (multi-      │   │  tools, wake_up)        │  │
│   │  Google,     │   │  provider)   │   └───────────┬─────────────┘  │
│   │  DeepSeek,   │   └──────────────┘               │                │
│   │  Bedrock,    │                                  ▼                │
│   │  Vertex,     │   ┌──────────────┐   ┌─────────────────────────┐  │
│   │  Foundry,    │   │ Condition    │   │ Mesh Communication      │  │
│   │  Local)      │   │ Evaluator    │◀──│ (Agent-to-Agent Calls,  │  │
│   └──────────────┘   │ (AST-safe)   │   │  dual response,         │  │
│                       └──────────────┘   │  loop protection)       │  │
│                                          └───────────┬─────────────┘ │
│                                                      │               │
│   ┌─────────────────────────────────────────┐                        │
│   │ Automatic coordination & oversight       │◀──── observed events  │
│   │ (classifies events; intervenes on       │                        │
│   │  errors, timeouts, anomalies)           │                        │
│   └─────────────────────────────────────────┘                        │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────────┐   │
│   │ Business-state persistence                                   │   │
│   │ Sessions │ Yields │ Mesh Comms │ Decisions │ Event backbone  │   │
│   └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│   Observability ──── separate boundary ──── traces, metrics          │
└──────────────────────────────────────────────────────────────────────┘
```

## Architecture Pattern: Managed Mesh

LeafMesh implements a single architecture pattern: **MANAGED_MESH**. Despite the name, agents do not communicate in a peer-to-peer sense — every interaction is mediated by the control plane. The "mesh" describes the topology (any agent can potentially call any other agent), not the communication mechanism.

```yaml
name: "math_tutor_swarm"
architecture: "managed_mesh"

mesh:
  call_timeout: 300      # 5 minutes for complex workflows
  max_retries: 3         # Intelligent retry with backoff
  retry_backoff: 2       # Exponential backoff
```

**Why managed mesh:**
- **Fault tolerance**: Automatic failover and recovery
- **Visibility**: Complete observability at every handoff
- **Safety**: Policy enforcement at every routing decision
- **Auditability**: Every inter-agent call is logged and traceable

## Core Components

### YAML-Native Agent Definition

Agents are defined in YAML. A typical agent includes a prompt, output schema (yields), conditional routing (can_call), and tool access:

```yaml
agents:
  solver:
    name: "solver"
    model: "gpt-4o-mini"
    prompt: |
      You solve math problems step by step.
      Show your work clearly.
    yields:
      problem: "string"
      answer: "number"
      steps: "array"
    can_call:
      - agent: "checker"
        condition: "answer > 0"
        call_immediately: true
      - agent: "reporter"
        condition: "answer > 100"
    tools: ["calculator"]
    tool_choice: "auto"
```

**How this executes** when you send `"2 + 1"`:

1. **History retrieval**: Conversation history is loaded automatically
2. **Message construction**: Structured messages are assembled — system prompt, yields schema, history, user input
3. **Tool binding**: Tools from the `tools` array are loaded
4. **Provider selection**: The configured model is routed to the appropriate provider
5. **LLM execution**: Provider receives the complete request
6. **Yield parsing**: Response is validated against the declared schema — `answer` must be a number
7. **Condition evaluation**: `answer > 0` is evaluated using the AST-safe evaluator
8. **Mesh routing**: The call is dispatched to `checker`

### Communication Engine

#### Dual Response Pattern

Agents can provide immediate responses while simultaneously triggering background mesh calls:

```yaml
agents:
  solver:
    communication_type: "dual"    # Respond immediately, route in background
    can_call:
      - agent: "checker"
        timeout: 60
      - agent: "logger"
        async: true               # Fire-and-forget
```

The system returns the solver's response immediately while asynchronously processing the `can_call` chains. User-facing agents respond quickly while analysis workflows execute in the background.

#### AST-Safe Condition Evaluation

Routing conditions in YAML are evaluated using Python's `ast` module — never `eval()`. Only whitelisted node types are allowed:

```yaml
can_call:
  # Simple comparison
  - agent: "checker"
    condition: "answer > 0"

  # String equality
  - agent: "error_handler"
    condition: "status == 'error'"

  # Compound boolean
  - agent: "escalator"
    condition: "confidence < 0.5 && answer > 100"

  # Arithmetic
  - agent: "review"
    condition: "error_count + warning_count > 5"

  # Nested field access
  - agent: "enricher"
    condition: "calling_agent_response.quality_score >= 0.7"

  # Unconditional (always call)
  - agent: "logger"
    condition: ""
```

If a condition references an undefined variable, it evaluates to `False` with a warning. Code injection is prevented at the parser level.

#### Loop Protection

The platform tracks call chain depth and prevents infinite loops in `can_call` configurations where Agent A calls B which calls A.

### Multi-Layer Validation Pipeline

Every agent response passes through a multi-layer validation pipeline. The majority of layers are fully deterministic:

- **Yield parsing** — catches schema violations (wrong types, missing fields)
- **Condition evaluation** — catches invalid routing
- **Intelligence function** — catches business-logic violations
- **Automatic oversight** — catches workflow anomalies and coordination problems
- **Downstream validation** — catches input-contract violations

A hallucinated response must pass every layer to reach the end user.

### Built-in Oversight

LeafMesh includes automatic coordination that observes every event in the control plane and intervenes when something goes wrong — retrying transient failures, halting on persistent errors, and escalating to human review when configured.

- **Observation** is event-driven and asynchronous — it does not block agent execution.
- **Intervention** is reactive — when everything runs normally, overhead is negligible.
- **Behavior** is configurable via the `manager:` section in YAML (see [Automatic Coordination](manager)).

### Pre-Compose Pipeline

Before any LLM call, an optional deterministic pre-processing pipeline runs:

```python
from leafmesh import pre_compose

@pre_compose(
    context_processor=build_context,      # Assemble business context
    input_processor=clean_user_input,     # Sanitize input
    others_processor=handle_metadata      # Handle supplementary data
)
async def solver(llm_response, input_data, context):
    return llm_response
```

All three processors are plain Python — no LLM calls. They execute before prompt assembly, ensuring clean, structured input.

## Redis Integration

Redis handles business-logic persistence. The observability layer handles tracing and metrics. These boundaries are enforced architecturally.

```yaml
redis:
  host: "${REDIS_HOST}"
  port: 6379
  db: 0
  password: "${REDIS_PASSWORD}"
  auto_storage: true
  session_ttl: 604800    # 7 days
```

**What Redis stores:**
- **Sessions**: Conversation history with configurable TTL
- **Yields**: Agent output state for cross-agent communication
- **Mesh communications**: Inter-agent call logs
- **Decisions**: Coordination history
- **Event backbone**: durable event log for replay

**What Redis does NOT store:** Traces, metrics, or performance data — those are handled by the managed observability pipeline.

## Observability

```yaml
observability:
  service_name: "math_tutor_swarm"
  metrics_retention_minutes: 60
```

Observability is built-in and auto-enabled by your license key.

- **Distributed tracing**: Full request flow visibility across all agents
- **Performance metrics**: Real-time monitoring with configurable retention
- **Health endpoints**: System health and readiness checks
- **Dashboard API**: Accessible at `http://your-server:18820`

## Self-Healing Networks

```yaml
self_healing:
  enabled: true
  detection_interval: 30
  recovery_strategies:
    - "restart_agent"
    - "failover_to_backup"
    - "circuit_breaker"
  max_recovery_attempts: 3
```

Healing actions execute automatically without human intervention. The platform can restart failed agents, route traffic away from unhealthy ones, scale healthy agents to absorb load, isolate persistent failures, and roll configurations back to a last-known-good state. Specific strategies are configurable.

## Evolution (Health Check)

Operators can re-run defined scenarios against the running configuration to detect quality drift over time. Health-check mode is the default. Runs from Studio with operator-supplied scenarios; the running mesh continues serving traffic untouched. See [Evolutionary Optimization](../advanced/evolutionary-optimization).

## Adaptive LLM Executor

```yaml
adaptive_llm:
  enabled: true
  cost_optimization: true
  model_selection_strategy: "performance_based"
  fallback_models:
    - "gpt-4o-mini"
    - "gpt-3.5-turbo"
```

The platform classifies incoming requests and selects models accordingly. Automatic fallback chains ensure requests are not dropped due to provider issues.

## Deployment Patterns

### Docker
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . /app
WORKDIR /app
EXPOSE 8002
CMD ["python", "main.py"]
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: swarm-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: leafmesh-adk
  template:
    spec:
      containers:
      - name: leafmesh-adk
        image: leafmesh-adk:latest
        ports:
        - containerPort: 18820
        env:
        - name: REDIS_HOST
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: host
```

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Agent startup | < 2 seconds |
| Mesh call latency (local) | < 100ms |
| Mesh call latency (distributed) | < 500ms |
| Session recovery | < 1 second |
| Memory per agent | 50–200MB |
| Throughput per agent | 1000+ requests/second |

## Design Principles

1. **Configuration as code**: YAML is the primary interface. Python is optional enhancement.
2. **Event-driven communication**: All inter-component communication flows through an internal event backbone.
3. **Persistence/observability separation**: Redis for business state, a managed observability pipeline for operational data.

These principles reinforce each other. Configuration-as-code enables auditability. Event-driven communication enables persistence and replay. Separating business state from observability keeps the control plane clean.

## Next Steps

- **[LeafMesh Class Reference](leafmesh-adk)** — Core API documentation
- **[Agent Development](../agents/overview)** — Building and configuring agents
- **[Self-Healing Guide](../advanced/self-healing)** — Production resilience
- **[Multi-Agent Example](../examples/yield-monitoring)** — Calculator → Validator pipeline

---

*LeafMesh Architecture — Built for enterprise-scale multi-agent systems*
