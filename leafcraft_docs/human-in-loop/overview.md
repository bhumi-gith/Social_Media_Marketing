# Human-in-the-Loop Overview

Human-in-the-Loop (HITL) is a first-class feature in LeafMesh. Human agents are full mesh nodes — they have yields, can_call rules, and condition evaluation — but route execution to a person instead of a model.

## How It Works

```yaml
agents:
  human_reviewer:
    name: "human_reviewer"
    agent_type: "human"
    is_human_powered: true
    human_interface: "api"
    human_timeout_seconds: 300
    communication_type: "dual"
    webhook_config:
      outbound_url: "https://your-dashboard.example.com/review-needed"
      outbound_headers:
        Content-Type: "application/json"
      outbound_timeout: 30
      inbound_endpoint: "/webhook/process_request"
      max_retries: 3
      retry_delay: 5
    yields:
      decision: "string"
      notes: "string"
    can_call:
      - agent: "executor"
        condition: "decision == 'approved'"
      - agent: "rejection_handler"
        condition: "decision == 'rejected'"
```

When the mesh routes to a human agent:

1. LeafMesh sends an **outbound webhook** to the configured `outbound_url`
2. The payload includes the upstream agent's output, session_id, conversation history, and timeout
3. The flow **pauses**, waiting for the human's response
4. The human reviews the data and responds via `POST /webhook/{entry_point}` with the `session_id`
5. LeafMesh verifies the HMAC signature, matches the pending session, and resumes the flow
6. `can_call` conditions are evaluated against the human's response
7. Downstream agents fire based on the human's decision

## Complete Flow

```
mesh_call("entry_point", data)
    │
    ▼
LLM Agent (greeter, processor, etc.)
    │ can_call → human agent
    ▼
Human Agent triggered
    │
    ├── 1. Outbound webhook → your system (Slack, dashboard, email)
    │      Payload: session_id, input_data, conversation_history, timeout
    │
    ├── 2. Flow PAUSES, awaiting the human response
    │      (mesh_call returns greeter's result immediately)
    │
    ├── 3. Human reviews data in your system
    │
    ├── 4. Human responds: POST /webhook/{entry_point}
    │      Header: X-LeafMesh-Signature: sha256=<HMAC>
    │      Body: {"session_id": "...", "decision": "approved", "message": "..."}
    │
    ├── 5. LeafMesh verifies signature, finds the pending session
    │      Status: "resumed" (not "accepted")
    │
    ├── 6. can_call evaluated against response
    │      decision == 'approved' → executor agent
    │      decision == 'rejected' → rejection_handler
    │
    └── 7. Downstream chain continues automatically
```

## HMAC Webhook Signing

All webhook traffic (inbound and outbound) is HMAC-SHA256 signed. Rotate the signing secret from your LeafMesh settings panel and load it into your code from an environment variable:

```python
import os

secret = os.environ["LEAFMESH_WEBHOOK_SECRET"]
```

Sign inbound requests with the `X-LeafMesh-Signature` header:

```
X-LeafMesh-Signature: sha256=<HMAC-SHA256 hex digest of request body>
```

## HITL Event Lifecycle

Events published during human agent execution:

| Event | When |
|-------|------|
| `HUMAN_INPUT_REQUESTED` | Outbound webhook sent, waiting for human |
| `HUMAN_INPUT_RECEIVED` | Human responds via inbound webhook |
| `HUMAN_INPUT_TIMEOUT` | Human doesn't respond within timeout |
| `WORKFLOW_PAUSED` | Flow paused waiting for human input |
| `WORKFLOW_RESUMED` | Flow resumed after human responds |
| `HUMAN_ESCALATION` | Manager escalates to human intervention |

The Manager subscribes to all HITL events. On timeout, it takes configured actions: retry, route to fallback, escalate, or stop the chain.

## Key Properties

- **Full mesh node**: Human agents participate in can_call chains, fan-in/fan-out, and condition routing identically to LLM agents
- **YAML-only integration**: Add human review by adding a human agent to config — no code changes needed
- **Webhook-native**: Outbound notification + inbound response via standard HTTP webhooks
- **HMAC-signed**: All webhook traffic is cryptographically signed
- **Configurable timeout**: Default 300 seconds, configurable per agent
- **Two communication modes**: `"dual"` (async, non-blocking) or `"chain"` (blocking, waits for response)

## Next Steps

- **[Approval Workflows](workflows)** — Multi-step approval patterns with tested examples
- **[UI Integration](ui-integration)** — Building review interfaces with actual webhook payloads
- **[Notifications](notifications)** — Alert systems for human reviewers
- **[Human Agents Reference](../agents/human-agents)** — Full configuration reference

---

*LeafMesh — Human agents as first-class mesh nodes*
