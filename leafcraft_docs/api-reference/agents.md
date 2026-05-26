# Agent Classes

API reference for the agent types in LeafMesh.

## LLM Agent

The default agent type. Sends requests to an LLM provider and produces structured output.

### Configuration

```yaml
agents:
  my_agent:
    name: "my_agent"                    # Required
    model: "gpt-4o"                     # LLM model
    prompt: "Your instructions here"    # Required for LLM agents
    temperature: 0.1                    # Default: 0.1
    max_tokens: 2000                    # Max response tokens
    yields:                             # Expected output schema
      field: "type"
    can_call:                           # Routing rules
      - agent: "target"
        condition: "field == 'value'"
        call_immediately: false
    tools: ["calculator"]               # Granted tools
    tool_choice: "auto"                 # auto | required | none
    max_tool_calls_per_message: 5        # Default: 5, range 0-20
    communication_type: "dual"          # dual | chain | execute
    optimization_strategy: "performance" # Adaptive executor strategy
```

### Execution Pipeline

```
Pre-compose → Prompt assembly → LLM Call → Tool Loop → Yields Parse → Conditions → Intelligence → Mesh
```

## Programmatic Agent

Pure Python execution without LLM calls. Set `agent_type: "programmatic"`.

### Configuration

```yaml
agents:
  validator:
    name: "validator"
    agent_type: "programmatic"
    yields:
      is_valid: "boolean"
      errors: "string"
    can_call:
      - agent: "next_step"
        condition: "is_valid == true"
```

### Implementation

```python
async def validator(llm_response, input_data, context):
    # input_data contains upstream yields
    # Perform pure Python validation
    errors = []
    if not input_data.get("email"):
        errors.append("Email required")
    return {
        "is_valid": len(errors) == 0,
        "errors": ", ".join(errors) if errors else "none"
    }
```

## Human Agent

Routes execution to a human reviewer. Set `agent_type: "human"`.

### Configuration

```yaml
agents:
  reviewer:
    name: "reviewer"
    agent_type: "human"
    timeout: 300                        # Seconds (default: 300)
    webhook_config:
      url: "https://example.com/review"
      method: "POST"
    yields:
      approved: "boolean"
      notes: "string"
    can_call:
      - agent: "executor"
        condition: "approved == true"
```

### Custom Handler

```python
# Alternative to webhook: custom Python handler
async def custom_handler(context, session_id, timeout):
    # Implement custom review logic
    # (Slack, email, in-app, etc.)
    return {"approved": True, "notes": "Looks good"}
```

### Human-in-the-Loop Events

These events are emitted automatically and visible in **Studio's Activity tab**:

| Event | When |
|-------|------|
| `human.input.requested` | Webhook/handler invoked |
| `human.input.received` | Human responds |
| `human.input.timeout` | Timeout exceeded |
| `workflow.paused` | Workflow paused for human input |
| `workflow.resumed` | Workflow resumed after human responds |

## Scheduled Agent

Any agent with `wake_up` becomes scheduled. Uses APScheduler.

### Configuration

```yaml
agents:
  monitor:
    name: "monitor"
    wake_up: "0 9 * * *"              # Cron: daily at 9 AM
    # wake_up: "every 30 seconds"     # Interval
    # wake_up: "hourly"               # Keyword
```

### Schedule Formats

| Format | Example | Description |
|--------|---------|-------------|
| Cron | `"0 9 * * *"` | Five-field cron expression |
| Interval | `"every 30 seconds"` | Repeating interval |
| Keyword | `"daily"` | Predefined schedules |

Keywords: `"daily"` (midnight), `"hourly"` (top of hour), `"weekly"` (Sunday midnight).

### Runtime Management

```python
leafmesh.schedule_agent("monitor", "every 5 minutes")
leafmesh.unschedule_agent("monitor")
```

## External Agent

Integrates with external frameworks (LangChain, CrewAI, etc.). Set `agent_type: "external"`.

### Configuration

```yaml
agents:
  external_agent:
    name: "external_agent"
    agent_type: "external"
    framework: "langchain"
    connector_config:
      endpoint: "https://external.example.com/agent"
      auth_token: "${EXTERNAL_AUTH_TOKEN}"
    yields:
      result: "string"
      status: "string"
    can_call:
      - agent: "processor"
        condition: "status == 'success'"
```

External agents delegate execution to an outside system while still participating in the mesh with yields, can_call, and condition evaluation.

## Listing Agents

List registered agents from Python:

```python
agents = leafmesh.list_agents()
```

Or browse them in **Studio's Agents tab**.

## Next Steps

- **[LeafMesh Class](leafmesh-adk)** — LeafMesh class reference
- **[Configuration API](configuration)** — Full config reference
- **[Agent Development](../agents/development)** — Building agents

---

*LeafMesh — Agent class reference*
