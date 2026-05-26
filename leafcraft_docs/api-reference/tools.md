# Tool System API

API reference for the tool system in LeafMesh.

## Registering Custom Tools

### `@global_tool` Decorator

The way to register a custom tool that agents can use:

```python
from leafmesh.tools import global_tool

@global_tool(
    name="lookup_account",
    description="Look up account details by ID",
    category="database"
)
async def lookup_account(account_id: str) -> dict:
    return {"tier": "enterprise", "status": "active"}
```

The function remains callable as normal Python and is automatically available to any agent that lists it in their YAML `tools` array.

### Decorator Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `name` | str | Tool name (used in YAML `tools` array) |
| `description` | str | Description shown to the LLM for tool selection |
| `category` | str | Tool category for `tool_categories` YAML config |

## Built-in Tools (12 tools)

| Tool | Category | Description |
|------|----------|-------------|
| `calculator` | math | Safe AST-based math evaluation |
| `random_number` | math | Random number generation (max 1000) |
| `current_time` | time | Current date/time in any timezone |
| `time_difference` | time | Calculate time between timestamps |
| `text_analyzer` | text | Text statistics (words, sentences, etc.) |
| `text_formatter` | text | Format text (uppercase, title, wrap, etc.) |
| `web_request` | web | HTTP requests (GET/POST/PUT/DELETE), SSRF-protected |
| `json_formatter` | data | Format and validate JSON |
| `data_converter` | data | Convert between data formats |
| `chain_of_thought` | reasoning | Step-by-step reasoning framework |
| `metacognitive_reflection` | reasoning | Evaluate reasoning quality |
| `system_info` | system | Platform and system information |

## Agent Tool Configuration

Grant tools to agents in your YAML configuration:

```yaml
agents:
  my_agent:
    tools: ["calculator", "web_request", "lookup_account"]
    tool_choice: "auto"                  # "auto" | "none" | specific tool name
    max_tool_calls_per_message: 5        # Range: 0-20
    tool_call_timeout: 30.0              # Range: 0.1-300 seconds
    allow_parallel_tool_calls: true      # Default: true
    tool_categories: ["math", "web"]     # Grant all tools in a category
```

## Tool Choice Modes

| Mode | Behavior |
|------|----------|
| `"auto"` | LLM decides whether to call tools |
| `"none"` | Tool calling disabled |
| `"tool_name"` | Force a specific tool |

## Permission Enforcement

Tools are only available to agents that declare them in their YAML `tools` array or `tool_categories`. If an LLM generates a call for an unauthorized tool, the call is rejected before any tool code runs.

## Next Steps

- **[Built-in Tools](../tools/builtin-tools)** — Detailed tool reference
- **[Custom Tools](../tools/custom-tools)** — Creating custom tools
- **[Tool Permissions](../tools/permissions)** — Access control

---

*LeafMesh — Tool system API reference*
