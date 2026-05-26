# SocialMediaMarketing_v2

A LeafMesh multi-agent project with Human-in-the-Loop (HITL), fan-in/fan-out patterns, smart memory, scheduled agents, and more.

## Quick Start

```bash
# 1. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
#    Edit .env with your API keys (OPENAI_API_KEY, LEAFMESH_LICENSE_KEY, Redis)

# 3. Start Redis (if not already running)
docker compose up redis -d
# Or: redis-server

# 4. Start the mesh
python main.py
```

The mesh starts an API server at **http://127.0.0.1:18820**. Visit `/docs` for interactive API docs.

## Project Structure

```
SocialMediaMarketing_v2/
  configs/
    config.yaml              # Agent definitions, mesh wiring, HITL config
  agency/
    greeter_agent.py         # LLM agent with @pre_compose
    processor_agent.py       # Programmatic agent with @conditional_chain
    researcher_agent.py      # LLM agent with @chain_with_results + smart memory
    fallback_researcher_agent.py  # Programmatic fast fallback (race pattern)
    advisor_agent.py         # LLM fan-in agent with @chain + @compose
    scheduler_agent.py       # Cron-scheduled agent (daily reports)
    tools.py                 # Custom tools (@global_tool, @tool)
    external_agents.py       # Integration reference (CrewAI, LangGraph, etc.)
  main.py                    # Entry point
  hitl_stub_receiver.py      # Webhook stub for testing HITL locally
  requirements.txt
  .env                       # API keys and config
  Dockerfile
  docker-compose.yml         # Redis + app (one command)
```

## Agent Flow

```
                              HITL Scenario 1 (system-initiated)
                              ===================================
  API request                 greeter_agent (LLM)
  "greet_user"  ─────────>       |
                                 v
                              client (human agent, HITL)
                              [outbound webhook → human reviews → inbound webhook]
                                 |
                                 v
                              processor_agent (programmatic, parallel)
                              ┌──┼──┐
                              v  v  v
                    researcher  fallback  advisor (waits)
                    (LLM)      (instant)     |
                              └──────────────┘
                              advisor_agent (OR fan-in)
                              [processor AND (researcher OR fallback)]


                              HITL Scenario 2 (human-initiated)
                              ==================================
  Webhook                     client (human agent)
  "human_contact"  ──────>       |  (no from_agent → route to greeter)
                                 v
                              greeter_agent (LLM)
                                 |  (dual callback → client)
                                 v
                              client (HITL, from_agent = "greeter_agent")
                              [outbound webhook → human reviews → inbound webhook]
                                 |  (from_agent == "greeter_agent" → route to processor)
                                 v
                              processor_agent → researcher + fallback → advisor
```

## HITL Walkthrough

### Prerequisites

You need **3 terminals** open:

| Terminal | Purpose |
|----------|---------|
| Terminal 1 | HITL stub receiver (captures outbound webhooks) |
| Terminal 2 | LeafMesh server |
| Terminal 3 | curl commands (trigger mesh + respond as human) |

### Step 1: Start the Stub Receiver

```bash
# Terminal 1
python hitl_stub_receiver.py
```

This listens on port 9999 and prints outbound webhook payloads when the human agent is invoked.

### Step 2: Start the Mesh

```bash
# Terminal 2
python main.py
```

Wait for "SocialMediaMarketing_v2 is running" in the logs.

### Step 3: Get Your Webhook Signing Secret

```bash
# Terminal 3
curl http://127.0.0.1:18820/api/webhook/secret
```

Save the `secret` value — you'll need it to sign inbound webhook responses.

### Scenario 1: System-Initiated HITL

The system triggers a workflow, and the human agent is called mid-flow for review.

**Trigger the mesh:**

```bash
# Terminal 3
curl -X POST http://127.0.0.1:18820/api/mesh/request \
  -H "Content-Type: application/json" \
  -d '{"entry_point": "greet_user", "data": {"message": "I need help with item1, item2, item3"}}'
```

**What happens:**
1. `greeter_agent` processes the message via LLM
2. `greeter_agent` routes to `client` (human agent)
3. SDK sends outbound webhook to the stub receiver (Terminal 1)
4. The stub prints a curl command to respond

**Respond as the human** (compute HMAC + timestamp + nonce — required by the SDK):

```bash
# Terminal 3 — sign and respond
# Replace SESSION_ID with the session_id from the stub output
# Replace SECRET with the value from /api/webhook/secret

BODY='{"session_id": "SESSION_ID", "decision": "approved", "message": "Looks good, proceed with item1, item2, item3"}'
SECRET="your-secret-here"
TS=$(date +%s)
NONCE=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')

# Signed material: "{timestamp}.{nonce}.{body}"
SIG=$(printf '%s' "$TS.$NONCE.$BODY" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $NF}')

curl -X POST http://127.0.0.1:18820/webhook/greet_user \
  -H "Content-Type: application/json" \
  -H "X-LeafMesh-Signature: sha256=$SIG" \
  -H "X-LeafMesh-Timestamp: $TS" \
  -H "X-LeafMesh-Nonce: $NONCE" \
  -d "$BODY"
```

**Result:** The human's response flows through `processor_agent` → `researcher_agent` + `fallback_researcher_agent` → `advisor_agent`.

### Scenario 2: Human-Initiated HITL

The human initiates contact, the system processes it, and the human reviews before final processing.

**Trigger via webhook:**

```bash
# Terminal 3
BODY='{"message": "I want to report an issue with item1, item2"}'
SECRET="your-secret-here"
TS=$(date +%s)
NONCE=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')
SIG=$(printf '%s' "$TS.$NONCE.$BODY" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $NF}')

curl -X POST http://127.0.0.1:18820/webhook/human_contact \
  -H "Content-Type: application/json" \
  -H "X-LeafMesh-Signature: sha256=$SIG" \
  -H "X-LeafMesh-Timestamp: $TS" \
  -H "X-LeafMesh-Nonce: $NONCE" \
  -d "$BODY"
```

**What happens:**
1. `client` receives the message (no `from_agent` → routes to `greeter_agent`)
2. `greeter_agent` processes via LLM and responds back to `client`
3. SDK sends outbound webhook to the stub receiver (Terminal 1)
4. The stub prints a curl command to respond

**Respond as the human** (same pattern as Scenario 1 — use the session_id from the stub output).

**Result:** `from_agent == "greeter_agent"` → routes to `processor_agent` → full chain completes.

### How `from_agent` Routing Works

The `client` agent's `can_call` uses conditions to determine where to route:

```yaml
can_call:
  - agent: "greeter_agent"
    condition: "not calling_agent_response.from_agent"    # No caller → greet first
  - agent: "processor_agent"
    condition: "calling_agent_response.from_agent == 'greeter_agent'"  # Greeter done → process
```

When an agent calls the human agent, the SDK stores which agent called (`called_by`) in Redis. When the human responds via webhook, the SDK includes `from_agent` in the output data so `can_call` conditions can route accordingly.

## Key Concepts

### Agent Types

| Type | Description | Example |
|------|-------------|---------|
| `human` | Human-in-the-loop via webhook/channel | `client` |
| `llm` | LLM-powered with prompt + tools | `greeter_agent`, `researcher_agent` |
| `programmatic` | Pure Python logic, no LLM | `processor_agent`, `scheduler_agent` |
| `external` | Delegates to CrewAI, LangGraph, etc. | See `external_agents.py` |

### Decorators

| Decorator | Purpose | Example Agent |
|-----------|---------|---------------|
| `@pre_compose(fn1, fn2, ...)` | Pre-process input before LLM call | `greeter_agent` |
| `@chain(fn1, fn2, ...)` | Sequential post-processing pipeline | `advisor_agent` |
| `@chain_with_results(fn1, fn2)` | Accumulate results across steps | `researcher_agent` |
| `@conditional_chain(cond, true_fn, false_fn)` | Branch based on condition | `processor_agent` |
| `@compose(key=fn, ...)` | Inject shaped data per downstream agent | `advisor_agent` |

### Fan-In Patterns (`wait_for`)

```yaml
wait_for: "A AND B"                    # Wait for both
wait_for: "A OR B"                     # First wins
wait_for: "A AND B?"                   # A required, B optional
wait_for: "A AND (B OR C)"            # A required + first of B or C
```

### Smart Memory

```yaml
memory:
  strategy: "hybrid"          # recency | relevance | hybrid
  limit: 10                   # Max entries per invocation
  cross_session: true         # Persist across sessions
  relevance_weight: 0.6
  recency_weight: 0.4
```

### Upstream Yields

Agents define `yields` in YAML. The SDK auto-stores them in Redis and injects them into downstream agents as `input_data["upstream_yields"][agent_name]`.

### Scheduled Agents

```yaml
scheduler_agent:
  wake_up: "0 9 * * *"       # Cron expression (9 AM UTC daily)
```

Also triggerable on-demand via `mesh_call("scheduled_report", data)`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/mesh/request` | Trigger agent workflows via entry points |
| POST | `/api/mesh/stream` | SSE stream of LLM response |
| POST | `/webhook/{entry_point}` | Webhook (new task or human HITL response) |
| GET | `/api/mesh/entry_points` | List configured entry points |
| GET | `/api/agents/` | List all agents |
| GET | `/api/sessions/` | List active sessions |
| GET | `/api/sessions/{id}/history` | Conversation history |
| GET | `/api/webhook/secret` | HMAC signing secret |
| GET | `/health` | Health check |
| GET | `/docs` | Interactive API docs (ReDoc) |

## Docker

```bash
# Start Redis + app
docker compose up --build

# Or just Redis (run app locally)
docker compose up redis -d
```

## Configuration

All agent wiring is in `configs/config.yaml`. Key sections:

- **`entry_points`** — Named portals into the mesh
- **`agents`** — Agent definitions (type, model, can_call, yields, etc.)
- **`manager`** — Built-in coordinator with learning-based routing and escalation
- **`mesh`** — Timeout and cloud LLM provider configs

## Observability

Observability auto-enables when `LEAFMESH_LICENSE_KEY` is set in `.env`. Traces, metrics, and logs flow automatically. Set `LEAFMESH_ENV_TOKEN` to group telemetry by environment.

## Links

- [LeafMesh SDK](https://pypi.org/project/leafmesh/)
- [LeafCraft Studios](https://leafcraft.ai)
