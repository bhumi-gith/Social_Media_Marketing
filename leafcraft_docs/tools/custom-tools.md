# Custom Tools

Register custom Python functions as tools using the `@global_tool` decorator with OpenAI-compatible parameter schemas.

## Registration

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
    """Your implementation here"""
    return {"tier": "enterprise", "status": "active", "account_id": account_id}
```

## Using Custom Tools

Once registered, include the tool name in any agent's `tools` array:

```yaml
agents:
  support_agent:
    name: "support_agent"
    model: "gpt-4o"
    tools: ["lookup_account", "current_time"]
    prompt: |
      Look up customer accounts when needed.
```

## Examples

### Database Query

```python
@global_tool(
    name="query_database",
    description="Execute a read-only SQL query",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "SQL SELECT query"}
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

### HTTP API Call

```python
@global_tool(
    name="fetch_weather",
    description="Get current weather for a location",
    parameters={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"}
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

### Statistics

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
                "description": "Numeric values to analyze"
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
    return {"count": n, "mean": round(mean, 4), "std_dev": round(variance ** 0.5, 4)}
```

## Parameter Schema

The `parameters` field uses OpenAI-compatible JSON Schema:

```python
parameters={
    "type": "object",
    "properties": {
        "param_name": {
            "type": "string|number|boolean|array|object",
            "description": "What this parameter does"
        }
    },
    "required": ["param_name"]
}
```

## Tool Categories

Categories let you organize tools by domain and grant agents access to entire groups at once, instead of listing every tool individually.

### Built-in Categories

LeafMesh organizes its built-in tools into these categories:

| Category | Tools |
|----------|-------|
| `math` | `calculator`, `random_number` |
| `time` | `current_time`, `time_difference` |
| `text` | `text_analyzer`, `text_formatter` |
| `data` | `json_formatter`, `data_converter` |
| `web` | `web_request` |
| `reasoning` | `chain_of_thought`, `metacognitive_reflection` |
| `integration` | `zapier_action`, `mcp_call`, `composio_action`, `n8n_workflow` |
| `memory` | `recall_memory` |
| `system` | `system_info` |

### Assigning Categories to Agents

Use `tool_categories` in YAML to give an agent access to all tools in one or more categories:

```yaml
agents:
  data_agent:
    name: "data_agent"
    model: "gpt-4o"
    tool_categories: ["math", "data"]   # Access to all math + data tools
    prompt: |
      You are a data processing agent.
```

This is equivalent to writing `tools: ["calculator", "random_number", "json_formatter", "data_converter"]` but easier to maintain. You can combine both approaches -- tools listed in `tools` and tools from `tool_categories` are merged together:

```yaml
agents:
  analyst:
    name: "analyst"
    model: "gpt-4o"
    tools: ["web_request"]              # Specific tool
    tool_categories: ["math", "text"]   # Entire categories
    prompt: |
      You are an analyst with web access, math, and text tools.
```

### Defining Custom Categories

When you register a custom tool with `@global_tool`, set the `category` parameter to place it in a category. If the category does not exist, it is created automatically:

```python
from leafmesh import global_tool

@global_tool(
    name="query_orders",
    description="Query recent orders from the database",
    category="ecommerce",              # Custom category
    parameters={
        "type": "object",
        "properties": {
            "customer_id": {"type": "string", "description": "Customer ID"}
        },
        "required": ["customer_id"]
    }
)
async def query_orders(customer_id: str) -> dict:
    # Your implementation
    return {"orders": []}

@global_tool(
    name="check_inventory",
    description="Check product inventory levels",
    category="ecommerce",              # Same category
    parameters={
        "type": "object",
        "properties": {
            "product_id": {"type": "string", "description": "Product ID"}
        },
        "required": ["product_id"]
    }
)
async def check_inventory(product_id: str) -> dict:
    return {"in_stock": True, "quantity": 42}
```

Now any agent with `tool_categories: ["ecommerce"]` gets access to both `query_orders` and `check_inventory`:

```yaml
agents:
  shop_assistant:
    name: "shop_assistant"
    model: "gpt-4o"
    tool_categories: ["ecommerce"]
    prompt: |
      You are a shop assistant. Help customers with orders and inventory.
```

## Parallel Tool Execution

By default, when an LLM generates multiple tool calls in a single response, LeafMesh executes them concurrently. This significantly speeds up agents that need to gather data from multiple sources at once.

```yaml
agents:
  fast_agent:
    name: "fast_agent"
    model: "gpt-4o"
    tools: ["web_request", "query_database", "calculator"]
    allow_parallel_tool_calls: true    # Default: true
```

To force sequential execution (e.g., when one tool depends on another's result):

```yaml
agents:
  sequential_agent:
    name: "sequential_agent"
    model: "gpt-4o"
    tools: ["web_request", "query_database"]
    allow_parallel_tool_calls: false   # Tools run one at a time
```

When parallel execution is enabled, up to 3 tools run concurrently per batch.

## Tool Execution Limits

Prevent runaway tool loops with `max_tool_calls_per_message`. When the limit is reached, the LLM receives the accumulated tool results and must produce a final text response without further tool calls.

```yaml
agents:
  # Conservative: stop after 2 tool calls
  careful_agent:
    name: "careful_agent"
    model: "gpt-4o"
    tools: ["web_request", "calculator"]
    max_tool_calls_per_message: 2

  # Generous: allow up to 15 tool calls
  research_agent:
    name: "research_agent"
    model: "gpt-4o"
    tools: ["web_request", "query_database", "calculator"]
    max_tool_calls_per_message: 15
```

| Setting | Default | Range | Description |
|---------|---------|-------|-------------|
| `max_tool_calls_per_message` | 5 | 0-20 | Maximum tool call rounds per message |
| `tool_call_timeout` | 30.0 | Any positive float | Timeout per individual tool execution (seconds) |

Setting `max_tool_calls_per_message: 0` effectively disables tool calling for that agent, even if tools are listed.

## Tool Choice Modes

Control how the LLM uses its available tools with the `tool_choice` setting:

```yaml
agents:
  # LLM decides whether and which tools to call (default)
  auto_agent:
    name: "auto_agent"
    tools: ["calculator", "web_request"]
    tool_choice: "auto"

  # LLM must call at least one tool every turn
  always_tool_agent:
    name: "always_tool_agent"
    tools: ["query_database"]
    tool_choice: "required"

  # Force calls to a specific tool by name
  forced_agent:
    name: "forced_agent"
    tools: ["calculator", "web_request"]
    tool_choice: "calculator"

  # Disable tool calling — agent responds with text only
  text_only_agent:
    name: "text_only_agent"
    tools: ["calculator"]
    tool_choice: "none"
```

| Mode | Behavior |
|------|----------|
| `"auto"` | LLM decides when to use tools (default) |
| `"required"` | LLM must use at least one tool per turn |
| `"none"` | Tool calling disabled, even if tools are listed |
| `"<tool_name>"` | Force the LLM to call a specific tool |

## Complete Configuration Example

An agent combining all tool configuration options:

```yaml
agents:
  full_featured_agent:
    name: "full_featured_agent"
    model: "gpt-4o"
    tools: ["web_request"]
    tool_categories: ["math", "data", "ecommerce"]
    tool_choice: "auto"
    max_tool_calls_per_message: 10
    tool_call_timeout: 45.0
    allow_parallel_tool_calls: true
    prompt: |
      You are a versatile agent with access to web, math,
      data processing, and e-commerce tools.
```

## Next Steps

- **[Built-in Tools](builtin-tools)** --- Available built-in tools
- **[Tool Permissions](permissions)** --- Access control
- **[Tools Overview](overview)** --- Complete tool system docs

---

*LeafMesh --- Extend agents with custom capabilities*
