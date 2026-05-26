# Context Engineering

Context engineering in LeafMesh is the practice of assembling the right information in the right format before sending it to the LLM. The framework provides structured mechanisms for this through the pre-compose pipeline and automatic yields propagation.

## How Context Is Assembled

For each LLM agent, LeafMesh assembles the prompt from several sources:

- **Agent prompt** — the `prompt` field from your YAML
- **Yields schema** — automatically appended so the LLM knows exactly what structured output to produce
- **Pre-compose output** — context, input, and others processors (see below)
- **Conversation history** — recent turns from the session, automatically capped to keep prompts within budget
- **Upstream yields** — the calling agent's structured output, passed as `input_data`

You do not assemble messages by hand. The framework handles role assignment (system / user / supplementary), history truncation, and yields schema injection.

## History Management

Conversation history is automatically stored per session and the most recent turns are included in the prompt. Older turns remain in session storage for retrieval but are excluded from new prompts so context-window budgets stay under control.

History records carry role (`user` / `assistant` / `system`), content, timestamp, and the agent that produced each message — visible in the Studio Sessions tab.

## Pre-Compose Context Assembly

Pre-compose processors run before the LLM sees any data. Each maps to a distinct role in the prompt:

| Processor | Role | Purpose |
|-----------|------|---------|
| `context_processor` | System context | Business data, account info, external state |
| `input_processor` | User message | Cleaned, validated user input |
| `others_processor` | Supplementary | Attachments, metadata, additional data |

This separation keeps context organized and prevents information from being mixed into the wrong role.

## Yields Schema Injection

The framework automatically injects the agent's yields schema into the system context, telling the LLM exactly what format to produce:

```yaml
agents:
  classifier:
    prompt: "Classify the incoming request."
    yields:
      category: "string"
      urgency: "number"
      summary: "string"
```

The LLM sees the yields schema as part of its instructions, guiding it to produce structured output that matches the declared format.

## Context from Upstream Agents

When an agent is called via `can_call`, the upstream agent's yields are passed as `input_data`:

```python
async def specialist(llm_response, input_data, context):
    # input_data contains the upstream agent's yields
    upstream_category = input_data.get("category")
    upstream_urgency = input_data.get("urgency")
    return llm_response
```

Downstream agents automatically receive the structured output from upstream agents without manual data passing.

## Context Strategies

| Strategy | When to Use |
|----------|-------------|
| Pre-compose context_processor | External data that the LLM needs as background |
| Pre-compose input_processor | When raw input needs cleaning or extraction |
| Intelligence function + session state | When you need to read/write state during execution |
| Tool calling | When the LLM needs to decide what data to fetch |
| Upstream yields | When agents form a processing chain |

## Next Steps

- **[Message Formatting](../messages/formatting)** — How messages are constructed
- **[Middleware Overview](../middleware/overview)** — Pre-compose pipeline
- **[State Management](../memory/state-management)** — Session state patterns

---

*LeafMesh — Structured context assembly*
