# Tools

Tools extend agent capabilities beyond text generation. An agent with `tools: ["calculator"]` in its YAML config can call the calculator during its LLM execution. The LLM decides when and how to use tools based on the user's request.

## How Tools Work

1. Tools listed in an agent's `tools` array are loaded into the agent's available tool set
2. Tool definitions are formatted as OpenAI-compatible function schemas
3. The LLM receives these schemas alongside the prompt
4. When the LLM generates a tool call, LeafMesh runs it
5. Tool results are fed back to the LLM for a follow-up response
6. This loop continues until the LLM responds without tool calls, or `max_tool_calls_per_message` is reached

```yaml
agents:
  research_agent:
    name: "research_agent"
    model: "gpt-4o"
    tools: ["web_request", "text_analyzer", "calculator"]
    tool_choice: "auto"            # LLM decides when to use tools
    max_tool_calls_per_message: 5  # Prevent runaway tool loops (default: 5, range 0-20)
```

## Built-in Tools

LeafMesh includes these built-in tools:

| Tool | Description |
|------|-------------|
| `calculator` | Basic arithmetic and math operations |
| `random_number` | Random number generation |
| `current_time` | Current date, time, timezone |
| `time_difference` | Calculate time differences and durations |
| `text_analyzer` | Text analysis (word count, readability, etc.) |
| `text_formatter` | Text formatting and transformation |
| `json_formatter` | JSON parsing, formatting, validation |
| `web_request` | Full HTTP client (GET, POST, etc.) |
| `data_converter` | Convert between data formats |
| `chain_of_thought` | Structured reasoning chains |
| `metacognitive_reflection` | Self-assessment and reasoning quality |
| `system_info` | System information and resource monitoring |

### Assigning Built-in Tools

```yaml
agents:
  data_agent:
    name: "data_agent"
    model: "gpt-4o-mini"
    tools:
      - "calculator"
      - "current_time"
      - "json_formatter"
    prompt: |
      You are a data processing agent.
      Use the calculator for numeric operations.
      Use current_time when timestamps are needed.
```

## Custom Tools

Register custom tools using the `@global_tool` decorator with OpenAI-compatible parameter schemas:

```python
from leafmesh import global_tool

@global_tool(
    name="lookup_account",
    description="Look up account details by account ID",
    parameters={
        "type": "object",
        "properties": {
            "account_id": {
                "type": "string",
                "description": "The account ID to look up"
            }
        },
        "required": ["account_id"]
    }
)
async def lookup_account(account_id: str) -> dict:
    """Look up account details from the database"""
    # Replace with your actual implementation
    return {"tier": "enterprise", "status": "active", "account_id": account_id}
```

Once registered, any agent that includes `"lookup_account"` in its `tools` array can use it:

```yaml
agents:
  support_agent:
    name: "support_agent"
    model: "gpt-4o"
    tools: ["lookup_account", "current_time"]
    prompt: |
      You are a support agent. Look up customer accounts
      when needed to provide personalized assistance.
```

### Custom Tool Examples

**Database query tool:**

```python
@global_tool(
    name="query_database",
    description="Execute a read-only SQL query",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "SQL SELECT query to execute"
            }
        },
        "required": ["query"]
    }
)
async def query_database(query: str) -> dict:
    import aiosqlite
    async with aiosqlite.connect("app.db") as db:
        cursor = await db.execute(query)
        rows = await cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return {"columns": columns, "rows": rows, "count": len(rows)}
```

**HTTP API tool:**

```python
@global_tool(
    name="fetch_weather",
    description="Get current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name (e.g., 'San Francisco')"
            }
        },
        "required": ["city"]
    }
)
async def fetch_weather(city: str) -> dict:
    import aiohttp
    url = f"https://api.weather.example.com/current?city={city}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()
```

**Computation tool:**

```python
@global_tool(
    name="statistics",
    description="Calculate statistics for a list of numbers",
    parameters={
        "type": "object",
        "properties": {
            "values": {
                "type": "array",
                "items": {"type": "number"},
                "description": "List of numeric values to analyze"
            }
        },
        "required": ["values"]
    }
)
async def statistics(values: list) -> dict:
    n = len(values)
    if n == 0:
        return {"error": "Empty list"}

    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    std_dev = variance ** 0.5

    return {
        "count": n,
        "mean": round(mean, 4),
        "std_dev": round(std_dev, 4),
        "min": min(values),
        "max": max(values)
    }
```

## Tool Choice Modes

Control how the LLM uses tools:

```yaml
agents:
  # LLM decides whether and which tools to call
  auto_agent:
    tools: ["calculator", "web_request"]
    tool_choice: "auto"

  # LLM must call at least one tool
  required_agent:
    tools: ["calculator"]
    tool_choice: "required"

  # Force the LLM to use a specific tool
  forced_agent:
    tools: ["calculator", "web_request"]
    tool_choice:
      type: "function"
      function:
        name: "calculator"

  # Disable tool calling even if tools are listed
  no_tools_agent:
    tools: ["calculator"]
    tool_choice: "none"
```

## Permission-Based Tool Access

Tools are granted per-agent through the YAML `tools` array. An agent without `tools: ["web_request"]` **cannot** make web requests, regardless of what the LLM attempts.

```yaml
agents:
  # This agent can only use calculator and current_time
  restricted_agent:
    name: "restricted_agent"
    model: "gpt-4o-mini"
    tools: ["calculator", "current_time"]

  # This agent has full access to external services
  privileged_agent:
    name: "privileged_agent"
    model: "gpt-4o"
    tools: ["calculator", "web_request", "query_database"]
```

If the LLM generates a tool call for a tool the agent does not have permission to use, the call is **rejected before any tool code runs**.

## Tool Execution Limits

Prevent runaway tool loops with `max_tool_calls_per_message`:

```yaml
agents:
  careful_agent:
    name: "careful_agent"
    model: "gpt-4o"
    tools: ["web_request", "calculator"]
    max_tool_calls_per_message: 3  # Stop after 3 tool calls (default: 5, range 0-20)
```

LeafMesh tracks tool-call depth per agent execution. When the limit is reached, the LLM receives the accumulated tool results and must produce a final response without further tool calls.

## Using Tools with Agents in YAML

A complete example with a collector agent that uses custom tools:

```yaml
agents:
  collector:
    name: "collector"
    agent_type: "programmatic"
    tools: ["query_database", "fetch_weather"]
    wake_up: "*/5 * * * *"
    yields:
      data: "object"
      source: "string"
      timestamp: "string"
    can_call:
      - agent: "analyzer"
        condition: "data != {}"
```

```python
from leafmesh import global_tool

@global_tool(
    name="query_database",
    description="Query the monitoring database",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "SQL query"}
        },
        "required": ["query"]
    }
)
async def query_database(query: str) -> dict:
    # Your database query implementation
    return {"rows": [], "count": 0}

async def collector(llm_response, input_data, context):
    from datetime import datetime
    # For programmatic agents, use tools directly in the intelligence function
    return {
        "data": {"readings": [1, 2, 3]},
        "source": "database",
        "timestamp": datetime.now().isoformat()
    }
```

## Ground Truth Anchoring

Tools provide a critical mechanism for reducing hallucination. An agent that calls a database query tool or an API endpoint retrieves **actual data** rather than generating plausible-sounding data from parametric memory.

The combination of:
- **Typed yields** (structural anchoring — response must match the declared schema)
- **Pre-compose context** (deterministic context — Python code assembles the business context)
- **Tool calling** (external data — real data from databases and APIs)

...creates multiple layers of ground truth enforcement. None is sufficient alone, but together they significantly reduce the surface area for hallucination.

## Next Steps

- **[Agent Configuration](../api-reference/agent-config)** — Full YAML reference including `tools`, `tool_choice`, `max_tool_calls_per_message`
- **[LLM Agents](../agents/llm-agents)** — How tools integrate with the agent pipeline
- **[Architecture Guide](../core-concepts/architecture)** — Tool execution in context

---

*LeafMesh — Extend agents with real-world capabilities*
