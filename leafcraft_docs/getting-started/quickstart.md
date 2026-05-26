# LeafMesh Quick Start

Build your first agent mesh in **5 minutes**.

## Step 1: Install LeafMesh

```bash
pip install leafmesh
```

Or use the scaffolding tool for a complete project:

```bash
pip install create-leafmesh
create-leafmesh my-project
cd my-project
```

## Step 2: Create Your Config

Create `configs/config.yaml`:

```yaml
name: "my-first-mesh"
architecture: "managed_mesh"

redis:
  host: "localhost"
  port: 6379

manager:
  enabled: true
  model: "gpt-4o-mini"

entry_points:
  - name: "ask"
    target: "greeter"

agents:
  greeter:
    name: "greeter"
    model: "gpt-4o-mini"
    prompt: "You are a friendly assistant. Greet the user and help with their request."
    temperature: 0.7
    max_tokens: 500
    yields:
      greeting: "string"
      summary: "string"
    can_call:
      - agent: "researcher"
        condition: "true"

  researcher:
    name: "researcher"
    model: "gpt-4o"
    prompt: "You research topics thoroughly and provide detailed answers."
    temperature: 0.3
    max_tokens: 1500
    tools: ["web_request", "chain_of_thought"]
    yields:
      findings: "string"
      confidence: "number"
```

## Step 3: Add Python Intelligence (Optional)

Create `agency/greeter.py`:

```python
from leafmesh import pre_compose

@pre_compose(context_processor=lambda ctx: {"tone": "professional"})
async def greeter(llm_response, input_data, context):
    """Enhance the greeter with custom logic"""
    return {
        "greeting": llm_response.get("greeting", "Hello!"),
        "summary": llm_response.get("summary", str(input_data)),
    }
```

The `@pre_compose` decorator shapes input before the LLM call. The agent function runs **after** the LLM responds, adding deterministic validation.

## Step 4: Create the Entry Point

Create `main.py`:

```python
import asyncio
from leafmesh import LeafMesh

async def main():
    leafmesh = LeafMesh.from_yaml("configs/config.yaml")
    await leafmesh.start()

    print(f"LeafMesh running!")
    print(f"API docs: http://127.0.0.1:18820/docs")
    print("Press Ctrl+C to stop")

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await leafmesh.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Step 5: Set Environment Variables

```bash
export LEAFMESH_LICENSE_KEY="your-license-key"
export OPENAI_API_KEY="your-openai-key"
```

> **Tip:** You can use any supported provider. Change agent models to `claude-3.5-sonnet` (Anthropic), `gemini-2.5-flash` (Google), `bedrock/claude-3.5-sonnet` (AWS Bedrock), `vertex/gemini-2.5-flash` (Google Vertex AI), or `foundry/gpt-4o` (Microsoft Foundry). See [LLM Providers](../models/providers) for setup.

## Step 6: Start Redis and Run

```bash
# Start Redis (if not already running)
redis-server &

# Run your mesh
python main.py
```

## Step 7: Test It

Open `http://127.0.0.1:18820/docs` for the interactive API explorer, or use curl:

```bash
curl -X POST http://127.0.0.1:18820/api/mesh/request \
  -H "Content-Type: application/json" \
  -d '{
    "entry_point": "ask",
    "data": {"message": "Hello! Tell me about machine learning."},
    "session_id": "my-first-session"
  }'
```

## What Just Happened?

1. **YAML config** defined two agents with structured `yields` schemas
2. **Entry point** `ask` routes requests to `greeter`
3. **`can_call`** routing automatically chains `greeter` → `researcher`
4. **Built-in coordination** provides oversight and automatic intervention
5. **Session management** persists conversation across requests
6. **API server** exposes everything at `:18820` with OpenAPI docs
7. **Observability** auto-enabled with your license key

## Key Concepts

### Entry Points
Entry points are the external-facing API for your mesh. Define them in YAML, call them via `POST /api/mesh/request`.

### Agent Routing (`can_call`)
Agents declare which agents they can call and under what conditions:
```yaml
can_call:
  - agent: "next_agent"
    condition: "confidence > 0.8"  # AST-safe condition on yields
```

### Fan-In (Wait For)
When multiple agents need to contribute before a final agent runs:
```yaml
agents:
  final_agent:
    wait_for: "agent_a AND (agent_b OR agent_c)"
    wait_for_timeout: 60
```

### Python Intelligence
Add deterministic logic on top of LLM responses. The function name must match the agent name in YAML:
```python
async def agent_name(llm_response, input_data, context):
    # LLM handles interpretation, Python handles logic
    return {"validated_result": compute(llm_response)}
```

## API Endpoints

Your LeafMesh API server runs at `http://127.0.0.1:18820` with these key endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/mesh/request` | Submit a request via entry point |
| POST | `/api/mesh/stream` | SSE stream of LLM response via entry point |
| GET | `/api/mesh/entry_points` | List available entry points |
| POST | `/webhook/{entry_point}` | Webhook — new task or human response (see below) |
| POST | `/callback/{agent_name}` | External-system callback for `mode: callback` connectors |
| GET | `/health` | Health check |

### Webhook Endpoint

`POST /webhook/{entry_point}` is a single unified endpoint for external integrations (Slack, Zapier, n8n, etc.). The `{entry_point}` is the name from your `entry_points` config (e.g. `greet_user`, `research`).

**Smart routing based on your payload:**

| Payload | Behavior |
|---------|----------|
| No `session_id` in body | **New task** — routes to the agent mapped to this entry point |
| `session_id` matching a paused workflow | **Resume** — delivers the human response to the waiting agent |

```bash
# New task — Slack sends a message
curl -X POST http://localhost:18820/webhook/greet_user \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, I need help"}'

# Human response — resume a paused workflow
curl -X POST http://localhost:18820/webhook/greet_user \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sess_abc123", "decision": "approved"}'
```

## Enable Production Features

### Observability (Auto-Enabled)
Observability is included by default and auto-enabled when `LEAFMESH_LICENSE_KEY` is set. Traces, metrics, and logs are collected automatically.

### Self-Healing
```yaml
self_healing:
  enabled: true
  detection_interval: 30
  max_recovery_attempts: 3
```

### Webhook Signing
Outbound webhook payloads are signed with `X-LeafMesh-Signature`. Configure or rotate the webhook secret via Studio settings (or `LEAFMESH_WEBHOOK_SECRET`) and use it to verify the signature on the receiving side.

## Next Steps

- **[Architecture Guide](../core-concepts/architecture)** — Control plane and mesh patterns
- **[Agent Development](../agents/development)** — Agent types and Python intelligence
- **[Fan-In/Fan-Out](../multi-agent/communication)** — Complex agent workflows
- **[Customer Service Example](../examples/customer-service)** — Full production example

---

*LeafMesh — YAML-native multi-agent orchestration platform*
