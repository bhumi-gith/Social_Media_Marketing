# Built-in Tools

LeafMesh includes 17 built-in tools across 6 categories. All are automatically registered when LeafMesh loads.

## Math Tools

### `calculator`

Safe mathematical expression evaluation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `expression` | string | Math expression (max 500 chars) |

Supports: `+`, `-`, `*`, `/`, `//`, `%`, unary operators.

### `random_number`

Generate random integers.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `min_val` | integer | 1 | Minimum value |
| `max_val` | integer | 100 | Maximum value |
| `count` | integer | 1 | How many (max 1000) |

## Time Tools

### `current_time`

Get current date and time.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `timezone` | string | "UTC" | Timezone name |
| `time_format` | string | "iso" | "iso", "human", "timestamp", or strftime |

### `time_difference`

Calculate time between two ISO timestamps.

| Parameter | Type | Description |
|-----------|------|-------------|
| `start_time` | string | ISO format start |
| `end_time` | string | ISO format end |
| `unit` | string | "seconds", "minutes", "hours", "days" |

## Text Tools

### `text_analyzer`

Analyze text properties: character count, word count, sentence count, etc.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `text` | string | — | Text to analyze |
| `analysis_type` | string | "all" | "basic", "detailed", or "all" |

### `text_formatter`

Format text: uppercase, lowercase, title, reverse, capitalize, remove_spaces, add_prefix, add_suffix, wrap_lines.

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to format |
| `format_type` | string | Formatting operation |
| `options` | object | Additional options |

## Web Tools

### `web_request`

HTTP requests (GET, POST, PUT, DELETE). **Requires confirmation.** SSRF-protected.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | — | Target URL |
| `method` | string | "GET" | HTTP method |
| `headers` | object | {} | Request headers |
| `data` | object | {} | Request body |
| `timeout` | number | 10 | Timeout seconds |

## Data Tools

### `json_formatter`

Format and validate JSON: "pretty", "compact", "validate".

### `data_converter`

Convert between formats (json ↔ text).

## Reasoning Tools

### `chain_of_thought`

Step-by-step reasoning through problems. Styles: analytical, creative, logical, intuitive, systematic, exploratory.

### `metacognitive_reflection`

Evaluate reasoning quality: strengths, weaknesses, bias check, improvement suggestions.

## System Tools

### `system_info`

Platform info, Python version, current time, working directory.

## Assigning Tools to Agents

```yaml
agents:
  research_agent:
    tools: ["web_request", "calculator", "current_time"]
    tool_choice: "auto"
    max_tool_calls_per_message: 5
    allow_parallel_tool_calls: true
```

## Tool Execution Flow

1. Tool schemas sent to LLM alongside the prompt
2. LLM decides when to call tools (with `tool_choice: "auto"`)
3. LeafMesh validates permissions and runs the tool
4. Results returned to LLM for follow-up response
5. Loop continues until no more tool calls or `max_tool_calls_per_message` reached

## Next Steps

- **[Custom Tools](custom-tools)** — Register your own tools
- **[Tool Permissions](permissions)** — Access control details
- **[Tool System API](../api-reference/tools)** — API reference

---

*LeafMesh — 17 built-in tools*
