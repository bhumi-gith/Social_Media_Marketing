# Agent Types

LeafMesh supports four agent types. All four participate in the mesh identically — they have yields, can_call rules, and condition evaluation. The difference is how they produce their response.

| Type | How It Responds | Use Case |
|------|----------------|----------|
| **LLM Agent** | Calls an LLM provider | Natural language processing, analysis, generation |
| **Programmatic Agent** | Runs Python only, no LLM | Deterministic logic, calculations, API calls |
| **Human Agent** | Waits for a human response via webhook | Approvals, quality review, escalations |
| **Scheduled Agent** | Triggered by `wake_up` cron expression | Periodic data collection, health checks, reports |

## LLM Agents

The default agent type. Sends a prompt to an LLM, parses the response against the `yields` schema, and evaluates `can_call` conditions.

```yaml
agents:
  solver:
    name: "solver"
    model: "gpt-4o-mini"
    temperature: 0.1
    max_tokens: 500
    prompt: |
      You are a math solver. Given a math problem, solve it step by step.
      Be precise and show your work.
    yields:
      answer: "number"
      steps: "array"
      confidence: "number"
    can_call:
      - agent: "checker"
        condition: "answer >= 0"
        call_immediately: true
```

**Execution pipeline:**

1. The prompt is assembled (system prompt + yields schema + conversation history + user input)
2. The provider is called (`gpt-4o-mini`)
3. Response is parsed against the `yields` schema
4. If an intelligence function is registered (function name matches agent name), it processes the response
5. `can_call` conditions are evaluated against the yields
6. Matching downstream agents are called via the mesh

### Adding Intelligence

Enhance the LLM response with deterministic Python logic:

```python
# Function name "solver" matches the YAML agent name — auto_discover finds it
async def solver(llm_response, input_data, context):
    """Deterministic math solving — LLM is only the fallback"""
    import re
    problem = input_data.get("problem", "")
    numbers = re.findall(r'-?\d+\.?\d*', problem)

    if len(numbers) == 2:
        a, b = float(numbers[0]), float(numbers[1])
        if "+" in problem:
            return {"answer": a + b, "steps": [f"{a} + {b}"], "confidence": 1.0}
        elif "-" in problem:
            return {"answer": a - b, "steps": [f"{a} - {b}"], "confidence": 1.0}

    # Fall back to LLM for complex expressions
    return llm_response
```

The intelligence function runs **after** the LLM call. It receives the raw LLM response and can modify, enrich, or replace it entirely.

## Programmatic Agents

Pure Python agents that skip the LLM call entirely. Set `agent_type: "programmatic"` in YAML.

```yaml
agents:
  collector:
    name: "collector"
    agent_type: "programmatic"
    wake_up: "*/5 * * * *"          # Every 5 minutes
    yields:
      readings: "array"
      timestamp: "string"
      source: "string"
    can_call:
      - agent: "analyzer"
        condition: "readings != []"
```

The intelligence function **is** the agent — there is no LLM call:

```python
# Function name "collector" matches the YAML agent name — auto_discover finds it
async def collector(llm_response, input_data, context):
    """Collect data from your source — no LLM involved"""
    import random
    from datetime import datetime

    # Replace with real data: API call, DB query, sensor, etc.
    readings = [random.gauss(100, 10) for _ in range(20)]

    return {
        "readings": [round(r, 2) for r in readings],
        "timestamp": datetime.now().isoformat(),
        "source": "sensor_1"
    }
```

For programmatic agents, `llm_response` is an empty dict. The intelligence function produces the entire output.

**When to use programmatic agents:**
- Data collection from APIs, databases, or sensors
- Deterministic calculations (no need for an LLM)
- System integration tasks (file operations, HTTP calls)
- Cost-sensitive operations where an LLM call is wasteful

## Human Agents

Human-in-the-loop agents that delegate to a real person via webhook or custom handler. The mesh treats human responses identically to LLM responses for routing purposes.

```yaml
agents:
  human_reviewer:
    name: "human_reviewer"
    agent_type: "human"
    is_human_powered: true
    human_interface: "api"
    human_timeout_seconds: 300        # 5 minutes to respond
    yields:
      approval: "string"
      feedback: "string"
    can_call:
      - agent: "final_processor"
        condition: "approval == 'approved'"
```

### With Webhook

```yaml
agents:
  approver:
    name: "approver"
    agent_type: "human"
    is_human_powered: true
    human_timeout_seconds: 1800       # 30 minutes
    webhook_config:
      outbound_url: "https://internal.example.com/approve"
      method: "POST"
    communication_type: "dual"
    yields:
      decision: "string"
      notes: "string"
    can_call:
      - agent: "execute_action"
        condition: "decision == 'approved'"
```

When triggered, the agent:

1. Sends a webhook POST to `outbound_url` with the context and prompt
2. Waits for the human to respond (up to `human_timeout_seconds`)
3. Parses the response against the `yields` schema
4. Evaluates `can_call` conditions — same as any other agent

If the human does not respond within the timeout, a `HUMAN_INPUT_TIMEOUT` event is published. The Manager can trigger fallback actions: retry, route to a fallback LLM agent, escalate to a different reviewer, or stop the chain.

### HILT Event Lifecycle

The following events are published during human agent execution:

| Event | When |
|-------|------|
| `HUMAN_INPUT_REQUESTED` | Webhook or handler is invoked |
| `HUMAN_INPUT_RECEIVED` | Human provides a response |
| `HUMAN_INPUT_TIMEOUT` | Human does not respond in time |
| `HUMAN_AGENT_CONNECTED` | Human operator connects |
| `HUMAN_AGENT_DISCONNECTED` | Human operator disconnects |
| `WORKFLOW_PAUSED` | Workflow paused for human input |
| `WORKFLOW_RESUMED` | Workflow resumed after human responds |
| `HUMAN_HANDOFF` | Handing off to human agent |
| `HUMAN_ESCALATION` | Escalating to human intervention |
| `HUMAN_INTERVENTION_REQUIRED` | Human intervention needed |

The Manager subscribes to all HILT events and coordinates timeouts and fallbacks automatically.

**When to use human agents:**
- Approval workflows (refunds, deployments, access requests)
- Quality review for high-stakes outputs
- Escalation endpoints for angry customers or critical incidents
- Compliance checkpoints that require human judgment

## Scheduled Agents

Any agent type can be scheduled using `wake_up`. LeafMesh triggers the agent on a cron, interval, or keyword schedule.

```yaml
agents:
  # Every 5 minutes
  frequent_collector:
    name: "frequent_collector"
    agent_type: "programmatic"
    wake_up: "*/5 * * * *"

  # Every hour at minute 0
  hourly_reporter:
    name: "hourly_reporter"
    model: "gpt-4o-mini"
    wake_up: "0 * * * *"

  # Every day at midnight
  daily_digest:
    name: "daily_digest"
    model: "gpt-4o"
    wake_up: "0 0 * * *"

  # Every Monday at 9 AM
  weekly_summary:
    name: "weekly_summary"
    model: "gpt-4o"
    wake_up: "0 9 * * 1"
```

### Schedule Expression Formats

| Format | Example | Meaning |
|--------|---------|---------|
| Cron (5-field) | `*/5 * * * *` | Every 5 minutes |
| Interval | `every 30 seconds` | Every 30 seconds |
| Keyword | `hourly` | Top of every hour |
| Keyword | `daily` | Midnight |
| Keyword | `weekly` | Sunday midnight |

When `wake_up` fires, LeafMesh invokes the agent with empty `input_data`. The agent's intelligence function runs, produces yields, and `can_call` rules route the output downstream. The execution follows the same full pipeline as interactive calls — pre-compose, LLM call, validation, can_call evaluation.

### Runtime Schedule Management

```python
# Schedule an agent dynamically
leafmesh.schedule_agent("collector", "every 60 seconds")

# Unschedule an agent
leafmesh.unschedule_agent("collector")
```

**Common scheduling patterns:**
- Periodic data ingestion: collect, process, route to downstream agents
- Health reporting: collect metrics, summarize, notify humans
- Cache maintenance: check hit rates, invalidate stale entries
- Compliance: generate audit reports from Redis Streams data

## Agent Communication

All agents communicate through the control plane. Agents never call each other directly.

### Declarative Routing (can_call)

```yaml
agents:
  triage:
    name: "triage"
    model: "gpt-4o-mini"
    yields:
      urgency: "number"
      category: "string"
    can_call:
      - agent: "specialist"
        condition: "urgency >= 7"
        call_immediately: true
      - agent: "standard_handler"
        condition: "urgency < 7"
```

Conditions are evaluated using the AST-safe evaluator (Python `ast` module, never `eval()`). Supported operations:

- Comparisons: `==`, `!=`, `<`, `<=`, `>`, `>=`
- Boolean: `and`, `or`, `not` (also `&&`, `||`)
- Arithmetic: `+`, `-`, `*`, `/`, `%`
- String equality: `category == 'billing'`
- Nested access: `calling_agent_response.score >= 0.7`

### Direct Mesh Calls

From an intelligence function, you can call another agent directly:

```python
# Function name "coordinator" matches the YAML agent name — auto_discover finds it
async def coordinator(llm_response, input_data, context):
    # Direct mesh call to another agent
    check_result = await leafmesh.mesh_call(
        from_agent="coordinator",
        to_agent="verifier",
        data={"claim": llm_response.get("claim")},
        session_id=context.get("session_id", "default")
    )

    return {
        "claim": llm_response.get("claim"),
        "verified": check_result.get("is_valid", False)
    }
```

### Dual Response Pattern

For agents that need to respond immediately while triggering background work:

```yaml
agents:
  user_agent:
    name: "user_agent"
    model: "gpt-4o-mini"
    communication_type: "dual"     # Return response + async can_call
    yields:
      response: "string"
      log_event: "boolean"
    can_call:
      - agent: "logger"
        condition: "log_event == true"
```

With `communication_type: "dual"`, LeafMesh returns the agent's response to the caller immediately, then dispatches `can_call` chains as background tasks via `asyncio.ensure_future()`.

## Pre-Compose Pipeline

Run deterministic Python **before** the LLM call to control what the LLM sees:

```python
from leafmesh import pre_compose

async def enrich_context(input_data, context):
    """Enrich input before the LLM sees the request"""
    source = input_data.get("source", "unknown")
    # Use data from input_data (passed from upstream agents or the initial call)
    history = input_data.get("historical_data", [])
    return {"historical_data": history, "source": source, **input_data}

async def clean_input(input_data, context):
    """Sanitize input before the LLM processes it"""
    readings = input_data.get("readings", [])
    cleaned = [r for r in readings if r is not None and -1000 < r < 10000]
    return {**input_data, "readings": cleaned}

@pre_compose(
    context_processor=enrich_context,
    input_processor=clean_input
)
# Function name "analyzer" matches the YAML agent name — auto_discover finds it
async def analyzer(llm_response, input_data, context):
    # input_data now has historical_data and cleaned readings
    return llm_response
```

**Execution order:**
1. `context_processor` runs first — assembles business context
2. `input_processor` runs second — cleans and sanitizes user input
3. `others_processor` (optional) — handles supplementary data
4. The prompt is assembled using the prepared data
5. LLM call executes
6. Intelligence function receives the LLM response

Pre-compose controls what the LLM **sees**. The intelligence function controls what downstream agents **receive**. Both are deterministic Python.

## File Organization

For systems with more than 3 agents, organize into separate files:

```
my_system/
├── config.yaml
├── main.py
├── agency/
│   ├── __init__.py
│   ├── agency_client.py      # LeafMesh init + agent registration
│   ├── solver_agent.py       # Solver intelligence
│   ├── checker_agent.py      # Checker intelligence
│   └── tools/
│       └── database.py       # Custom tool definitions
```

```python
# agency/solver_agent.py
# Function name "solver" matches the YAML agent name — auto_discover finds it
async def solver(llm_response, input_data, context):
    # ... solver implementation
    return result
```

```python
# agency/agency_client.py
from leafmesh import LeafMesh

async def initialize(config_path: str):
    leafmesh = LeafMesh.from_yaml(config_path)
    await leafmesh.start()
    # auto_discover in YAML config handles agent registration
    # Set auto_discover: true and agents_dir in your config.yaml
    return leafmesh
```

## Next Steps

- **[LLM Agents](llm-agents)** — Deep dive into prompts, tools, and model configuration
- **[Quick Start](../getting-started/quickstart)** — Build your first agent in 5 minutes
- **[Math Pipeline Example](../examples/yield-monitoring)** — Full multi-agent pipeline walkthrough
- **[Agent Configuration Reference](../api-reference/agent-config)** — Complete YAML schema

---

*LeafMesh — Four agent types, one consistent mesh interface*
