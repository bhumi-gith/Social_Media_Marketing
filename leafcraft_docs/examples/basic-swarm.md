# Basic Swarm Setup

A minimal two-agent system demonstrating core LeafMesh concepts: YAML configuration, conditional routing, and intelligence functions.

## Configuration

```yaml
# configs/config.yaml
name: "support_system"
architecture: "managed_mesh"

agents:
  triage_agent:
    name: "triage_agent"
    model: "gpt-4o-mini"
    prompt: |
      Classify the incoming request by urgency (1-10) and category.
      Route urgent requests to specialists.
    yields:
      urgency: "number"
      category: "string"
      summary: "string"
    can_call:
      - agent: "specialist_agent"
        condition: "urgency >= 7"
        call_immediately: true

  specialist_agent:
    name: "specialist_agent"
    model: "gpt-4o"
    prompt: |
      You are a specialist handler for urgent requests.
      Provide detailed analysis and resolution steps.
    yields:
      analysis: "string"
      resolution_steps: "string"
      confidence: "number"

manager:
  enabled: true
  model: "gpt-4o-mini"
  coordination_rules:
    max_agent_calls: 10

redis:
  host: "localhost"
  port: 6379

entry_points:
  - name: "support_request"
    target: "triage_agent"
    description: "Incoming support requests"
```

## Application Code

```python
# app.py
import asyncio
from leafmesh import LeafMesh

leafmesh = LeafMesh.from_yaml("configs/config.yaml")

# Function name "specialist_agent" matches the YAML agent name — auto_discover finds it
async def specialist_agent(llm_response, input_data, context):
    """Add business context to specialist analysis"""
    llm_response["handled_by"] = "specialist_team"
    return llm_response

async def main():
    await leafmesh.start()

    result = await leafmesh.mesh_call(
        "support_request",                                    # Entry point name
        {"user_message": "Our production database is down"},  # Input data
        session_id="session_001"
    )

    print(result)
    await leafmesh.stop()

asyncio.run(main())
```

## What Happens When This Runs

1. `leafmesh.start()` brings the mesh online and registers your agents
2. `leafmesh.mesh_call()` routes through the "support_request" entry point to `triage_agent`
3. The LLM produces structured output matching the yields schema: `{urgency: 9, category: "technical", summary: "..."}`
4. The `can_call` conditions are evaluated against the yields
5. `urgency >= 7` matches, so `specialist_agent` is called immediately
6. Specialist receives the triage yields as `input_data`
7. The `specialist_agent` intelligence function adds `handled_by`
8. Session state, yields, and conversation history are persisted automatically

## Architecture Diagram

```
User Message: "Production database is down"
    │
    ▼
triage_agent (gpt-4o-mini)
    │ yields: {urgency: 9, category: "technical", summary: "..."}
    │
    │ condition: urgency >= 7 ✓
    ▼
specialist_agent (gpt-4o)
    │ yields: {analysis: "...", resolution_steps: "...", confidence: 0.9}
    │ + intelligence function adds: handled_by: "specialist_team"
    ▼
Result returned to caller
```

## Running It

```bash
# 1. Start Redis
redis-server

# 2. Set LLM API keys
export OPENAI_API_KEY="sk-..."

# 3. Run
python app.py
```

## Next Steps

- **[Customer Service System](customer-service)** — Multi-agent with human review
- **[Data Processing Pipeline](data-pipeline)** — Programmatic agents
- **[Quick Start](../getting-started/quickstart)** — Full tutorial

---

*LeafMesh — Minimal two-agent example*
