# LeafMesh Agent Configuration — Complete Field Reference

This document lists every configuration field, its type, default value, and accepted values. Use this to build frontend forms, dropdowns, and validation.

---

## Table of Contents

1. [Agent Types](#agent-types)
2. [AgentConfig — Core Fields (All Types)](#agentconfig--core-fields-all-types)
3. [LLM Agent Fields](#llm-agent-fields-agent_type-llm)
4. [Human Agent Fields](#human-agent-fields-agent_type-human)
5. [External Agent Fields](#external-agent-fields-agent_type-external)
6. [Programmatic Agent Fields](#programmatic-agent-fields-agent_type-programmatic)
7. [WebhookConfig](#webhookconfig)
8. [ChannelConfig](#channelconfig)
9. [Memory Config](#memory-config)
10. [EscalationConfig](#escalationconfig)
11. [EscalationTarget](#escalationtarget)
12. [BrokerConfig](#brokerconfig)
13. [EventListener](#eventlistener)
14. [Top-Level Config (LeafMeshConfig)](#top-level-config-leafmeshconfig)
15. [ManagerConfig](#managerconfig)
16. [MeshConfig & Cloud Providers](#meshconfig--cloud-providers)
17. [RedisConfig](#redisconfig)
18. [EvolutionConfig](#evolutionconfig)
19. [DataStructure](#datastructure)
20. [Entry Points](#entry-points)
21. [Validation Rules](#validation-rules)
22. [Field Applicability by Agent Type](#field-applicability-by-agent-type)

---

## Agent Types

| Value | Description |
|-------|-------------|
| `llm` | LLM-powered agent (default). Executes via OpenAI, Claude, Bedrock, Vertex, or Foundry. |
| `human` | Human operator agent. Routes to a person via API, webhook, or channel. |
| `programmatic` | Python function with business logic. No LLM calls. |
| `external` | Delegates to an external framework (CrewAI, LangGraph, AutoGen, etc.). |

---

## AgentConfig — Core Fields (All Types)

These fields apply to every agent regardless of `agent_type`.

| Field | Type | Default | Accepted Values | Required | Description |
|-------|------|---------|-----------------|----------|-------------|
| `name` | string | — | any string | **yes** | Unique agent name within the mesh |
| `description` | string | `null` | any string | no | Agent description and purpose |
| `agent_type` | string | `"llm"` | `llm`, `human`, `programmatic`, `external` | no | Agent execution type (see note below) |
| `communication_type` | string | `"dual"` | `dual`, `chain`, `execute` | no | How agent communicates with the mesh |
| `response_overrides` | list or dict | `null` | list of `{caller, type}` OR dict `{caller_name: type}` | no | Per-caller override of `communication_type`. Falls back to the default for any caller not listed and for external entry points. See [Per-caller Response Overrides](#per-caller-response-overrides). |
| `parallel` | bool | `false` | `true`, `false` | no | Enable parallel processing |
| `max_concurrent` | int | `null` | 1 – unlimited | no | Max concurrent calls when `parallel: true` (null = unlimited) |
| `wake_up` | string | `null` | cron expression (e.g. `"0 9 * * *"`) | no | Schedule for periodic wake-up |
| `yields` | dict | `{}` | key: field name, value: type string or nested object | no | Output schema — what agent produces |
| `inputs` | dict | `{}` | key: field name, value: type string or nested object | no | Input schema — what agent expects |
| `can_call` | list | `[]` | list of `{"agent": "name"}` or `{"agent": "name", "condition": "expr"}` | no | Agents this agent can invoke |
| `listen_events` | list | `[]` | list of [EventListener](#eventlistener) entries | no | External event sources (Kafka/SQS/MQTT/Redis Streams/IMAP) that trigger this agent. Each entry references a broker by name from the top-level `brokers:` block (BRD-021). |
| `narration` | string | `null` | any string (multiline supported) | no | Plain-English routing hints for the Manager — evaluated when conditions don't cover everything (see [Narration Routing](#narration-routing)) |
| `wait_for` | string or list | `[]` | agent names or expression string | no | Fan-in/join condition |
| `wait_for_timeout` | int | `60` | 1 – unlimited (seconds) | no | Hard timeout for fan-in |
| `auto_store_response` | bool | `true` | `true`, `false` | no | Auto-store responses in Redis |
| `auto_store_yields` | bool | `true` | `true`, `false` | no | Auto-store yields in Redis |
| `memory` | bool or dict | `false` | `true`, `false`, or memory config dict | no | Agent memory — see [Memory Config](#memory-config) |
| `memory_limit` | int | `10` | 1 – 100 | no | Legacy: max recent feed posts (use `memory.limit` instead) |
| `knowledge` | bool or dict | `false` | `false`, or `{serviceName, enabled, groupName}` | no | Knowledge/RAG — see [Knowledge Config](#knowledge-config) |
| `enforce_yields` | bool | `false` | `true`, `false` | no | Strictly validate this agent's output against the declared `yields:` schema. `false` (default) fills missing keys with type defaults and logs warnings; `true` triggers a Manager-driven retry up to `enforce_yields_retry` times, then escalates. See [Yields Enforcement](#yields-enforcement). |
| `enforce_yields_retry` | int | `0` | 0 – unlimited | no | Maximum self-correction attempts when `enforce_yields: true`. `0` fails on first contract violation. Each retry passes the previous output + validation errors as feedback so LLM/external/human/programmatic agents can self-correct. Honored by every agent type. |
| `receive_conversation_history` | bool | `false` | `true`, `false` | no | Opt-in for **non-LLM agents** (programmatic / human / external) to receive prior conversation turns in their payload. LLM agents already see history via the prompt; this flag has no effect on them. When `true`: programmatic agents read it from `context["_conversation_history"]`, external connectors get it on `input_data._conversation_history` AND `context._conversation_history`, human webhooks include it in the body. See [Conversation History Opt-In](#conversation-history-opt-in). |
| `history_limit` | int | `20` | 1 – 200 | no | Max prior turns delivered when `receive_conversation_history: true`. Ignored when the flag is off. Note: human agents that haven't opted in still use the legacy 5-turn fallback for backwards compatibility — flip the flag to switch to this configurable limit. |
| `stream_yield` | string | `null` | any yield key from `yields:` | no | For **dual-mode LLM agents**, picks which yield field is streamed token-by-token when the caller passes `stream=True` to `mesh_call`. If the agent declares exactly one yield key, the SDK auto-picks it and this field can stay unset. See [Streaming Output](#streaming-output). |

### Per-caller Response Overrides

`communication_type` sets one default response behavior for the whole agent — once `dual`, it replies back to every caller; once `chain`, never. Real workflows often need different behavior per caller: a sales agent might want to reply back to a customer-facing router (`dual`) but stay silent when an internal processor calls it (`chain`).

`response_overrides` is an optional per-caller override on top of `communication_type`. Lookup priority at the dual-callback site:

1. If `response_overrides[called_by]` is set → use that type.
2. Otherwise → fall back to `communication_type`.

External entry points (mesh_call from the outside, event listeners, scheduler `wake_up`) have no `called_by` and skip this lookup entirely — they always use the top-level `communication_type`. The override surface is internal-call-only by design.

**List form** (mirrors `can_call` style — recommended for YAML readability):

```yaml
agents:
  sales_agent:
    agent_type: llm
    model: gpt-4o-mini
    communication_type: chain          # default for any caller
    response_overrides:
      - caller: customer_facing_agent  # reply back to this one
        type: dual
      - caller: escalation_router      # reply back to this one too
        type: dual
    # internal_processor: not listed → falls back to chain → no reply
```

**Dict form** (also accepted, terser):

```yaml
agents:
  sales_agent:
    communication_type: chain
    response_overrides:
      customer_facing_agent: dual
      escalation_router: dual
```

Both shapes are normalised internally into a dict `{caller_name: type}` for O(1) runtime lookup.

**Studio UI:** the agent inspector exposes a "Per-caller overrides" panel under the Communication field. The caller dropdown is restricted to agents whose `can_call` actually targets this agent — overrides for unrelated agents would be dead config and never fire. When nobody calls this agent AND no overrides are configured, the panel hides entirely.

**Available since:** SDK v2.2.32 (field + runtime), v2.2.33 (API exposure + Studio panel).

### Yields Enforcement

`enforce_yields` and `enforce_yields_retry` work together to make `yields:` an enforceable contract on the producer side, without coupling agents to each other's shapes.

**Default behavior (`enforce_yields: false`)** — lenient mode, backwards-compatible:

- Missing yield keys → filled with type defaults (`""`, `0`, `[]`, `{}`, `false`).
- Type mismatches → kept verbatim, WARNING logged.
- `can_call` conditions evaluate on a known shape (no more silent skips on undefined keys).

**Strict mode (`enforce_yields: true`)** — for production-critical agents:

- On contract violation, the SDK fires a Manager-driven retry.
- Up to `enforce_yields_retry` attempts. Each retry sees the previous (wrong) output + validation errors as rerun context:
  - **LLM agents** — the prompt appends a correction note.
  - **Human agents** — outbound payload exposes the rerun context; inbox/channel UI surfaces what's needed.
  - **External connectors** — `data._rerun_context` is added to the workflow payload.
  - **Programmatic agents** — `input_data._rerun_context` is available alongside the (possibly auto-corrected) inputs.
- After the retry budget is exhausted, fires `AGENT_ERROR` with `error_type="YieldContractFailure"` + `retry_exhausted=true`. Routes through `manager.escalation:` if configured.

**Example:**

```yaml
agents:
  client:
    agent_type: human
    human_interface: webhook
    yields:
      request_data: object
      decision: string
    enforce_yields: true        # strict
    enforce_yields_retry: 3     # 3 self-correction attempts before escalating
```

**Programmatic agents are retryable too** — the Manager's analysis pass can inspect the failure and produce a `corrected_input` (e.g. fix `"ORGANIZATION"` → `"Organization"`). The retry runs the same deterministic function with the corrected input and produces a different result. See [Manager — Rerun Flow](../core-concepts/manager#rerun) for the full path.

### Dynamic Per-Call Routing (Human Agents)

YAML configures **default** routing for a human agent — `operator_ids: [alice, bob]` lists who can see HITL requests, `channels.slack.post_channel: "C0SLACK0123"` sets the default Slack channel, etc. Real workflows need per-turn dynamism on top: "today's on-call is Alice," "this approval goes to the legal team's WhatsApp," "escalations route to the manager directly."

Routing has two layers. **YAML is the contract** (sane defaults, channel-scoped operator rosters). **Pre-compose is the override** (per-turn steering). They work together: pre-compose narrows when your code knows better; YAML catches anything pre-compose didn't set.

#### Layer 1 — YAML defaults

Operators live **inside each channel** that knows them. Slack owns Slack IDs, WhatsApp owns phone numbers, email owns addresses — the same logical roster (`operator_ids: [alice, bob, carol]`) is resolved per-channel via that channel's own `operators:` map.

```yaml
agents:
  client:
    agent_type: "human"
    is_human_powered: true

    # Default broadcast list — who sees HITL requests when no override.
    # This is the LOGICAL roster (same names used across channels below).
    operator_ids: [alice, bob, carol]

    channels:
      slack:
        bot_token: "${SLACK_BOT_TOKEN}"
        signing_secret: "${SLACK_SIGNING_SECRET}"
        post_channel: "C0DEFAULT"         # fallback when nobody overrides
        # NEW (v2.2.44): channel-scoped operator roster.
        # Lets pre_compose say "_target_operator: alice" — SDK looks up
        # alice's Slack ID under this channel's operators map.
        operators:
          alice: "U0ALICE"                # Slack user ID (DM) or channel ID
          bob:   "U0BOB"
          carol: "C0TEAM_CHANNEL"         # team channel, not DM

      whatsapp:
        bot_token: "${WHATSAPP_TOKEN}"
        signing_secret: "${META_APP_SECRET}"
        post_channel: "+15551111111"
        operators:
          alice: "+14155551234"           # alice's WhatsApp number
          bob:   "+18005550000"

      email:
        enabled: true
        smtp_host: "smtp.acme.com"
        from_address: "ops@acme.com"
        operators:
          alice: "alice@company.com"
          bob:   "bob@company.com"
```

Why channel-scoped? Each channel naturally owns the recipients it can address. Adding Slack → list its operators once inside the slack block. Removing WhatsApp → all its operator info goes with it (no orphans). You never spread a single recipient ID across two YAML sections.

#### Layer 2 — Pre-compose runtime override

Pre-compose populates reserved keys in `input_data`. Underscore prefix marks them as routing metadata (not business fields). Same convention as the existing `_operator_ids`.

| Key | Used by | Effect |
|---|---|---|
| `_target_operator` (**recommended**) | All human-agent paths | Logical operator ID. SDK looks up each configured channel's `operators` map and dispatches to that channel's recipient. Single key drives Slack + WhatsApp + Email + … simultaneously. |
| `_operator_ids` | Default inbox | List override — narrows the HITL broadcast to listed operators. Legacy convention, still works. |
| `_target_channel_id` | Channel adapters | **Escape hatch** — raw recipient ID in the platform's namespace. Use when the ID comes from somewhere dynamic (a Zapier response, an external API) and you don't want it in YAML. Bypasses operator resolution. |
| `_target_channel_provider` | Channel adapters | Pin outbound to one provider when several configured. Values: `slack`, `discord`, `telegram`, `whatsapp`, `teams`, `email`. |
| `_target_webhook_url` | Webhook fallback | Raw URL override for `webhook_config.outbound_url`. Bypasses operator resolution. |

#### Layer 2 — Example: daily on-call rotation

```python
from leafmesh import pre_compose
import datetime


@pre_compose(input_data=lambda data, ctx: {
    **data,
    "_target_operator": _todays_oncall(),     # "alice" on Mon, "bob" on Tue, ...
})
async def escalation_agent(input_data, context):
    return {
        "alert": input_data["incident"],
        "severity": input_data["severity"],
    }


def _todays_oncall() -> str | None:
    """Map weekday → operator ID. Returns None on weekends → YAML default."""
    return {0: "alice", 1: "bob", 2: "carol"}.get(datetime.datetime.now().weekday())
```

If the agent has Slack + WhatsApp + Email configured, **the same `_target_operator: "alice"` routes to all three** — alice's Slack DM, alice's WhatsApp number, alice's email — each pulled from its own channel's `operators:` map. You think in terms of *people*; each channel resolves to its own recipient namespace.

#### Resolution order (per outbound dispatch)

For each configured channel:

1. **`_target_channel_id`** (raw override — power user / dynamic ID)
2. **`_target_operator`** → `channels.<provider>.operators[operator]` (ergonomic)
3. **`adapter.get_channel_for_session(session_id)`** (reply continuity — the channel the inbound message arrived from)
4. **`adapter.config["post_channel"]`** (YAML default)

For the webhook fallback path:

1. **`_target_webhook_url`** (raw)
2. **`webhook_config.operators[operator]`** (ergonomic)
3. **`webhook_config.outbound_url`** (YAML default)

**Fail-soft semantics:** if `_target_operator` is set but the operator has no entry under a given channel's `operators:` map, the SDK logs a WARNING and falls through to (3)/(4) for that channel. **Messages are never silently dropped** — there's always a YAML default to catch the fallback.

#### When to use which layer

| Scenario | Use |
|---|---|
| Fixed recipient — always the same person | **YAML only** (per-channel `operators` map + `operator_ids`) |
| Workflow-driven recipient (on-call, round-robin, escalation tier) | **YAML + pre_compose** (`_target_operator`) |
| Recipient ID from external system (Zapier, MCP, DB lookup) | **YAML + pre_compose** (`_target_channel_id` raw override) |
| Multi-channel rosters (Slack + WhatsApp + Email in parallel) | **Per-channel `operators` + pre_compose `_target_operator`** — single key drives all transports, each channel resolves its own recipient |

#### Applies to all human-agent transports

| Transport | Supports `_target_operator` via | Raw override key |
|---|---|---|
| Default inbox | (narrows broadcast to that operator) | `_operator_ids` |
| Slack | `channels.slack.operators` | `_target_channel_id` + `_target_channel_provider: slack` |
| Discord | `channels.discord.operators` | `_target_channel_id` + `_target_channel_provider: discord` |
| Telegram | `channels.telegram.operators` | `_target_channel_id` + `_target_channel_provider: telegram` |
| WhatsApp | `channels.whatsapp.operators` | `_target_channel_id` + `_target_channel_provider: whatsapp` |
| Teams | `channels.teams.operators` | `_target_channel_id` + `_target_channel_provider: teams` |
| Email | `channels.email.operators` | `_target_channel_id` + `_target_channel_provider: email` |
| Webhook fallback | `webhook_config.operators` | `_target_webhook_url` |

> **Note for LLM, programmatic, external agents:** The `_target_*` convention applies only to human agents (which actually route messages to people). LLM agents have no recipient. Programmatic / external agents route via their own `connector_config` (Zapier action, MCP tool, framework endpoint) — pre_compose can shape that payload via standard input_data fields, but the operator abstraction is human-specific.

Available since SDK v2.2.44. Backward compatible — agents not using the new keys behave exactly as before.

### Conversation History Opt-In

LLM agents automatically receive prior conversation turns in their prompt. Programmatic, human, and external agents do **not** — they're stateless by design. When you want a non-LLM agent to see history (for e.g. domain-specific summarisation, context-aware retrieval), set the flag and the SDK injects the last `history_limit` turns at a standard location.

```yaml
agents:
  context_summariser:
    name: "context_summariser"
    agent_type: "programmatic"
    receive_conversation_history: true
    history_limit: 30          # default 20, range 1-200
    inputs:
      latest_question: "string"
    yields:
      summary: "string"
```

**Where the history lands per agent type:**

| Agent type | Field |
|---|---|
| `programmatic` | `context["_conversation_history"]` |
| `external` (connector) | `input_data["_conversation_history"]` AND `context["_conversation_history"]` |
| `human` | included in the webhook payload body |
| `llm` | (no effect — LLM agents already see history via the prompt) |

**Human agent backwards compatibility:** Human agents that have NOT opted in still use the pre-v2.2.1 hardcoded cap of 5 turns (preserves legacy webhook behaviour). Flip `receive_conversation_history: true` to switch to `history_limit` (default 20).

**Studio + Playground UI:** Both Studio's "Inputs & Outputs" panel and Playground's agent inspector expose a toggle for `receive_conversation_history` and a number input for `history_limit` — visible only when `agent_type` is non-LLM.

### Streaming Output

Dual-mode LLM agents (the default LLM type) can stream their output token-by-token to the caller via Server-Sent Events. The caller passes `stream=True` to `mesh_call`, the SDK opens an SSE connection, and tokens flow out as they're generated.

```yaml
agents:
  storyteller:
    name: "storyteller"
    agent_type: "llm"
    communication_type: "dual"   # required for streaming
    model: "gpt-4o-mini"
    stream_yield: "narration"     # picks which yield field gets streamed
    yields:
      narration: "string"
      sentiment: "string"
```

```python
# Caller-side (Python)
async for chunk in sdk.mesh_call("storyteller", {"prompt": "..."}, stream=True):
    if chunk["kind"] == "token":
        print(chunk["text"], end="", flush=True)
    elif chunk["kind"] == "final":
        # full assembled response when the agent finishes
        result = chunk["data"]
```

**Chunk envelope** — three kinds: `token` (incremental text), `final` (assembled response dict at the end), `error` (terminal failure).

**Auto-pick rule:** If the agent declares exactly ONE yield key, `stream_yield` can be omitted and the SDK auto-picks that key. If the agent has multiple yields, set `stream_yield` explicitly.

**Falls back cleanly:** Non-dual-mode agents (`communication_type: chain`, `execute`) and non-LLM agents ignore the stream flag and return the full result as a single `final` chunk. Your SSE consumer code stays identical.

**API surface:** `POST /api/mesh/request` and `POST /api/playground/execute` both honour `stream=true`. Studio's Test Modal and Playground's session history have a single toggle to enable streaming for debugging.

### Accessing Yields in `can_call` Conditions

`can_call.condition` expressions read from the agent's parsed yields. Whatever shape your yields produce is what the condition sees.

#### Flat yields → top-level access

```yaml
agents:
  triage:
    yields:
      urgency: number
      category: string
    can_call:
      - agent: specialist
        condition: "urgency >= 7"
      - agent: billing_handler
        condition: "category == 'billing'"
```

#### Nested object yield → dot-path access

```yaml
agents:
  qualification_agent:
    yields:
      qualification: object       # one object yield
    can_call:
      - agent: assessment_agent
        condition: "qualification.match_score >= 30"
```

For this pattern, the condition `qualification.match_score >= 30` reads the nested field. Both forms are valid — pick whichever matches how your LLM (or programmatic function) naturally produces output.

#### Auto-wrap: flat LLM output under a single object yield

LLM prompts often ask for a flat JSON shape (top-level fields), even when the YAML declares `yields: { something: object }`. A common case:

```yaml
yields:
  qualification: object
```

```text
prompt: ...
OUTPUT FORMAT: Return only valid JSON.
{
  "match_score": 0,
  "recommendation": "...",
  "summary": "..."
}
```

The LLM does what the prompt asks — returns `{match_score: 65, recommendation: "...", ...}` at the top level, without a `qualification:` wrapper.

When **all three** conditions hold, the SDK reads the customer's intent and treats the whole flat dict as the value of that single yield, so `qualification.match_score >= 30` works:

| | |
|--|--|
| Schema declares | exactly **one** yield |
| Type is | `object` (or `dict`) |
| LLM returned | a non-empty dict that does **not** contain the yield key |

**Result:** `qualification = {match_score: 65, recommendation: "...", summary: "..."}` — accessible via dot-path in conditions.

This rule does **not** fire when:

- Multiple yields are declared (ambiguous — which one would the flat dict belong to?)
- The single yield is a scalar (`string`, `number`, `boolean`, `list`)
- The result already contains the yield key (already wrapped — passes through unchanged)
- The result is empty `{}` (treated as "missing", same as before)

If you want explicit nesting end-to-end, change your prompt to wrap:

```text
OUTPUT FORMAT: Return only valid JSON.
{
  "qualification": {
    "match_score": 0,
    "recommendation": "...",
    "summary": "..."
  }
}
```

Both forms now produce the same `qualification` yield, so existing configurations don't need to change.

#### Common gotchas

| Symptom | Cause | Fix |
|---|---|---|
| Condition silently fails, narration routes elsewhere | LLM returned a different shape than declared in yields | Either reshape prompt to match yields, or rely on auto-wrap above for single-object yields |
| `Failed to evaluate condition`: `'>=' not supported between instances of 'NoneType' and 'int'` in logs | The yield key was missing → defaulted to `None`/`{}` → dot-path access against `None` | Check the `YIELDS: ... produced incomplete output` warning that fires just before — that names the missing key |
| Condition evaluates to `False` when you expected `True` | Yield key present but value is the type default (`""`, `0`, `[]`, `{}`) | Same root cause — your output didn't actually populate the field |

See **[Message Routing — Condition Evaluation](../messages/routing#condition-evaluation)** for the full operator reference.

### Changing `agent_type`

You can change an agent's type from **Studio's Studio tab** (per-agent editor). When `agent_type` changes, LeafMesh automatically **removes fields that don't belong to the new type**:

| Switching away from... | Fields removed |
|------------------------|----------------|
| `llm` | `model`, `prompt`, `temperature`, `max_tokens`, `max_completion_tokens`, `thinking`, `reasoning`, `reasoning_budget`, `tools`, `tool_categories`, `context_parts`, `tool_choice` |
| `human` | `webhook_config`, `human_interface`, `human_timeout_seconds`, `channels`, `is_human_powered` |
| `external` | `framework`, `connector_config` |
| `programmatic` | `integration` |

This prevents stale configuration from the old type interfering with the new type's execution.

### `yields` and `inputs` Type Strings

Values can be a simple type string (flat field) or a nested object definition.

**Flat fields** — value is a type string:

| Type String | Description |
|-------------|-------------|
| `"string"` | Text value |
| `"number"` | Numeric value |
| `"boolean"` | True/false |
| `"list"` | Array/list |
| `"object"` | Dictionary/object (unstructured) |

**Nested fields** — value is an object with `type` and `fields`:

```yaml
inputs:
  # Flat fields
  name: string
  email: string

  # Nested object with defined sub-fields
  arguments:
    type: object
    fields:
      summary: string
      start_datetime: string
      end_datetime: string
      timezone: string

yields:
  # Flat
  status: string

  # Nested
  data:
    type: object
    fields:
      result: string
      metadata: object
```

When a field uses the nested format, the frontend renders individual sub-field editors instead of a single text input. This is useful for external framework integrations (Composio, Zapier, etc.) where the request body has a known structure.

### `wait_for` Expression Syntax

```yaml
# Simple list — all required (AND)
wait_for:
  - agent_a
  - agent_b

# Expression strings
wait_for: "agent_a AND agent_b"                            # Wait for both
wait_for: "agent_a OR agent_b"                             # Wait for first
wait_for: "agent_a AND agent_b?"                           # agent_b is optional (? suffix)
wait_for: "agent_a AND (agent_b OR agent_c)"               # Nested logic
wait_for: "agent_a AND (agent_b OR agent_c) AND agent_d?"  # Complex expression
```

### `can_call` Format

```yaml
# Simple
can_call:
  - agent: "next_agent"

# With condition
can_call:
  - agent: "next_agent"
  - agent: "conditional_agent"
    condition: "calling_agent_response.status == 'ready'"
```

### Narration Routing

`narration` is an agent-level field for routing hints you **can't express as conditions**. Conditions handle definitive routes ("if category is billing, call billing_agent"). Narration handles non-definitive routes ("if the customer sounds frustrated and mentions cancelling, maybe call retention_agent").

```yaml
agents:
  triage:
    yields:
      category: "string"
      urgency: "number"
    can_call:
      - agent: "billing_agent"
        condition: "category == 'billing'"
      - agent: "technical_agent"
        condition: "category == 'technical'"
    narration: >
      If the customer mentions cancelling their subscription, route to retention_agent.
      If the customer mentions a competitor by name, route to win_back_agent.
      If the customer asks about enterprise plans, route to sales_agent.
```

**How it works:**

1. Conditions are evaluated first by the control plane (AST, instant, deterministic)
2. Condition targets are dispatched immediately
3. The Manager's analysis pass reads the narration alongside the agent output
4. The Manager recommends additional next agents based on both condition results and narration hints
5. The Manager calls any narration-suggested agents that conditions didn't already dispatch

**Key rules:**

- Conditions are the authority — narration never overrides a condition result
- Narration targets are **additive** — they add to condition targets, never remove
- Narration can reference **any agent** in the mesh, not just those in `can_call`
- No narration = zero overhead
- If the Manager is disabled, narrations are ignored

See **[Manager — Narration Routing](../core-concepts/manager#narration-routing)** and **[Message Routing](../messages/routing#narration-routing)** for the full flow.

### Knowledge Config

`knowledge` enables RAG-powered context injection from a vector database. The agent gets both pre-call injection (automatic) and a `query_knowledge` tool (on-demand) — same dual pattern as memory.

```yaml
agents:
  support_agent:
    knowledge:
      serviceName: "mongo_main"
      enabled: true
      groupName: "product_docs"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `serviceName` | string | yes | — | Provider name (configured via Knowledge API, stored in Redis) |
| `enabled` | bool | no | `true` | Enable/disable knowledge for this agent |
| `groupName` | string | no | `null` | Query a specific group. Omit to query all groups. |

**Key points:**

- Provider connection details (connection strings, API keys, embedding model) are configured via the Knowledge API, not in YAML
- When enabled, both retrieval paths are active automatically — no mode flag
- `query_knowledge` tool is stripped from agents without knowledge enabled
- The Manager can also have knowledge for SOP awareness (configured under `manager.knowledge`)

See **[Manager — Narration Routing](../core-concepts/manager#narration-routing)** for how knowledge integrates with Manager analysis.

---

## LLM Agent Fields (`agent_type: "llm"`)

These fields are used when `agent_type` is `"llm"`. Ignored for other types.

| Field | Type | Default | Accepted Values | Description |
|-------|------|---------|-----------------|-------------|
| `model` | string | `"gpt-4o-mini"` | see [Model List](#model-list) below | LLM model name |
| `prompt` | string | `null` | any string (multiline supported) | System prompt |
| `temperature` | float | `0.1` | `0.0` – `2.0` | LLM temperature (creativity/randomness) |
| `max_tokens` | int | `800` | 1 – model max | Max output tokens (legacy models) |
| `max_completion_tokens` | int | `null` | 1 – model max | Max completion tokens (o1, gpt-5.x models) |
| `thinking` | bool | `false` | `true`, `false` | **v2.2.24+:** SDK chain-of-thought scaffolding tools (`chain_of_thought`, `metacognitive_reflection`, `python_exec`, `apply_edits`) — works on any model. Was `reasoning` pre-v2.2.24. |
| `reasoning` | bool | `false` | `true`, `false` | **v2.2.24+:** Native model reasoning via provider API. Requires a reasoning-capable model (o-series, gpt-5.x, Claude 4 manual-thinking, Gemini 2.5/3.x, DeepSeek-Reasoner). Was `thinking` pre-v2.2.24. |
| `reasoning_budget` | int | `null` | 1024 – 32768 (tokens) | **v2.2.24+:** Max native reasoning tokens. Was `thinking_budget` pre-v2.2.24 (which is still accepted as a deprecated alias). |
| `enable_prompt_caching` | bool | `false` | `true`, `false` | Enable provider-native prompt caching for cost reduction (see below) |
| `optimization_strategy` | string | `null` | `performance`, `cost`, `speed` | Per-agent adaptive model selection. When set, overrides `model` with the predictor's pick; the configured `model` becomes the fallback. See [LLM Agents → Adaptive Model Selection](../agents/llm-agents#adaptive-model-selection). |
| `context_parts` | dict | `null` | see below | Optional context parts |
| `tools` | list | `[]` | tool name strings | Available tools |
| `tool_choice` | string | `"auto"` | `auto`, `none`, or specific tool name | Tool selection strategy |
| `max_tool_calls_per_message` | int | `5` | 0 – 20 | Max tool calls per LLM message |
| `tool_call_timeout` | float | `30.0` | 0.1 – 300 (seconds) | Tool execution timeout |
| `allow_parallel_tool_calls` | bool | `true` | `true`, `false` | Allow parallel tool execution |
| `tool_categories` | list | `[]` | category name strings | Tool categories agent can access |

### `context_parts` Keys

Each key is injected as a separate system message with a bracketed label, in the order below. Custom keys are also supported — they receive an auto-generated label from their name (`MY_KEY` → `[MY KEY]`).

| Key | Label injected | Description |
|-----|---------------|-------------|
| `care` | `[EMPATHY & TONE]` | Warmth/empathy instructions — shapes how the agent expresses itself |
| `sentiment_analysis` | `[SENTIMENT ANALYSIS]` | Tone detection instructions — tells the agent to read user mood |
| `guardrails` | `[SAFETY GUARDRAILS]` | Safety and compliance rules — what the agent must never do |
| `flows` | `[FLOW INSTRUCTIONS]` | **Per-caller routing behaviour** — what the agent should do differently depending on who called it and where in the mesh it is |

Values are free text strings. All keys are optional — use any combination.

```yaml
context_parts:
  care: |
    Always respond with empathy. Acknowledge frustration before solving.
  guardrails: |
    Never share internal system details. No PII disclosure.
  flows: |
    When called from the entry point (no from_agent):
      - This is a new user. Greet warmly and gather requirements.
    When called from client (human agent):
      - The human has already responded. Don't re-greet. Summarise and proceed.
    When called from scheduler_agent:
      - This is a scheduled run. Skip greeting, produce a structured summary.
```

### Model List

**OpenAI:** (`OPENAI_API_KEY`)
- `gpt-4o-mini`, `gpt-4o`
- `gpt-4.1`, `gpt-4.1-mini`, `gpt-4.1-nano`
- `gpt-5.1`, `gpt-5.2`
- `o1`, `o1-mini`, `o3`, `o3-mini`, `o4-mini`

**Anthropic:** (`ANTHROPIC_API_KEY`)
- `claude-opus-4-7`, `claude-opus-4-6`, `claude-opus-4-5`
- `claude-sonnet-4-7`, `claude-sonnet-4-6`, `claude-sonnet-4-5`
- `claude-haiku-4-6`, `claude-haiku-4-5`

**Google:** (`GOOGLE_API_KEY` / `GEMINI_API_KEY`)
- `gemini-2.0-flash`
- `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite`
- `gemini-3-pro-preview`

**DeepSeek:** (`DEEPSEEK_API_KEY`)
- `deepseek-chat`, `deepseek-reasoner`

**Mistral:** (`MISTRAL_API_KEY`) *(v2.2.25)*
- `mistral-large-2`, `mistral-medium-3`, `mistral-small-3`
- `codestral-2`
- Self-hosted: set `MISTRAL_BASE_URL` to override the default `https://api.mistral.ai/v1` endpoint

**xAI Grok:** (`XAI_API_KEY`) *(v2.2.25)*
- `grok-4`, `grok-4-mini`, `grok-2-vision`

**AWS Bedrock:**
- Any Bedrock model ID (e.g. `anthropic.claude-3-sonnet-20240229-v1:0`, `amazon.titan-text-premier-v1:0`)
- Requires `mesh.bedrock` config

**Google Vertex AI:**
- Any Vertex model ID (e.g. `gemini-1.5-pro`)
- Requires `mesh.vertex` config

**Azure Foundry:**
- Any Azure deployment name
- Requires `mesh.foundry` config

**Local Models (vLLM, SGLang, Ollama, llama.cpp, etc.):**
- Any model name supported by your local server
- Requires `mesh.local` config (or `LOCAL_MODEL_ENDPOINT` env var)
- See [LocalModelConfig](#localmodelconfig) for server setup

### `thinking` vs `reasoning` (v2.2.24+ semantics)

These are two **separate** features. The YAML key meanings were swapped in v2.2.24 to align with provider terminology — see [LLM Agents → v2.2.24 migration](../agents/llm-agents#v2224--reasoning-and-thinking-swapped-breaking).

| Feature | `thinking: true` | `reasoning: true` |
|---------|-------------------|-------------------|
| **What it does** | SDK injects chain-of-thought scaffolding tools (`chain_of_thought`, `metacognitive_reflection`, `python_exec`, `apply_edits`) into the available tool list | Enables provider-native extended reasoning / thinking |
| **Works with** | Any model (tool injection) | Only models that support native reasoning |
| **Token cost** | Tool-call overhead | Dedicated reasoning tokens (billed as output) |
| **Quality** | Good for structured CoT scaffolding | Best quality — model's internal reasoning |

You can use both together — `thinking` adds SDK reflection tools while `reasoning` enables the model's own native chain-of-thought.

### Native Reasoning — Provider Support

| Provider | Model Requirement | Behavior |
|----------|------------------|----------|
| **Anthropic** | Claude 3.7+ except `claude-opus-4-7` (adaptive-only) | Sends `thinking: {type:enabled, budget_tokens:N}`. Adaptive-only models (opus-4-7, mythos) auto-skip the manual parameter — the model decides for itself. |
| **OpenAI** | o-series (o1/o3/o4-mini), gpt-5.x | `reasoning_effort: str` parameter on `chat.completions.create()` (NOT the `reasoning: {effort: ...}` dict — that's the Responses API). |
| **Google** | Gemini 2.5+ (uses `thinking_budget`), Gemini 3.x (uses `thinking_level: low/medium/high`) | Family-aware param selection — provider auto-picks the right field per model. |
| **DeepSeek** | `deepseek-reasoner` (only valid reasoner API id) | Implicit via model name; emits `reasoning_content`. Temperature / top_p / penalties are silently stripped (reasoner ignores them anyway). |
| **Bedrock** | Claude models on Bedrock (same Anthropic rules) | Writes `additionalModelRequestFields.thinking` (NOT `inferenceConfig.thinking` — that location is rejected). |
| **Vertex** | Claude + Gemini on Vertex | Both paths supported with the same family rules. |
| **Foundry** | Azure o-series + gpt-5.x deployments | `reasoning_effort: str` (same kwarg shape as direct OpenAI). |
| **Mistral** *(v2.2.25)* | No native reasoning API as of v2.2.25 | `reasoning: true` is silently ignored with an informational log. Use `thinking: true` for SDK chain-of-thought scaffolding. |
| **xAI Grok** *(v2.2.25)* | `grok-4-mini` only (`grok-4` rejects the field, `grok-2-vision` doesn't accept it) | `reasoning_effort` accepts only `low`/`high` (NOT minimal/medium/xhigh — xAI returns 400). Provider auto-maps the SDK's 5-tier effort to xAI's 2-tier (medium → low, xhigh → high). |
| **Local** | Depends on model/server | Passthrough if server supports it. |

### Prompt Caching — Provider Support

| Provider | How it works | Savings |
|----------|-------------|---------|
| **Anthropic** | `cache_control: ephemeral` on system prompt + tools | ~90% on cached reads |
| **Bedrock** | `promptCaching` parameter | ~90% on cached reads |
| **Vertex (Claude)** | `cache_control: ephemeral` on system prompt | ~90% on cached reads |
| **OpenAI** | Automatic — no config needed (stats in response) | ~50% on cached |
| **Google** | Context caching API (requires separate setup) | Varies |

### Structured Output — Derived from `yields`

You do **not** declare a separate `response_format` field. The agent's [`yields`](#yields-and-inputs-type-strings) schema is the single source of truth — at runtime the SDK auto-builds a provider-appropriate JSON enforcement shape from it.

```yaml
agents:
  data_extractor:
    agent_type: llm
    model: gpt-4o
    prompt: "Extract structured data from the user's message."
    yields:                     # ← this IS the output contract
      name: string
      email: string
      priority: string
```

| Provider | What the SDK applies under the hood |
|----------|--------------------------------------|
| **OpenAI** | `response_format = {"type": "json_object"}` (basic JSON mode) |
| **DeepSeek** | `response_format = {"type": "json_object"}` |
| **Foundry** | `response_format = {"type": "json_object"}` |
| **Local** | `response_format = {"type": "json_object"}` |
| **Anthropic** | Tool-based JSON extraction using the derived schema |
| **Bedrock** | Schema injected into system prompt |
| **Google / Vertex** | `response_schema` in generation config |

If the LLM produces non-JSON or output that doesn't match the yields keys, the SDK runs one reflection retry; if that also fails, the agent returns a clean error instead of silently substituting defaults.

### Example

```yaml
agents:
  analyst:
    agent_type: llm
    model: claude-sonnet-4-6
    thinking: true              # native model thinking
    thinking_budget: 8192       # max 8K thinking tokens
    reasoning: true             # also inject built-in chain-of-thought tools
    enable_prompt_caching: true # cache system prompt + tools
    prompt: |
      You are a data analyst. Analyze the provided data thoroughly.
```

---

## Human Agent Fields (`agent_type: "human"`)

These fields are used when `agent_type` is `"human"`. `is_human_powered` is auto-set to `true`.

| Field | Type | Default | Accepted Values | Description |
|-------|------|---------|-----------------|-------------|
| `is_human_powered` | bool | `false` | `true`, `false` | Auto-synced to `true` when agent_type="human" |
| `human_interface` | string | `"api"` | `default`, `api`, `webhook`, `custom` | How human receives/submits input (see below) |
| `human_timeout_seconds` | int | `300` | 1 – 3600 (seconds) | Human response timeout |
| `human_context_template` | string | `null` | any string | Template for presenting context to human |
| `human_prompt_template` | string | `null` | any string | Template for human prompts |
| `fallback_on_timeout` | bool | `true` | `true`, `false` | Use fallback response when human doesn't respond |
| `fallback_response` | dict | `null` | arbitrary JSON | Default response on human timeout |
| `require_human_confirmation` | bool | `false` | `true`, `false` | Require approval before proceeding |
| `human_escalation_triggers` | list | `[]` | free text strings | Conditions triggering human escalation |
| `operator_ids` | list | `[]` | list of strings (email or ID) | Operators who can see this agent's HITL requests. Empty = broadcast (all operators see it). |
| `webhook_config` | object | `null` | see [WebhookConfig](#webhookconfig) | Webhook settings (required for `webhook` interface) |
| `channels` | dict | `{}` | see [ChannelConfig](#channelconfig) | Native channel adapters (Slack, Telegram, etc.) |

### `human_interface` — Interface Types

| Value | Description | How it works |
|-------|-------------|-------------|
| `default` | **Built-in HITL Inbox** (recommended) | Writes request to Redis, emits stream event. Studio Frontend renders an inbox with conversation thread. Human replies via the UI. Supports parallel requests per session. |
| `webhook` | **External webhook** | POSTs request to `webhook_config.outbound_url`. Human responds via inbound webhook endpoint. Also supports native channel adapters (Slack, Telegram, etc.). |
| `api` | **Python callback** | Calls a Python handler set on the human agent instance via `human_agent.set_human_interface_handler(handler)` after `sdk.start()`. Retrieve the agent from `sdk.agent_registry.get_agent("<name>")`. No outbound HTTP. Used for custom integrations and testing. |
| `custom` | **Custom handler** | Same as `api` — uses the registered `human_interface_handler` callback. |

> **Note:** `default` mode writes the request to Redis and emits a stream event for an inbox UI to pick up — Studio renders this out of the box. If you're not running Studio, point `webhook` at your own `outbound_url` or use `api` with a Python callback instead.

### Example — Default (Studio Frontend Inbox)

```yaml
agents:
  support_human:
    agent_type: human
    human_interface: default          # Studio Frontend inbox
    human_timeout_seconds: 300
    yields:
      resolution: string
      action_taken: string
```

### Example — Webhook with Channel Adapter

```yaml
agents:
  support_human:
    agent_type: human
    human_interface: webhook
    human_timeout_seconds: 600
    webhook_config:
      outbound_url: "https://my-app.com/api/human-requests"
    channels:
      slack:
        bot_token: "${SLACK_BOT_TOKEN:}"
        signing_secret: "${SLACK_SIGNING_SECRET:}"
        post_channel: "C123456"
```

### Two Scenarios for Human Agent Sessions

Human agents support two interaction patterns via the same webhook endpoint:

**Scenario 1 — Resume (session_id present):** When a POST to `/webhook/{entry_point}` includes a `session_id` that matches a pending HITL request, LeafMesh resumes that session. The operator's response is routed via `can_call` to the next agent.

**Scenario 2 — New (no session_id or not found):** When a POST has no `session_id` or the session has no pending expectation, LeafMesh creates a new workflow. If the human agent has no upstream caller, the operator's message is immediately routed via `can_call` — no HITL pending step is created.

---

## External Agent Fields (`agent_type: "external"`)

These fields are used when `agent_type` is `"external"`.

| Field | Type | Default | Accepted Values | Required | Description |
|-------|------|---------|-----------------|----------|-------------|
| `framework` | string | `null` | `crewai`, `langgraph`, `autogen`, `a2a`, `mcp`, `zapier`, `composio`, `n8n`, `custom` | **yes** | External framework name |
| `connector_config` | dict | `{}` | framework-specific key-values | no | Connection configuration — passed as `**kwargs` to the connector |

> **One agent = one action/workflow.** Each agent targets one specific endpoint, graph, tool, or action. Create multiple agents with different `connector_config` values to call different workflows.
>
> All `connector_config` fields can also be overridden per-call via `request.connector_config` at runtime.

### Common connector_config fields (all frameworks)

These fields are available on **every** connector type:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mode` | string | `"sync"` | Execution mode: `"sync"` (wait for HTTP response) or `"callback"` (fire request, wait for external system to POST back) |
| `callback_timeout` | float | `120.0` | Seconds to wait for a callback response before timing out (only used when `mode: "callback"`) |

#### Sync vs Callback Mode

**Sync mode** (default): The connector POSTs to the external system and holds the HTTP connection open until the response arrives. This works when the external system returns the actual result in the same HTTP response.

**Callback mode**: The connector POSTs to the external system with a `_leafmesh_callback_url` and `_leafmesh_session_id` injected into the payload. The connector then blocks internally until the external system POSTs the result back to `/callback/{agent_name}`. Use this when:
- The external workflow takes longer than the HTTP timeout
- The external system uses "fire and forget" (e.g., n8n's "Respond Immediately" mode)
- You need the external system to process asynchronously and deliver results later

**How external systems use callbacks:**

The LeafMesh connector injects these fields into the outbound payload:
- `_leafmesh_callback_url` — the URL to POST the result back to
- `_leafmesh_session_id` — the session ID to include in the callback

The external system should POST to `_leafmesh_callback_url` with a JSON body containing:
```json
{
  "session_id": "<the _leafmesh_session_id value>",
  "result": { ... }
}
```

### connector_config fields per framework

#### crewai

| Field | Type | Default | Required | Env Fallback | Description |
|-------|------|---------|----------|-------------|-------------|
| `endpoint` | string | `""` | **yes** | `CREWAI_ENDPOINT` | HTTP endpoint for deployed CrewAI crew |
| `api_key` | string | `""` | no | `CREWAI_API_KEY` | Bearer Token for authentication |
| `user_api_key` | string | `""` | no | `CREWAI_USER_API_KEY` | User Bearer Token (preferred over `api_key` when both are set) |
| `poll_interval` | float | `2.0` | no | — | Seconds between status polls |
| `max_poll_seconds` | float | `300.0` | no | — | Max total polling time (seconds) |
| `http_timeout` | float | `30.0` | no | — | HTTP request timeout (seconds) |

#### langgraph

| Field | Type | Default | Required | Env Fallback | Description |
|-------|------|---------|----------|-------------|-------------|
| `endpoint` | string | `""` | **yes** | `LANGGRAPH_ENDPOINT`, `LANGCHAIN_ENDPOINT` | LangGraph Platform deployment URL |
| `api_key` | string | `""` | no | `LANGCHAIN_API_KEY`, `LANGGRAPH_API_KEY` | API key |
| `graph_id` | string | `"agent"` | no | — | **Which graph to run** — this is the workflow selector |
| `poll_interval` | float | `1.0` | no | — | Seconds between status polls |
| `max_poll_seconds` | float | `300.0` | no | — | Max total polling time (seconds) |
| `http_timeout` | float | `30.0` | no | — | HTTP request timeout (seconds) |

#### autogen

Connects to an external AutoGen Studio or custom AutoGen API service via HTTP.

| Field | Type | Default | Required | Env Fallback | Description |
|-------|------|---------|----------|-------------|-------------|
| `endpoint` | string | `""` | **yes** | `AUTOGEN_ENDPOINT` | AutoGen service base URL (e.g. `http://localhost:8081`) |
| `api_key` | string | `""` | no | `AUTOGEN_API_KEY` | Bearer token for authentication |
| `workflow_id` | string | `""` | no | — | Workflow/agent ID to execute on the AutoGen service |
| `timeout` | float | `120.0` | no | — | HTTP request timeout (seconds) |
| `poll_interval` | float | `2.0` | no | — | Seconds between status poll requests |
| `max_poll_seconds` | float | `300.0` | no | — | Max total polling time (seconds) |

#### a2a

| Field | Type | Default | Required | Env Fallback | Description |
|-------|------|---------|----------|-------------|-------------|
| `url` | string | `""` | **yes** | `A2A_AGENT_URL` | A2A-compatible agent server base URL |
| `auth_token` | string | `""` | no | `A2A_AUTH_TOKEN` | Bearer token for authentication |
| `auth_scheme` | string | `"Bearer"` | no | — | Authorization header scheme |
| `poll_interval` | float | `2.0` | no | — | Seconds between task status polls |
| `max_poll_seconds` | float | `300.0` | no | — | Max total polling time (seconds) |
| `http_timeout` | float | `30.0` | no | — | HTTP request timeout (seconds) |

#### mcp

MCP supports two transport modes. `tool_name` is always required.

**Common fields (both transports):**

| Field | Type | Default | Required | Env Fallback | Description |
|-------|------|---------|----------|-------------|-------------|
| `tool_name` | string | `""` | **yes** | — | **Which MCP tool to call** — the workflow selector |
| `transport` | string | `"stdio"` | no | — | Transport mode: `"stdio"` or `"http"` |
| `timeout` | float | `60.0` | no | — | Request timeout (seconds) |

**stdio transport fields:**

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `command` | string | `""` | **yes** (stdio) | Executable to launch (e.g. `"npx"`) |
| `args` | list | `[]` | no | Command arguments (e.g. `["-y", "@mcp/server-npm"]`) |
| `env` | dict | `null` | no | Environment variables for the subprocess |

**http transport fields:**

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `url` | string | `""` | **yes** (http) | MCP server HTTP/SSE endpoint |
| `auth_token` | string | `""` | no | Bearer token |

#### zapier

Tool name is built as `{connection}_{action}` (e.g. `google_sheets_create_row`).

| Field | Type | Default | Required | Env Fallback | Description |
|-------|------|---------|----------|-------------|-------------|
| `connection` | string | `""` | yes* | — | Zapier app name (e.g. `"google_sheets"`, `"slack"`, `"gmail"`) |
| `action` | string | `""` | yes* | — | Action name (e.g. `"create_row"`, `"send_message"`) |
| `mcp_key` | string | `""` | yes† | `ZAPIER_MCP_KEY` | Zapier MCP key — used first if `prefer_mcp=true` |
| `api_key` | string | `""` | yes† | `ZAPIER_API_KEY` | Zapier REST API key — used as fallback |
| `prefer_mcp` | bool | `true` | no | — | Try MCP path first; fall back to REST on failure |
| `instructions` | string | `""` | no | — | Optional natural language instructions (REST path only) |
| `timeout` | float | `60.0` | no | — | HTTP request timeout (seconds) |

*At least one of `connection` or `action` required for the tool name. †At least one of `mcp_key` or `api_key` required.

#### composio

| Field | Type | Default | Required | Env Fallback | Description |
|-------|------|---------|----------|-------------|-------------|
| `action` | string | `""` | **yes** | — | **Composio action enum** (e.g. `"GITHUB_STAR_A_REPOSITORY"`) — the workflow selector |
| `entity_id` | string | `"default"` | no | `COMPOSIO_ENTITY_ID` | User/entity context for managed auth |
| `api_key` | string | `""` | no | `COMPOSIO_API_KEY` | Composio API key |
| `timeout` | float | `60.0` | no | — | Execution timeout (seconds) |

#### n8n

| Field | Type | Default | Required | Env Fallback | Description |
|-------|------|---------|----------|-------------|-------------|
| `webhook_url` | string | `""` | **yes** | `N8N_WEBHOOK_URL` | Full webhook trigger URL — **one URL per n8n workflow** |
| `auth_token` | string | `""` | no | `N8N_AUTH_TOKEN` | Bearer token |
| `timeout` | float | `60.0` | no | — | HTTP request timeout (seconds, sync mode only) |

**n8n webhook URL types:**
- **Production:** `https://your-instance.app.n8n.cloud/webhook/<id>` — works when workflow is **activated** (toggle ON)
- **Test:** `https://your-instance.app.n8n.cloud/webhook-test/<id>` — only works while n8n editor has "Listen for Test Event" active (one-shot, for development only)

**n8n + callback mode:**

When `mode: "callback"`, the n8n workflow should:
1. Start with a Webhook trigger node (receives the payload including `_leafmesh_callback_url`)
2. Configure the Webhook node to "Respond Immediately" (optional — sync mode works too)
3. Process the workflow
4. End with an HTTP Request node that POSTs back to `{{ $json._leafmesh_callback_url }}` with body:
   ```json
   { "session_id": "{{ $json._leafmesh_session_id }}", "result": { ... } }
   ```

---

## Programmatic Agent Fields (`agent_type: "programmatic"`)

These fields are used when `agent_type` is `"programmatic"`.

| Field | Type | Default | Accepted Values | Description |
|-------|------|---------|-----------------|-------------|
| `integration` | string | `null` | `zapier`, `composio`, `n8n`, `mcp` | Integration connector (optional) |
| `connector_config` | dict | `{}` | integration-specific key-values | Same fields as the matching external framework connector — see tables above |

**Validation rule:** `integration` is only valid when `agent_type` is `"programmatic"`.

When `integration` is set, `connector_config` is passed as `**kwargs` to the connector's `__init__`. Use the same fields as the matching framework in the tables above (zapier → zapier fields, mcp → mcp fields, etc.).

The common fields (`mode`, `callback_timeout`) are also available here — programmatic agents with connectors support the same sync/callback modes as external agents.

---

## WebhookConfig

Used inside `webhook_config` for human agents.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `outbound_url` | string | `null` | URL to POST responses to external system |
| `outbound_headers` | dict | `{}` | Headers for outbound webhook (key-value string pairs) |
| `outbound_timeout` | int | `30` | Timeout for outbound calls (seconds) |
| `inbound_endpoint` | string | `null` | Endpoint path for inbound responses (e.g. `"/webhook/human_contact"`). If not set, derived from entry points. |
| `inbound_auth_token` | string | `null` | Auth token for validating inbound requests |
| `response_mapping` | dict | `{}` | Field mapping for webhook response transformation |
| `max_retries` | int | `3` | Max retry attempts for failed outbound webhooks |
| `retry_delay` | int | `5` | Delay between retries (seconds) |

---

## ChannelConfig

Used inside `channels` dict for human agents. Keys are provider names.

### Supported Provider Keys

| Key | Provider |
|-----|----------|
| `slack` | Slack Bot API |
| `telegram` | Telegram Bot API |
| `discord` | Discord Bot API |
| `whatsapp` | WhatsApp Business API (Meta Cloud API) |
| `teams` | Microsoft Teams Bot Framework |
| `email` | SMTP outbound + Mailgun / SendGrid / Postmark inbound (BRD-020) — see [Email Channel](#email-channel) |

### Fields Per Channel

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `bot_token` | string | `null` | Bot/API token for the provider (see per-provider notes below) |
| `signing_secret` | string | `null` | Request verification secret (see per-provider notes below) |
| `listen_channels` | list | `[]` | Channel/chat IDs to accept inbound messages from (empty = all) |
| `post_channel` | string | `null` | Default channel/chat ID for outbound messages (see per-provider notes below) |
| `verify_token` | string | `null` | Webhook verification token — **WhatsApp only** (`hub.verify_token`) |

**Note:** `ChannelConfig` allows extra fields (`extra="allow"`) for any provider-specific config.

### Per-Provider Field Semantics

| Provider | `bot_token` | `signing_secret` | `post_channel` | `verify_token` |
|----------|------------|------------------|----------------|----------------|
| `slack` | Bot OAuth token (`xoxb-…`) | Slack signing secret (HMAC-SHA256) | Channel ID (e.g. `C123456`) | — |
| `telegram` | Bot token from @BotFather | Secret token set when registering webhook | Chat ID | — |
| `discord` | Bot token (without `Bot ` prefix) | App public key (Ed25519 — requires `pynacl`) | Channel ID | — |
| `whatsapp` | Meta Graph API access token | Meta app secret (HMAC-SHA256) | Phone number ID | `hub.verify_token` for webhook registration |
| `teams` | Bot Framework App ID | Bot Framework App password | Conversation ID | — |

### Inbound Route Registered Per Provider

| Provider | Route |
|----------|-------|
| `slack` | `POST /channels/slack/{agent_name}/events` |
| `telegram` | `POST /channels/telegram/{agent_name}/webhook` |
| `discord` | `POST /channels/discord/{agent_name}/interactions` |
| `whatsapp` | `GET /channels/whatsapp/{agent_name}/webhook` (verification) + `POST` (messages) |
| `teams` | `POST /channels/teams/{agent_name}/messages` |

### Example

```yaml
channels:
  slack:
    bot_token: "${SLACK_BOT_TOKEN:}"
    signing_secret: "${SLACK_SIGNING_SECRET:}"
    listen_channels: ["C123456", "C789012"]
    post_channel: "C123456"

  telegram:
    bot_token: "${TELEGRAM_BOT_TOKEN:}"
    signing_secret: "${TELEGRAM_SECRET_TOKEN:}"   # optional
    listen_channels: []                            # empty = all chats
    post_channel: ""

  discord:
    bot_token: "${DISCORD_BOT_TOKEN:}"
    signing_secret: "${DISCORD_PUBLIC_KEY:}"       # Ed25519 public key
    listen_channels: ["987654321098765432"]
    post_channel: "987654321098765432"

  whatsapp:
    bot_token: "${WHATSAPP_ACCESS_TOKEN:}"
    signing_secret: "${META_APP_SECRET:}"
    post_channel: "${WHATSAPP_PHONE_NUMBER_ID:}"   # phone number ID, not a phone number
    verify_token: "my_verify_token"                # set same value in Meta dashboard

  teams:
    bot_token: "${TEAMS_APP_ID:}"
    signing_secret: "${TEAMS_APP_PASSWORD:}"
    post_channel: ""                               # set at runtime from inbound activity
```

---

### Email Channel

The `email` provider has a strict schema (validated at YAML load time, not at first send). Inbound is webhook-based via Mailgun / SendGrid / Postmark; outbound is SMTP via `aiosmtplib`.

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `enabled` | bool | `true` | no | Set `false` to keep the block but disable the adapter |
| `provider` | string | `"mailgun"` | no | Inbound webhook provider: `mailgun`, `sendgrid`, `postmark` |
| `region` | string | `"us"` | no | Provider region: `us`, `eu` (Mailgun: `api.mailgun.net` vs `api.eu.mailgun.net`) |
| `signing_secret` | string | `null` | yes (inbound) | HMAC/ECDSA verification secret. Mailgun: HTTP webhook signing key. SendGrid: ECDSA P-256 verification key. Postmark: shared HMAC secret. |
| `inbound_domain` | string | `null` | no | Domain hosting inbound mail — used for plus-addressing (`agent+THREAD@inbound.example.com`) |
| `inbound_local_part_filter` | list | `[]` | no | Only process emails sent to these local parts (e.g. `["support", "help"]`); empty = accept all |
| `auto_reply_drop` | bool | `true` | no | Drop RFC 3834 auto-replies (Auto-Submitted, Precedence: bulk/list, noreply senders) |
| `smtp_host` | string | `null` | yes (when enabled) | Outbound SMTP hostname |
| `smtp_port` | int | `587` | no | SMTP port (587 STARTTLS, 465 implicit TLS) |
| `smtp_username` | string | `null` | no | SMTP auth username |
| `smtp_password` | string | `null` | no | SMTP auth password |
| `from_address` | string | `null` | yes (when enabled) | Default From: address |
| `reply_to_address` | string | `null` | no | Override Reply-To: header (defaults to from_address with plus-addressing token) |
| `use_starttls` | bool | `true` | no | Negotiate STARTTLS for SMTP submission |
| `subject_prefix` | string | `null` | no | Prefix for subjects, e.g. `"[#TICKET-{thread_id}]"` — used as fallback threading token when reference headers are stripped |
| `threading` | string | `"references_first"` | no | Thread mapping strategy: `references_first` (prefer `In-Reply-To`/`References` headers, fall back to plus-addressing) or `reply_to_token` (skip headers, plus-addressing only) |
| `attachments` | dict | see below | no | Inbound attachment handling — see [EmailAttachmentConfig](#emailattachmentconfig) |

**`EmailAttachmentConfig`** (under `channels.email.attachments`):

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `receive` | bool | `false` | Opt-in: surface inbound attachments to the agent. Off by default for security. |
| `max_size_mb` | int | `10` | Max accepted attachment size in MB (1–100) |
| `storage_url` | string | `null` | Object-storage URL (e.g. `s3://bucket/prefix`). Agent receives a presigned URL — never raw bytes. |

**Provider-specific signing notes:**

| Provider | Verification | Notes |
|----------|-------------|-------|
| `mailgun` | HMAC-SHA256 over `timestamp + token` | `signing_secret` = Mailgun's HTTP webhook signing key |
| `sendgrid` | ECDSA P-256 | `signing_secret` = base64 ECDSA verification key (Inbound Parse settings) |
| `postmark` | HTTP Basic Auth + IP allowlist | `signing_secret` = the shared HMAC secret; thread token comes from `MailboxHash` |

**Inbound route:** `POST /channels/email/{agent_name}/{provider}/inbound`

**Required when enabled:** `smtp_host` and `from_address` must be set or SDK startup fails. Set `enabled: false` to register the block without configuring outbound.

**Example:**

```yaml
agents:
  support_agent:
    name: "support_agent"
    agent_type: "human"
    channels:
      email:
        provider: "mailgun"
        region: "us"
        signing_secret: "${MAILGUN_SIGNING_KEY}"
        inbound_domain: "inbound.example.com"
        inbound_local_part_filter: ["support", "help"]
        auto_reply_drop: true
        smtp_host: "smtp.mailgun.org"
        smtp_port: 587
        smtp_username: "${MAILGUN_SMTP_USER}"
        smtp_password: "${MAILGUN_SMTP_PASSWORD}"
        from_address: "support@example.com"
        subject_prefix: "[#TICKET-{thread_id}]"
        threading: "references_first"
        attachments:
          receive: true
          max_size_mb: 25
          storage_url: "s3://example-attachments/inbound"
```

See **[Human Agents — Email Channel](../agents/human-agents#email-channel)** for end-to-end setup walkthroughs per provider.

---

## Memory Config

Field: `memory` — accepts `bool` or `dict`.

### Simple Mode

```yaml
memory: false   # Disabled (default)
memory: true    # Enabled with defaults
```

### Advanced Mode (Dict)

| Field | Type | Default | Accepted Values | Description |
|-------|------|---------|-----------------|-------------|
| `strategy` | string | `"recency"` | `recency`, `relevance`, `hybrid` | Memory retrieval strategy |
| `limit` | int | `10` | 1 – 100 | Max feed posts per invocation |
| `cross_session` | bool | `false` | `true`, `false` | Persist memory across sessions |
| `cross_session_limit` | int | `50` | 1 – 500 | Max cross-session posts to retain |
| `relevance_weight` | float | `0.6` | 0.0 – 1.0 | Weight for relevance scoring |
| `recency_weight` | float | `0.4` | 0.0 – 1.0 | Weight for recency scoring |
| `decay_hours` | int | `24` | 1 – unlimited | Hours before entries decay |

### Example

```yaml
memory:
  strategy: "hybrid"
  limit: 10
  cross_session: true
  cross_session_limit: 50
  relevance_weight: 0.6
  recency_weight: 0.4
  decay_hours: 24
```

---

## EscalationConfig

Used inside `manager.escalation`.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `targets` | list of [EscalationTarget](#escalationtarget) | `[]` | Escalation targets — all fire in parallel |
| `auto_escalate` | dict | see below | Auto-escalation rules |

### `auto_escalate` Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_retries` | int | `3` | Max retry attempts before escalating |
| `max_errors_per_session` | int | `5` | Error count threshold per session |
| `timeout_threshold` | int | `2` | Consecutive timeouts before escalating |

---

## EscalationTarget

Each target in the `escalation.targets` list.

| Field | Type | Default | Accepted Values | Applies To |
|-------|------|---------|-----------------|------------|
| `type` | string | **required** | `human_agent`, `webhook`, `channel` | all |
| `agent` | string | `null` | agent name | `human_agent` |
| `entry_point` | string | `null` | entry point name | `human_agent` |
| `url` | string | `null` | URL | `webhook` |
| `method` | string | `"POST"` | `POST`, `PUT`, `PATCH` | `webhook` |
| `headers` | dict | `{}` | key-value string pairs | `webhook` |
| `payload_template` | dict | `null` | JSON with `{{var}}` placeholders | `webhook` |
| `provider` | string | `null` | `slack`, `telegram`, `discord`, `whatsapp`, `teams` | `channel` |
| `channel_id` | string | `null` | channel ID | `channel` |
| `message_template` | string | `null` | text with `{{var}}` placeholders | `channel` |

### Example

```yaml
escalation:
  targets:
    - type: "human_agent"
      agent: "customer_support_team"

    - type: "webhook"
      url: "https://incident.example.com/api/escalate"
      method: "POST"
      headers:
        Authorization: "Bearer ${ESCALATION_TOKEN:}"
      payload_template:
        incident_id: "{{session_id}}"
        severity: "{{severity_level}}"
        message: "{{error_message}}"

    - type: "channel"
      provider: "slack"
      channel_id: "#critical-incidents"
      message_template: "Escalation: {{message}} (session: {{session_id}})"

  auto_escalate:
    max_retries: 3
    max_errors_per_session: 5
    timeout_threshold: 2
```

---

## BrokerConfig

Top-level `brokers:` is a registry of connections to external event sources. An agent's `listen_events:` references a broker by name. One broker connection serves any number of listeners on different topics/queues — same way Knative Brokers, Dapr Components, and Azure Functions `Connection=` work.

```yaml
brokers:
  prod_kafka:
    type: "kafka"
    bootstrap_servers: ["kafka-1:9092", "kafka-2:9092"]
    security_protocol: "SASL_SSL"
    sasl_mechanism: "SCRAM-SHA-512"
    sasl_username: "${KAFKA_USERNAME}"
    sasl_password: "${KAFKA_PASSWORD}"
    ssl_cafile: "/etc/ssl/certs/kafka-ca.pem"

  alerts_sqs:
    type: "sqs"
    region: "us-east-1"

  iot_mqtt:
    type: "mqtt"
    host: "mqtt.example.com"
    port: 8883
    use_tls: true
    username: "${MQTT_USERNAME}"
    password: "${MQTT_PASSWORD}"

  external_redis:
    type: "redis_streams"
    url: "rediss://upstream-redis.example.com:6380"
    db: 0

  support_imap:
    type: "imap"
    host: "imap.example.com"
    port: 993
    username: "support@example.com"
    password: "${IMAP_PASSWORD}"
    use_tls: true
```

The `type` discriminator selects the schema. Each subtype has its own field set — typos and wrong types fail at SDK startup, not at first message.

### KafkaBrokerConfig (`type: "kafka"`)

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `type` | string | `"kafka"` | yes | Discriminator |
| `bootstrap_servers` | list[string] | — | yes | Kafka broker addresses, e.g. `["kafka-1:9092"]` |
| `security_protocol` | string | `null` | no | `PLAINTEXT`, `SSL`, `SASL_PLAINTEXT`, `SASL_SSL` |
| `sasl_mechanism` | string | `null` | no | `PLAIN`, `SCRAM-SHA-256`, `SCRAM-SHA-512`, `GSSAPI` |
| `sasl_username` | string | `null` | no | SASL username |
| `sasl_password` | string | `null` | no | SASL password |
| `ssl_cafile` | string | `null` | no | Path to CA bundle for TLS |
| `ssl_certfile` | string | `null` | no | Client cert (mTLS) |
| `ssl_keyfile` | string | `null` | no | Client key (mTLS) |

### SQSBrokerConfig (`type: "sqs"`)

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `type` | string | `"sqs"` | yes | Discriminator |
| `region` | string | — | yes | AWS region, e.g. `"us-east-1"` |
| `aws_access_key_id` | string | `null` | no | Optional explicit key — otherwise IAM role / env credentials are used |
| `aws_secret_access_key` | string | `null` | no | Optional explicit secret |
| `aws_session_token` | string | `null` | no | STS session token (for assumed roles) |
| `endpoint_url` | string | `null` | no | Override endpoint (LocalStack, VPC endpoints) |

### MQTTBrokerConfig (`type: "mqtt"`)

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `type` | string | `"mqtt"` | yes | Discriminator |
| `host` | string | — | yes | MQTT broker hostname |
| `port` | int | `1883` | no | Port (`1883` plain, `8883` TLS) |
| `username` | string | `null` | no | MQTT username |
| `password` | string | `null` | no | MQTT password |
| `use_tls` | bool | `false` | no | Enable TLS |
| `client_id` | string | `null` | no | Client ID (random if unset) |
| `keepalive_s` | int | `60` | no | Keepalive interval in seconds |

### RedisStreamsBrokerConfig (`type: "redis_streams"`)

Distinct from the SDK's primary Redis (used for sessions/yields/feed). Use this when an upstream service writes events into a Redis stream that an agent should consume.

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `type` | string | `"redis_streams"` | yes | Discriminator |
| `url` | string | — | yes | `redis://`, `rediss://`, or `unix://` URL |
| `db` | int | `0` | no | Redis database number |

### IMAPBrokerConfig (`type: "imap"`)

For email-as-event-source when webhook-based email isn't viable (firewall, no public DNS). For webhook-based email channels on human agents, use `channels.email` instead.

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `type` | string | `"imap"` | yes | Discriminator |
| `host` | string | — | yes | IMAP server hostname |
| `port` | int | `993` | no | Port (`143` plain, `993` TLS) |
| `username` | string | — | yes | IMAP username (usually full email address) |
| `password` | string | — | yes | IMAP password or app-specific token |
| `use_tls` | bool | `true` | no | Use implicit TLS (port 993) |

---

## EventListener

A single entry in an agent's `listen_events:`. Each entry creates one long-lived asyncio task that consumes from the named broker and dispatches matching messages into the mesh as an entry-point event for the agent. All listeners use **at-least-once** delivery with idempotency keying on `(listener_name, message_id)` to prevent double-processing on retry.

```yaml
agents:
  order_processor:
    name: "order_processor"
    agent_type: "llm"
    listen_events:
      - broker: "prod_kafka"
        topic: "orders.new"
        group_id: "order-processor-v1"
        filter:
          type: "com.example.order.created"
        deserialize: "myapp.schemas:OrderEvent"
        delivery:
          max_attempts: 5
          backoff: "exponential"
          backoff_initial_s: 2.0
          backoff_max_s: 120.0
          dead_letter:
            broker: "prod_kafka"
            topic: "orders.dlq"
        batch_size: 10
```

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `broker` | string | — | yes | Name of an entry in the top-level `brokers:` block |
| `topic` | string | `null` | yes (Kafka) | Kafka topic to subscribe to |
| `group_id` | string | `null` | no | Kafka consumer group ID (defaults to `<sdk-name>-<agent-name>`) |
| `queue` | string | `null` | yes (SQS) | SQS queue URL or name |
| `stream` | string | `null` | yes (Redis Streams) | Redis stream key |
| `consumer_group` | string | `null` | no | Redis Streams consumer group |
| `mqtt_topic` | string | `null` | yes (MQTT) | MQTT topic filter (supports `+` and `#` wildcards) |
| `qos` | int | `1` | no | MQTT QoS level: `0` at-most-once, `1` at-least-once, `2` exactly-once |
| `folder` | string | `"INBOX"` | no | IMAP folder to monitor |
| `poll_interval_s` | float | `null` | no | Polling interval for IMAP / non-streaming sources |
| `filter` | dict | `null` | no | CloudEvents-style attribute equality. AND-semantics — all key/value pairs must match for the listener to fire. |
| `deserialize` | string | `null` | no | Pydantic class for payload validation, format `"module.path:ClassName"`. `ValidationError` routes the message to DLQ. |
| `delivery` | object | see [EventDeliverySpec](#eventdeliveryspec) | no | Retry + DLQ behavior |
| `batch_size` | int | `1` | no | Messages fetched per poll cycle (1–1000) |
| `visibility_heartbeat` | bool | `false` | no | (SQS only) Auto-extend the visibility timeout while a long-running agent handler executes |

### EventDeliverySpec

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_attempts` | int | `5` | Max delivery attempts before routing to DLQ (1–50) |
| `backoff` | string | `"exponential"` | `linear` or `exponential` |
| `backoff_initial_s` | float | `1.0` | Initial backoff delay in seconds |
| `backoff_max_s` | float | `60.0` | Cap on backoff delay |
| `dead_letter` | object | `null` | DLQ destination — see [DeadLetterRef](#deadletterref) |

### DeadLetterRef

Points at another broker (by name) and the destination shape on it. Only one of `topic`/`queue`/`stream` is meaningful per broker type — the listener validates the right one is set at startup.

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `broker` | string | — | yes | Name of a broker in the top-level `brokers:` block |
| `topic` | string | `null` | when broker is Kafka | Kafka DLQ topic name |
| `queue` | string | `null` | when broker is SQS | SQS DLQ queue URL or name |
| `stream` | string | `null` | when broker is Redis Streams | Redis Streams DLQ stream key |

### How Listeners Fire Agents

When a message arrives:

1. **Verify** — the listener verifies the source-specific signature/credentials at the connection layer.
2. **Filter** — `filter:` keys are matched against the normalized envelope. Non-match = ack and skip (no retry).
3. **Idempotency** — the runtime tracks `(listener_name, message_id)` to drop duplicate deliveries. If already processed, ack and skip.
4. **Deserialize** — if `deserialize:` is set, payload is validated through the named Pydantic class. `ValidationError` → DLQ (no retry — bad data won't fix itself).
5. **Wrap** — message is wrapped in a CloudEvents-shaped `TriggerEvent` envelope.
6. **Dispatch** — published as an `ENTRY_POINT` event for the agent. Same path as a `POST /webhook/{entry_point}`. Agent counts toward [BRD-012 invocation metering](../advanced/invocation-metering) like any other invocation.
7. **Ack** — on success, the source is acked (Kafka offset commit, SQS `DeleteMessage`, Redis `XACK`, etc.).
8. **Retry / DLQ** — on failure, the message is retried per `delivery.backoff` until `max_attempts`, then routed to `dead_letter` if configured.

See **[Event Listeners — Architecture](../multi-agent/event-listeners)** for an end-to-end walkthrough.

---

## Top-Level Config (LeafMeshConfig)

| Field | Type | Default | Accepted Values | Description |
|-------|------|---------|-----------------|-------------|
| `name` | string | `"default_mesh"` | any string | Mesh name |
| `version` | string | `"1.0.0"` | any string | Configuration version |
| `architecture` | string | `"managed_mesh"` | `managed_mesh` | Architecture type (only one supported) |
| `debug` | bool | `false` | `true`, `false` | Enable debug mode |
| `log_level` | string | `"INFO"` | `DEBUG`, `INFO`, `WARNING`, `ERROR` | Logging level |
| `environment` | string | `"development"` | `development`, `production` | Environment |
| `redis` | object | see [RedisConfig](#redisconfig) | — | Redis connection |
| `manager` | object | see [ManagerConfig](#managerconfig) | — | Manager coordination + analysis |
| `mesh` | object | see [MeshConfig](#meshconfig--cloud-providers) | — | Mesh network + cloud providers |
| `agents` | dict | `{}` | agent name → AgentConfig | Agent configurations |
| `entry_points` | list | `[]` (auto-populated with a default entry when none is provided) | see [Entry Points](#entry-points) | Named portals into mesh |
| `brokers` | dict | `{}` | broker name → [BrokerConfig](#brokerconfig) | Top-level connection definitions referenced by `agent.listen_events` (BRD-021) |
| `data_structures` | dict | `{}` | name → DataStructure | Custom data type definitions |
| `auto_discover` | dict | `null` | `{"directory": "path", "pattern": "*.py", "recursive": true}` | Auto-discover agent files |
| `evolution` | object | see [EvolutionConfig](#evolutionconfig) | — | Evolutionary optimization |

**Note:** `LeafMeshConfig` has `extra="forbid"` — unknown top-level keys will raise a validation error.

---

## ManagerConfig

| Field | Type | Default | Accepted Values | Description |
|-------|------|---------|-----------------|-------------|
| `enabled` | bool | `true` | `true`, `false` | Enable manager analysis |
| `model` | string | `"gpt-4o-mini"` | same as [Model List](#model-list) | LLM model for Manager analysis |
| `domain` | string | `"generic"` | `generic`, `ecommerce`, `data_analysis` | Manager domain specialization |
| `prompt` | string | `null` | any string (multiline supported) | **Evaluation criteria** — tell the Manager what success looks like, what to escalate on, and what patterns to watch. Injected into every Manager analysis pass as an `EVALUATION CRITERIA` section, alongside the domain prompt. |
| `can_intervene` | bool | `true` | `true`, `false` | Allow manager interventions (false = read-only) |
| `coordination_rules` | dict | `{}` | arbitrary key-values | User-defined business rules |
| `chain_completion_timeout` | float | `60.0` | seconds | Wait time before checking chain completeness |
| `health_check_interval` | int | `60` | seconds | Seconds between health checks |
| `agent_timeout_threshold` | int | `180` | seconds | Seconds before agent is timed out |
| `escalation` | object | `null` | see [EscalationConfig](#escalationconfig) | Escalation targets and rules |
| `routing` | dict | see below | — | Manager routing configuration |

### `manager.prompt` — Evaluation Criteria

Gives the Manager direct context about your mesh's specific purpose, success criteria, and escalation triggers. The Manager reads this on every agent turn alongside its domain template.

```yaml
manager:
  model: "gpt-4o-mini"
  domain: "generic"
  prompt: |
    This mesh handles customer support tickets.
    A successful flow means:
      - greeter identifies the issue category correctly
      - processor routes to the right specialist agent
      - the customer receives a clear resolution within 5 minutes

    Escalate if:
      - the same issue loops more than twice
      - sentiment is negative AND no resolution has been proposed
      - the human agent times out without responding

    Watch for:
      - advisor_agent confidence scores below 0.6
      - processor_agent routing to fallback more than 50% of the time
```

### `routing` Fields

| Field | Type | Default | Accepted Values | Description |
|-------|------|---------|-----------------|-------------|
| `mode` | string | `"static"` | `static`, `learning` | Routing mode (static=YAML only, learning=adaptive) |
| `memory_size` | int | `100` | 1 – 1000 | Max routing decisions to remember |
| `confidence_threshold` | float | `0.7` | 0.0 – 1.0 | Min confidence to accept learned route |
| `fallback` | string | `"all"` | `all` | Fallback when confidence too low |
| `decay_days` | int | `30` | 1 – 365 | Days before old routing memory decays |

### `human_input_rules` (Defaults)

| Field | Type | Default |
|-------|------|---------|
| `max_concurrent_requests` | int | `3` |
| `max_agent_requests` | int | `5` |
| `enable_request_queuing` | bool | `true` |

### `timeout_rules` (Defaults)

| Field | Type | Default |
|-------|------|---------|
| `max_timeouts_before_escalation` | int | `2` |
| `timeout_escalation_enabled` | bool | `true` |
| `escalation_notify_managers` | bool | `true` |

### `workflow_pause_rules` (Defaults)

| Field | Type | Default |
|-------|------|---------|
| `max_pause_duration_minutes` | int | `30` |
| `max_concurrent_paused_workflows` | int | `2` |
| `pause_monitoring_enabled` | bool | `true` |

### `human_response_rules` (Defaults)

| Scenario | `requires_manager_review` | `auto_escalate` |
|----------|--------------------------|-----------------|
| `approval` | `false` | `false` |
| `escalation` | `true` | `true` |
| `timeout` | `true` | `false` |

---

## MeshConfig & Cloud Providers

### MeshConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `call_timeout` | int | `30` | Call timeout in seconds |
| `bedrock` | object | `null` | AWS Bedrock config |
| `vertex` | object | `null` | Google Vertex AI config |
| `foundry` | object | `null` | Microsoft Foundry/Azure AI config |
| `local` | object | `null` | Local model server config (vLLM, SGLang, Ollama, etc.) |

### BedrockConfig (AWS)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `region` | string | `"us-east-1"` | AWS region |
| `profile` | string | `null` | AWS profile from `~/.aws/credentials` |
| `endpoint_url` | string | `null` | Custom Bedrock endpoint URL |

Auth: `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` env vars, IAM role, or `~/.aws/credentials`

### VertexConfig (Google Cloud)

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `project` | string | — | **yes** | GCP project ID |
| `location` | string | `"us-central1"` | no | GCP region |

Auth: `GOOGLE_APPLICATION_CREDENTIALS` env var or `gcloud auth`

### FoundryConfig (Azure)

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `endpoint` | string | — | **yes** | Foundry endpoint URL (e.g. `https://<resource>.openai.azure.com`) |
| `api_version` | string | `null` | no | Azure API version (e.g. `2024-10-21`). Omit for v1 endpoint. |

Auth: `AZURE_FOUNDRY_API_KEY` or `AZURE_FOUNDRY_TOKEN` env vars

### LocalModelConfig

| Field | Type | Default | Required | Description |
|-------|------|---------|----------|-------------|
| `endpoint` | string | `"http://localhost:11434/api/generate"` | no | Model server URL |
| `server_type` | string | `null` (auto-detect) | no | Server type: `openai`, `ollama`, `textgen`, `huggingface` |
| `timeout` | float | `120.0` | no | Request timeout in seconds |
| `headers` | dict | `{}` | no | Custom HTTP headers (e.g. for auth) |

Env fallbacks: `LOCAL_MODEL_ENDPOINT`, `LOCAL_MODEL_SERVER_TYPE`, `LOCAL_MODEL_TIMEOUT`

**Supported servers and their `endpoint` + `server_type`:**

| Server | `server_type` | Example `endpoint` |
|--------|--------------|-------------------|
| vLLM | `openai` | `http://localhost:8000/v1/chat/completions` |
| SGLang | `openai` | `http://localhost:30000/v1/chat/completions` |
| llama.cpp server | `openai` | `http://localhost:8080/v1/chat/completions` |
| LM Studio | `openai` | `http://localhost:1234/v1/chat/completions` |
| LocalAI | `openai` | `http://localhost:8080/v1/chat/completions` |
| TGI (--api openai) | `openai` | `http://localhost:8080/v1/chat/completions` |
| TensorRT-LLM | `openai` | `http://localhost:8000/v1/chat/completions` |
| Triton + vLLM | `openai` | `http://localhost:8000/v1/chat/completions` |
| Ollama | `ollama` | `http://localhost:11434/api/generate` |
| Text Gen Web UI | `textgen` | `http://localhost:5000/api/v1/generate` |
| HF Inference | `huggingface` | `https://api-inference.huggingface.co/models/...` |

> **Tip:** Most production servers (vLLM, SGLang, TGI, llama.cpp) expose OpenAI-compatible endpoints. Use `server_type: openai` for all of them. If `server_type` is omitted, it's auto-detected from the URL.

```yaml
mesh:
  local:
    endpoint: http://localhost:8000/v1/chat/completions
    server_type: openai
    timeout: 120
    headers:
      Authorization: "Bearer ${VLLM_API_KEY:}"
```

---

## RedisConfig

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `host` | string | `"localhost"` | Redis server host |
| `port` | int | `6379` | Redis server port |
| `db` | int | `0` | Redis database number |
| `password` | string | `null` | Redis password |
| `decode_responses` | bool | `true` | Decode Redis responses |
| `auto_storage` | bool | `true` | Enable automatic data storage |
| `default_ttl` | int | `3600` | Default TTL (seconds) |
| `session_ttl` | int | `7200` | Session TTL (seconds) |
| `cluster_mode` | bool | `false` | Use Redis cluster |
| `cluster_nodes` | list | `[]` | Cluster node addresses (strings) |
| `ssl` | bool | `false` | Enable TLS for Redis connection |
| `ssl_cert_reqs` | string | `"required"` | TLS verification mode: `required` \| `optional` \| `none` |
| `ssl_ca_certs` | string | `null` | Path to CA bundle for verifying Redis server cert |
| `ssl_certfile` | string | `null` | Client TLS cert path (mutual TLS) |
| `ssl_keyfile` | string | `null` | Client TLS private key path (mutual TLS) |
| `ssl_check_hostname` | bool | `true` | Verify server hostname against certificate |

---

## APIConfig

Top-level `api:` block Configures the LeafMesh HTTP server.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `cors_origins` | list[string] | `[]` | Additional CORS origins, appended to the built-in defaults (`https://platform.leafcraft.ai` + localhost dev ports). Each entry must be a full origin (`scheme://host[:port]`). |

---

## EvolutionConfig — removed from YAML

> **The `evolution:` YAML block was removed in v2.1.54.** Evolution
> now runs as a standalone co-located service — operators kick off
> runs from Studio with their test scenarios. There is no longer any
> YAML configuration surface for evolution.

If your existing config still has an `evolution:` block, it is
silently ignored at runtime (a one-time deprecation warning prints
at boot). You can leave it in place for backwards-compatibility or
delete it.

See [Evolutionary Optimization](../advanced/evolutionary-optimization)
for what evolution does and how to use it.

---

## DataStructure

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `type` | string | **required** | `object`, `string`, `number`, `boolean`, `list` |
| `properties` | dict | `null` | Object properties (for type=object) |
| `required` | list | `[]` | Required field names |
| `validation_rules` | dict | `{}` | Validation rules (key-value strings) |

---

## Entry Points

Each entry point is a named portal into the mesh.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | **required** | Entry point name |
| `target` | string | **required** | Target agent name |
| `description` | string | optional | Description |
| `condition` | string | `"always"` | Trigger condition |

### Example

```yaml
entry_points:
  - name: "greet_user"
    target: "greeter_agent"
    description: "Main entry — greets user and starts the agent chain"
  - name: "direct_research"
    target: "researcher_agent"
    description: "Skip greeting, go straight to research"
```

---

## Validation Rules

These are enforced at config load:

| Rule | Constraint |
|------|-----------|
| `agent_type` | Must be `llm`, `human`, `programmatic`, or `external` |
| `communication_type` | Must be `dual`, `chain`, or `execute` |
| `optimization_strategy` | Must be `performance`, `cost`, or `speed` (or null) |
| `max_tool_calls_per_message` | Must be 0–20 |
| `tool_call_timeout` | Must be > 0 and <= 300 seconds |
| `tool_choice` | Must be a non-empty string (`auto`, `none`, or tool name) |
| `framework` | Must be `crewai`, `langgraph`, `autogen`, `a2a`, `mcp`, `zapier`, `composio`, `n8n`, `custom` (or null) |
| `framework` required | When `agent_type` is `external`, `framework` must be set |
| `integration` | Must be `zapier`, `composio`, `n8n`, `mcp` (or null) |
| `integration` restricted | Only valid when `agent_type` is `programmatic` |
| `is_human_powered` sync | Auto-set to `true` when `agent_type="human"`, forced to `false` when `agent_type="llm"` |
| `AgentConfig` extras | Allows arbitrary extra fields (`extra="allow"`) |
| `LeafMeshConfig` extras | Rejects unknown top-level keys (`extra="forbid"`) |

---

## Field Applicability by Agent Type

Shows which fields are **used** (U), **ignored** (—), or **required** (R) for each agent type.

| Field | `llm` | `human` | `programmatic` | `external` |
|-------|-------|---------|----------------|------------|
| `name` | R | R | R | R |
| `description` | U | U | U | U |
| `model` | U | — | — | — |
| `prompt` | U | — | — | — |
| `temperature` | U | — | — | — |
| `max_tokens` | U | — | — | — |
| `max_completion_tokens` | U | — | — | — |
| `reasoning` | U | — | — | — |
| `thinking` | U | — | — | — |
| `thinking_budget` | U | — | — | — |
| `enable_prompt_caching` | U | — | — | — |
| `optimization_strategy` | U | — | — | — |
| `context_parts` | U | — | — | — |
| `tools` | U | — | — | — |
| `tool_choice` | U | — | — | — |
| `max_tool_calls_per_message` | U | — | — | — |
| `tool_call_timeout` | U | — | — | — |
| `allow_parallel_tool_calls` | U | — | — | — |
| `tool_categories` | U | — | — | — |
| `is_human_powered` | — | auto | — | — |
| `human_interface` | — | U | — | — |
| `human_timeout_seconds` | — | U | — | — |
| `human_context_template` | — | U | — | — |
| `human_prompt_template` | — | U | — | — |
| `fallback_on_timeout` | — | U | — | — |
| `fallback_response` | — | U | — | — |
| `require_human_confirmation` | — | U | — | — |
| `human_escalation_triggers` | — | U | — | — |
| `webhook_config` | — | U | — | — |
| `channels` | — | U | — | — |
| `framework` | — | — | — | R |
| `connector_config` | — | — | — | U |
| `integration` | — | — | U | — |
| `communication_type` | U | U | U | U |
| `parallel` | U | U | U | U |
| `max_concurrent` | U | U | U | U |
| `wake_up` | U | U | U | U |
| `yields` | U | U | U | U |
| `inputs` | U | U | U | U |
| `can_call` | U | U | U | U |
| `narration` | U | U | U | U |
| `knowledge` | U | U | U | U |
| `wait_for` | U | U | U | U |
| `wait_for_timeout` | U | U | U | U |
| `auto_store_response` | U | U | U | U |
| `auto_store_yields` | U | U | U | U |
| `memory` | U | U | U | U |

**Legend:** R = required, U = used, — = ignored, auto = auto-set
