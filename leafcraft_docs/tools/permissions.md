# Tool Permissions

Tool access in LeafMesh is permission-based and declared per-agent through YAML configuration.

## How Permissions Work

Each agent lists the tools it can use in its `tools` array. An agent **cannot** use tools not in its list, regardless of what the LLM attempts:

```yaml
agents:
  # Can only use calculator and current_time
  restricted_agent:
    name: "restricted_agent"
    model: "gpt-4o-mini"
    tools: ["calculator", "current_time"]

  # Has full access to external services
  privileged_agent:
    name: "privileged_agent"
    model: "gpt-4o"
    tools: ["calculator", "web_request", "query_database"]
```

## Enforcement

If the LLM generates a tool call for a tool the agent does not have permission to use, the call is **rejected before any tool code runs**. The LLM receives an error and must produce a response without that tool.

## Tool Choice Modes

Control how the LLM uses its permitted tools:

```yaml
# LLM decides whether to call tools (default)
tool_choice: "auto"

# LLM must call at least one tool
tool_choice: "required"

# Force a specific tool
tool_choice:
  type: "function"
  function:
    name: "calculator"

# Disable tool calling even if tools are listed
tool_choice: "none"
```

## Execution Limits

Prevent runaway tool loops with `max_tool_calls_per_message`:

```yaml
agents:
  careful_agent:
    tools: ["web_request", "calculator"]
    max_tool_calls_per_message: 3  # Stop after 3 tool calls (default: 5, range 0-20)
```

LeafMesh tracks tool-call depth per execution. When the limit is reached, the LLM must produce a final response without further tool calls.

## Security Implications

- Tools are granted **per-agent**, not globally
- An agent without `tools: ["web_request"]` cannot make HTTP requests
- Agents can only access tools explicitly listed in their `tools` array
- `max_tool_calls_per_message` prevents infinite tool loops

## Next Steps

- **[Built-in Tools](builtin-tools)** — Available tools
- **[Custom Tools](custom-tools)** — Register your own
- **[Tools Overview](overview)** — Full tool system docs

---

*LeafMesh — Permission-based tool access*
