# Guardrails

Guardrails in LeafMesh are validation mechanisms that operate at different layers of the execution pipeline to ensure agent outputs are safe, correct, and within expected boundaries.

## Structural Guardrails: Yields Schema

The yields schema is the primary structural guardrail. Every LLM agent declares its expected output format:

```yaml
agents:
  analyzer:
    yields:
      category: "string"
      confidence: "number"
      is_urgent: "boolean"
```

LeafMesh parses the LLM response against this schema. If the response doesn't match, parsing fails and the agent returns an error rather than propagating malformed data.

## Routing Guardrails: Condition Evaluation

The `can_call` conditions control which agents can be triggered and under what circumstances:

```yaml
can_call:
  - agent: "escalation_handler"
    condition: "confidence < 0.5 and is_urgent == true"
```

Conditions are evaluated through a secure expression evaluator with a strict allow-list of permitted operations. The system never uses `eval()`, preventing code injection through YAML configuration.

### Supported Operators

| Type | Operators |
|------|-----------|
| Comparison | `==`, `!=`, `>`, `<`, `>=`, `<=` |
| Logical | `and`, `or`, `not` |
| Membership | `in`, `not in` |
| String | `.startswith()`, `.endswith()`, `.contains()` |

## Tool Access Guardrails

Tools are granted per-agent through YAML configuration:

```yaml
agents:
  research_agent:
    tools: ["web_request", "text_analyzer"]
    max_tool_calls_per_message: 3
```

- An agent without `tools: ["web_request"]` cannot make web requests
- `max_tool_calls_per_message` prevents runaway tool loops (default: 5, range 0-20)
- Tool calls for unauthorized tools are rejected at the executor level

## Prompt-Level Guardrails: Context Parts

Context parts inject behavioral instructions **directly into the LLM prompt** as separate system messages. Unlike the main `prompt` (which defines the agent's task), context parts shape **how** the agent responds — with empathy, safety boundaries, or sentiment awareness.

```yaml
agents:
  support_agent:
    name: "support_agent"
    model: "gpt-4o"
    prompt: |
      You handle customer support requests. Diagnose the issue
      and provide a clear resolution.

    context_parts:
      care: |
        Always respond with empathy and warmth. Acknowledge the user's
        situation before jumping to solutions. Use encouraging language.
        If the user seems frustrated, prioritize acknowledgment over action.

      sentiment_analysis: |
        Analyze the user's emotional tone before responding.
        If negative sentiment detected, prioritize de-escalation.
        If positive, match their energy.
        Include a 'detected_sentiment' field in your response.

      guardrails: |
        Never share internal system details or agent architecture.
        Do not make promises about timelines or guarantees.
        If the request is outside your domain, clearly redirect.
        Refuse harmful, illegal, or unethical requests.
        Never disclose PII from other customers.

    yields:
      resolution: "string"
      detected_sentiment: "string"
      confidence: "number"
```

### How It Works

The platform injects each context part as a separate system message **after** the main prompt and **before** the yields schema:

```
System messages sent to LLM:
  1. Agent prompt          ← "You handle customer support requests..."
  2. care                  ← "[EMPATHY & TONE] Always respond with empathy..."
  3. sentiment_analysis    ← "[SENTIMENT ANALYSIS] Analyze the user's emotional tone..."
  4. guardrails            ← "[SAFETY GUARDRAILS] Never share internal system details..."
  5. flows                 ← "[FLOW INSTRUCTIONS] When called from entry point: greet warmly..."
  6. Yields schema         ← "Return JSON with: resolution, detected_sentiment..."
  7. Conversation history  ← Previous messages in this session
  8. User input            ← Current request
```

Each reserved key is injected with its canonical bracket label. Custom keys receive an auto-generated label from their name.

### The Four Reserved Parts

| Part | Label | Purpose | When to Use |
|------|-------|---------|-------------|
| `care` | `[EMPATHY & TONE]` | Tone and empathy instructions | Customer-facing agents, support, onboarding |
| `sentiment_analysis` | `[SENTIMENT ANALYSIS]` | Emotion detection guidance | Agents that need to adapt to user mood |
| `guardrails` | `[SAFETY GUARDRAILS]` | Safety boundaries and restrictions | Any agent handling sensitive data or external users |
| `flows` | `[FLOW INSTRUCTIONS]` | Per-caller routing behaviour | Agents called from multiple places in the mesh that need different behaviour per caller |

All four are optional. Use any combination — or define only the ones you need:

```yaml
# Guardrails only — no care or sentiment
context_parts:
  guardrails: "Never disclose pricing. Never compare to competitors."
```

```yaml
# Care + guardrails — no sentiment
context_parts:
  care: "Be patient with non-technical users. Explain acronyms."
  guardrails: "Do not execute code on behalf of users."
```

### Context Parts vs Prompt

| | `prompt` | `context_parts` |
|---|---------|----------------|
| **Purpose** | Define the agent's task and role | Shape how the agent behaves |
| **Scope** | One system message | Up to 4 separate system messages (plus custom keys) |
| **Content** | "You are a support agent. Diagnose issues." | "Be empathetic. Never disclose PII." |
| **Reusability** | Unique per agent | Same guardrails can apply to many agents |

### Context Parts with Different Agent Types

Context parts work with all agent types, but are most impactful for LLM agents where the instructions directly shape LLM output:

```yaml
agents:
  # LLM agent — context parts shape the LLM response
  analyst:
    model: "gpt-4o"
    context_parts:
      guardrails: "Never recommend specific stocks."

  # Human agent — context parts are available in the context template
  reviewer:
    agent_type: "human"
    context_parts:
      care: "This reviewer handles sensitive escalations."
```

## Input Guardrails via Pre-Compose

Pre-compose processors can validate and sanitize input before the LLM sees it:

```python
async def input_guardrail(input_data, context):
    """Validate input before LLM processing"""
    message = input_data.get("user_message", "")

    # Length enforcement
    if len(message) > 10000:
        message = message[:10000]

    # Required field check
    if not message.strip():
        return "Please provide a valid message."

    return message

@pre_compose(input_processor=input_guardrail)
async def my_agent(llm_response, input_data, context):
    return llm_response
```

## Output Guardrails via Intelligence Functions

Intelligence functions run after the LLM call and can validate or modify outputs:

```python
async def content_generator(llm_response, input_data, context):
    """Post-LLM output validation"""
    # Enforce confidence bounds
    confidence = llm_response.get("confidence", 0)
    llm_response["confidence"] = max(0.0, min(1.0, confidence))

    # Ensure required fields
    if not llm_response.get("summary"):
        llm_response["summary"] = "No summary generated"

    return llm_response
```

## Coordination Guardrails

The platform continuously observes execution events and automatically intervenes when things go wrong — retrying transient failures, halting runaway chains, or escalating issues that need human attention. You don't need to wire this up; the safety nets run by default.

You can tune the overall coordination envelope:

```yaml
manager:
  coordination_rules:
    max_agent_calls: 10        # Max calls per session
    max_retries: 3             # Max retries per agent
```

## Token Guardrails

Per-agent token limits prevent cost runaway:

```yaml
agents:
  my_agent:
    max_tokens: 2000
    max_completion_tokens: 1000
```

## Guardrail Summary

| Layer | Mechanism | What It Prevents |
|-------|-----------|-----------------|
| Prompt | Context parts (care, sentiment, guardrails) | Unsafe tone, PII disclosure, off-topic responses |
| Input | Pre-compose processors | Malformed/oversized input |
| Schema | Yields parsing | Structural hallucination |
| Routing | Secure expression evaluation | Unauthorized agent calls |
| Tools | Permission-based access | Unauthorized tool use |
| Output | Intelligence functions | Invalid output values |
| Coordination | Platform safety nets | Runaway chains, failures |
| Cost | Token limits, tool limits | Cost overruns |

## Next Steps

- **[Structured Output](../models/structured-output)** — Yields schema enforcement
- **[Tool Permissions](../tools/permissions)** — Tool access control
- **[Self-Healing](../advanced/self-healing)** — Automatic failure recovery

---

*LeafMesh — Multi-layer validation and safety*
