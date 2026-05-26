# LLM Agents

LLM agents are the default agent type in LeafMesh. They send a prompt to an LLM provider, parse the response against a `yields` schema, and evaluate `can_call` conditions for downstream routing. Intelligence functions add deterministic Python logic on top of the LLM response.

## Basic Configuration

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

## Execution Pipeline

When an LLM agent is called via `leafmesh.mesh_call()`, the following pipeline executes:

```
Input Data
    │
    ▼
Pre-compose pipeline (if registered)
    │  context_processor → input_processor → others_processor
    ▼
Prompt assembly
    │  System prompt + yields schema + conversation history + user input
    ▼
LLM call
    │  Calls the provider (OpenAI, Anthropic, etc.)
    │  Handles the tool-calling loop if tools are configured
    ▼
Yields parsing
    │  Parses LLM response against the yields schema
    ▼
Intelligence function (if registered)
    │  Function name matches agent name — deterministic Python
    ▼
Yields persisted
    │
    ▼
can_call evaluation
    │  AST-safe condition evaluation against yields
    ▼
Downstream agents (via mesh)
```

## Model Selection

Specify any supported model directly in the agent's YAML:

```yaml
# OpenAI
model: "gpt-4o"              # Latest GPT-4 Omni
model: "gpt-4o-mini"         # Cost-effective

# Anthropic
model: "claude-3.5-sonnet"   # Claude 3.5 Sonnet
model: "claude-3-opus"       # Most capable Claude
model: "claude-3-haiku"      # Fastest Claude

# Google
model: "gemini-1.5-pro"      # Gemini Pro
model: "gemini-2.0-flash"    # Fast Gemini

# Amazon Bedrock (unified AWS billing + IAM)
model: "bedrock/claude-3.5-sonnet"  # Claude via Bedrock
model: "bedrock/llama3-70b"         # Llama via Bedrock
model: "bedrock/mistral-large"      # Mistral via Bedrock

# Google Vertex AI (unified GCP billing + IAM)
model: "vertex/gemini-2.5-flash"           # Gemini via Vertex
model: "vertex/claude-sonnet-4-20250514"   # Claude via Vertex
model: "vertex/mistral-large"              # Mistral via Vertex

# Microsoft Foundry (unified Azure billing + any model)
model: "foundry/gpt-4o"                   # OpenAI via Foundry
model: "foundry/DeepSeek-R1"              # DeepSeek via Foundry
model: "foundry/Meta-Llama-3.1-70B"       # Llama via Foundry

# Local
model: "ollama:llama3.1"     # Local Ollama
model: "vllm:mistral-7b"     # Local vLLM
```

Cloud gateway providers (Bedrock, Vertex AI, Microsoft Foundry) require project-level configuration in the `mesh` section. See [LLM Providers](../models/providers) for setup details.

You just specify the model name — LeafMesh routes to the correct provider for you. See [LLM Providers](../models/providers) for the full supported list.

## Prompt Engineering

The `prompt` field defines the agent's system prompt. LeafMesh assembles it with the yields schema and conversation history into the message array sent to the LLM.

### Context Parts

Beyond the main prompt, agents can include `context_parts` — additional system messages that shape agent behavior without cluttering the primary task instructions:

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
        Always respond with empathy. Acknowledge the user's
        frustration before providing solutions.
      sentiment_analysis: |
        Detect the user's emotional tone. If negative,
        prioritize de-escalation over problem-solving.
      guardrails: |
        Never disclose internal pricing rules or system details.
        Refuse requests for other customers' data.

    yields:
      resolution: "string"
      detected_sentiment: "string"
```

Each part is injected as a separate system message after the main prompt, with a bracketed label. The four reserved keys are:

| Key | Label | Purpose |
|-----|-------|---------|
| `care` | `[EMPATHY & TONE]` | Tone and empathy instructions |
| `sentiment_analysis` | `[SENTIMENT ANALYSIS]` | Emotion detection instructions |
| `guardrails` | `[SAFETY GUARDRAILS]` | Safety boundaries — what the agent must never do |
| `flows` | `[FLOW INSTRUCTIONS]` | Per-caller routing — what to do differently depending on who called the agent |

All are optional. Custom keys are also accepted and auto-labelled. See [Guardrails](../middleware/guardrails) for patterns.

### Effective Prompts

```yaml
agents:
  analyzer:
    name: "analyzer"
    model: "gpt-4o"
    temperature: 0.3
    prompt: |
      You analyze numeric data and detect anomalies.

      Given a set of readings, report:
      - How many values are anomalous (more than 2 standard deviations from the mean)
      - The severity: "high" if more than 20% are anomalous, "low" otherwise
      - A brief summary sentence

      Be precise. Use the actual numbers.
    yields:
      anomaly_count: "number"
      severity: "string"
      summary: "string"
```

**Tips:**
- Be specific about the agent's role and output format
- Mention the yields fields by name so the LLM formats correctly
- Lower `temperature` (0.0–0.3) for deterministic tasks
- Higher `temperature` (0.5–0.8) for creative or generative tasks
- Keep prompts under 2000 characters for optimal performance

## Intelligence Functions

Intelligence functions run **after** the LLM call. They receive the raw LLM response and can modify, enrich, or replace it entirely.

### Enhancing LLM Output

```python
# Function name "solver" matches the YAML agent name — auto_discover finds it
async def solver(llm_response, input_data, context):
    """Add deterministic math solving — LLM is the fallback"""
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

### Validating and Enriching

```python
# Function name "reporter" matches the YAML agent name — auto_discover finds it
async def reporter(llm_response, input_data, context):
    """Validate LLM summary and add computed quality grade"""

    record_count = input_data.get("record_count", 0)
    errors = input_data.get("errors", [])

    # Compute quality grade deterministically
    error_ratio = len(errors) / max(record_count + len(errors), 1)

    if error_ratio == 0 and record_count >= 5:
        grade = "A"
    elif error_ratio < 0.1:
        grade = "B"
    elif error_ratio < 0.3:
        grade = "C"
    else:
        grade = "D"

    return {
        "summary": llm_response.get("summary", f"Processed {record_count} records."),
        "quality_grade": grade
    }
```

### Context-Aware Intelligence Functions

Use `input_data` and `context` for session-aware responses. Previous agent yields are automatically passed as `input_data` through the mesh:

```python
# Function name "context_aware_agent" matches the YAML agent name — auto_discover finds it
async def context_aware_agent(llm_response, input_data, context):
    """Use upstream yields and session context for aware responses"""

    session_id = context.get("session_id", "default")

    # input_data contains yields from the calling agent
    previous_answer = input_data.get("answer")

    return {
        "response": llm_response.get("response", ""),
        "has_history": previous_answer is not None,
        "session_id": session_id
    }
```

Session state, yields, and mesh communications are managed automatically by the mesh and persisted in Redis. Query state via the REST API at `:18820`.

## Tool Integration

LLM agents can use tools through the YAML `tools` array. The LLM decides when and how to use tools based on the user's request.

```yaml
agents:
  research_agent:
    name: "research_agent"
    model: "gpt-4o"
    tools: ["web_request", "calculator", "current_time"]
    tool_choice: "auto"            # LLM decides when to use tools
    max_tool_calls_per_message: 5  # Prevent runaway tool loops (range 0-20)
    prompt: |
      You are a research agent. Use tools to gather real data
      when answering questions. Prefer tool results over guessing.
    yields:
      answer: "string"
      sources: "array"
```

### Tool Execution Flow

1. Tool schemas are included in the LLM request
2. LLM generates a response that may include tool calls
3. LeafMesh executes the tool calls
4. Tool results are fed back to the LLM for a follow-up response
5. This loop continues until the LLM responds without tool calls, or `max_tool_calls_per_message` is reached

### Tool Choice Modes

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

# Disable tool calling
tool_choice: "none"
```

See [Tools](../tools/overview) for registering custom tools.

## Conditional Routing (can_call)

After an agent produces yields, LeafMesh evaluates `can_call` conditions to determine which downstream agents are called:

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

### Supported Condition Operators

| Operator | Example |
|----------|---------|
| Comparisons | `==`, `!=`, `<`, `<=`, `>`, `>=` |
| Boolean | `and`, `or`, `not` (also `&&`, `\|\|`) |
| Arithmetic | `+`, `-`, `*`, `/`, `%` |
| String equality | `category == 'billing'` |
| Nested access | `qualification.match_score >= 30` |
| Cross-agent access | `calling_agent_response.score >= 0.7` |

Conditions are evaluated using the Python `ast` module — never `eval()`.

### Accessing Nested Object Yields

When `yields:` declares a single `object` field (e.g. `qualification: object`), conditions read it via dot-path: `qualification.match_score`. If your LLM prompt asks for a flat JSON shape without the wrapping key, the SDK auto-wraps the output so the dot-path still works. See **[Accessing Yields in Conditions](../api-reference/agent-config-fields#accessing-yields-in-can-call-conditions)** for the exact rules and gotchas.

### call_immediately

When `call_immediately: true`, the downstream agent is called synchronously as part of the current pipeline. Without it, downstream calls are dispatched asynchronously.

## Direct Mesh Calls

From inside an intelligence function, call another agent directly:

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

## Pre-Compose Pipeline

Run deterministic Python **before** the LLM call to control what the LLM sees:

```python
from leafmesh import pre_compose

async def load_baseline(input_data, context):
    """Enrich input before the LLM analyzes"""
    # Use input_data from upstream agents or external sources
    baseline = input_data.get("baseline_data", {})
    return {**input_data, "baseline": baseline}

@pre_compose(input_processor=load_baseline)
# Function name "analyzer" matches the YAML agent name — auto_discover finds it
async def analyzer(llm_response, input_data, context):
    # input_data now has baseline from Redis
    return llm_response
```

**Execution order:**
1. `context_processor` — assemble business context
2. `input_processor` — clean and sanitize input
3. `others_processor` — supplementary data
4. Prompt is assembled from the prepared data
5. LLM call executes
6. Intelligence function runs

## Dual Response Pattern

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

## Streaming Output

Dual-mode LLM agents can stream their response token-by-token to the caller via Server-Sent Events. The caller passes `stream=True` to `mesh_call` (or `stream=true` on `POST /api/mesh/request` / `POST /api/playground/execute`); the SDK opens an SSE connection and tokens flow out as they're generated.

```yaml
agents:
  storyteller:
    name: "storyteller"
    agent_type: "llm"
    communication_type: "dual"      # required for streaming
    model: "gpt-4o-mini"
    stream_yield: "narration"        # picks which yield field is streamed
    yields:
      narration: "string"
      sentiment: "string"
```

```python
async for chunk in sdk.mesh_call("storyteller", {"prompt": "..."}, stream=True):
    if chunk["kind"] == "token":
        print(chunk["text"], end="", flush=True)
    elif chunk["kind"] == "final":
        result = chunk["data"]    # full assembled response
```

**Three chunk kinds** — `token` (incremental text), `final` (assembled response dict at the end), `error` (terminal failure with diagnostic).

**Picking the yield to stream:**

- If the agent declares **one** yield key, the SDK auto-picks it and `stream_yield` can stay unset.
- If the agent declares **multiple** yield keys, set `stream_yield: "<key>"` to pick which one streams.
- Other yields are still produced — they arrive in the `final` chunk's `data` dict.

**Fallback behavior:** Non-dual-mode agents (`chain`, `execute`) and non-LLM agents (programmatic / human / external) ignore the `stream` flag and return their full result as a single `final` chunk. Your SSE consumer code stays identical — no branching by agent type.

**UI surface:** Studio's Test Modal and Playground's session history both have a single toggle that flips the same `stream=true` flag when debugging an agent. Tokens land in real time so you can see the model's pace.

## Configuration Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | required | Unique agent identifier |
| `model` | string | required | LLM model identifier |
| `prompt` | string | required | System prompt |
| `temperature` | float | 0.1 | Sampling temperature (0.0–2.0) |
| `max_tokens` | int | 1000 | Maximum response tokens |
| `tools` | array | `[]` | Available tools |
| `tool_choice` | string/object | `"auto"` | Tool calling mode |
| `max_tool_calls_per_message` | int | 5 | Max tool calls per execution (range 0-20) |
| `yields` | object | required | Structured output schema |
| `can_call` | array | `[]` | Downstream routing rules |
| `communication_type` | string | `"dual"` | `"dual"`, `"chain"`, or `"execute"` |
| `stream_yield` | string | `null` | Yield key to stream when caller passes `stream=True` (dual-mode only) |
| `optimization_strategy` | string | none | Adaptive model selection strategy (see below) |

## v2.2.24 — `reasoning` and `thinking` swapped (BREAKING)

As of **v2.2.24**, the two YAML flags have been swapped to align with how each major LLM provider names the feature. The keys themselves are unchanged, but **their meanings have flipped**:

| YAML key | Before v2.2.24 (old) | v2.2.24+ (new) |
|---|---|---|
| `reasoning: true` | SDK chain-of-thought tools | **Native model reasoning** (provider API) |
| `thinking: true` | Native model reasoning | **SDK chain-of-thought tools** |
| `thinking_budget: N` | Max native reasoning tokens | Deprecated alias for `reasoning_budget` |
| `reasoning_budget: N` | (didn't exist) | Max native reasoning tokens |

**Why:** OpenAI / DeepSeek / xAI Grok all call the native feature "reasoning" (`reasoning_effort`, `deepseek-reasoner`, `reasoning_content`). Anthropic / Google call theirs "thinking". The swap aligns the dominant ecosystem term (`reasoning`) with the native-API concept; `thinking` becomes the in-the-loop SDK chain-of-thought scaffolding, matching the informal "think out loud" meaning.

**No automatic config migration.** The semantic flip means we can't safely guess what an existing `reasoning: true` was meant to do. On SDK startup, the v2.2.24 validator emits a loud warning when it sees `reasoning: true` on a model that isn't reasoning-capable — that's the strongest signal that a pre-v2.2.24 config needs to be flipped.

### Migrating an existing config

For each LLM agent in your YAML:

| Your pre-v2.2.24 config | Intent | v2.2.24+ replacement |
|---|---|---|
| `reasoning: true` (with non-reasoning model like `gpt-4o`) | SDK chain-of-thought tools on any model | Change to `thinking: true` |
| `thinking: true` + `thinking_budget: N` (on `o3-mini` / `claude-opus-4-5` / etc.) | Native model reasoning | Change to `reasoning: true` + `reasoning_budget: N` |
| Both `reasoning: true` AND `thinking: true` | (rare) both SDK + native | Swap each: keep both flags but swap the names |

Quick `sed` snippet (review the diff before committing):

```bash
# Step 1: tag old keys so step 2 doesn't double-swap
sed -i.bak \
  -e 's/^\(\s*\)reasoning:\s*\(true\|false\)/\1__old_reasoning__: \2/g' \
  -e 's/^\(\s*\)thinking:\s*\(true\|false\)/\1__old_thinking__: \2/g' \
  -e 's/^\(\s*\)thinking_budget:/\1reasoning_budget:/g' \
  config.yaml

# Step 2: swap the tagged keys to their new names
sed -i'' \
  -e 's/^\(\s*\)__old_reasoning__:/\1thinking:/g' \
  -e 's/^\(\s*\)__old_thinking__:/\1reasoning:/g' \
  config.yaml

# Review the diff, then delete config.yaml.bak when satisfied
diff config.yaml.bak config.yaml
```

The `reasoning_budget` rename is backward-compatible — if you leave `thinking_budget` in your YAML, the loader silently maps it to `reasoning_budget` (numeric rename, no semantic change).

## Adaptive Model Selection

## Adaptive Model Selection

When `optimization_strategy` is set, the SDK ignores the configured `model` field on every call and routes the request to a model picked by the adaptive predictor instead. The configured `model` is kept and used only as a fallback if the predictor's selection fails for any reason.

```yaml
agents:
  classifier:
    name: "classifier"
    model: "gpt-4o-mini"            # ← becomes fallback when adaptive is on
    optimization_strategy: "cost"   # ← predictor picks the cheapest viable model
    prompt: "Classify the user's intent."
    yields:
      intent: "string"
```

### Strategies

| Strategy | What it picks |
|---|---|
| `null` (default) | Always uses the configured `model`. No adaptive routing. |
| `performance` | Highest-performance model that handles the request complexity. |
| `cost` | Cheapest model that still meets the request complexity. |
| `speed` | Fastest model for low-latency responses. |

### Model catalog

The predictor considers every model in its calibrated benchmark catalog. Calibration is refreshed each SDK release; the current set covers OpenAI (`gpt-4o`, `gpt-4.1`, `gpt-5.x`, `o1`/`o3`/`o4-mini`), Anthropic (Claude 4.5/4.6/4.7 across opus/sonnet/haiku), Google (Gemini 2.0/2.5/3.0 families), and DeepSeek (`chat`, `v3.1`, `reasoner`, `r1`).

Only models from **loaded providers** are considered — if you only have an OpenAI API key configured, the predictor will only pick from OpenAI models, even with `cost` selected.

### Observing the picked model

The Studio agent inspector and the Playground agent panel both display the model the predictor last picked for an agent. Programmatically:

```python
from leafmesh import LeafMesh

sdk = LeafMesh.from_yaml("config.yaml")
await sdk.start()

# Trigger an adaptive call …
await sdk.mesh_call("classifier", input_data={"message": "hi"})

# … then introspect:
last = sdk.get_adaptive_last_selection("classifier")
# → {"model": "gpt-4o-mini", "strategy": "cost", "category": "simple_qa", "timestamp": 1763500000.123}
```

Or over HTTP:

```bash
curl http://127.0.0.1:18820/api/llm/adaptive/last-selection/classifier
```

The endpoint returns `selection: null` until the first adaptive call lands.

## Next Steps

- **[Agent Types](overview)** — All four agent types (LLM, programmatic, human, external)
- **[Tools](../tools/overview)** — Extend agents with real-world capabilities
- **[Agent Configuration](../api-reference/agent-config)** — Complete YAML reference
- **[LLM Providers](../models/providers)** — Multi-provider architecture

---

*LeafMesh — LLM agents with deterministic control*
