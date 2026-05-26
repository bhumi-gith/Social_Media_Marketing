# HITL Workflows

Build workflows where AI agents pause for human review, approval, or input before continuing.

## Mid-Flow Human Review

The most common pattern: an LLM agent processes a request, routes to a human for review, then the human's decision drives the next step.

### Configuration

```yaml
name: "budget_review"
architecture: "managed_mesh"

entry_points:
  - name: "review_budget"
    target: "analyzer"

agents:
  analyzer:
    name: "analyzer"
    agent_type: "llm"
    model: "gpt-4o-mini"
    communication_type: "dual"
    prompt: |
      Analyze the budget data and prepare a structured review summary.
      Flag any line items that exceed 10% variance from last quarter.
    yields:
      summary: "string"
      flagged_items: "list"
      total_variance: "number"
    can_call:
      - agent: "human_reviewer"

  human_reviewer:
    name: "human_reviewer"
    agent_type: "human"
    is_human_powered: true
    human_interface: "api"
    human_timeout_seconds: 600
    communication_type: "dual"
    webhook_config:
      outbound_url: "https://your-app.example.com/review-needed"
      outbound_headers:
        Content-Type: "application/json"
      outbound_timeout: 30
      inbound_endpoint: "/webhook/review_budget"
      max_retries: 3
      retry_delay: 5
    yields:
      decision: "string"
      notes: "string"
    can_call:
      - agent: "submitter"
        condition: "decision == 'approved'"
      - agent: "revision_handler"
        condition: "decision == 'revision_needed'"

  submitter:
    name: "submitter"
    agent_type: "programmatic"
    yields:
      status: "string"
      confirmation_id: "string"

  revision_handler:
    name: "revision_handler"
    agent_type: "programmatic"
    yields:
      notification_sent: "boolean"
```

### What Happens

```
POST /api/mesh/request
  {"entry_point": "review_budget", "data": {"message": "Review Q1 budget"}}

1. analyzer (LLM) runs → produces summary + flagged items
2. can_call routes to human_reviewer
3. LeafMesh sends outbound webhook to your-app.example.com/review-needed
4. Flow PAUSES — mesh_call returns analyzer's result immediately

   --- Human reviews in your dashboard ---

5. Human responds: POST /webhook/review_budget
   {"session_id": "...", "decision": "approved", "notes": "Looks good"}

6. LeafMesh resumes → evaluates can_call → routes to submitter
7. submitter runs → budget submitted
```

### Testing the Flow

```bash
# Step 1: Trigger the workflow
curl -X POST http://127.0.0.1:18820/api/mesh/request \
  -H "Content-Type: application/json" \
  -d '{"entry_point": "review_budget", "data": {"message": "Review Q1 budget"}}'
# Returns: {"status": "completed", "session_id": "abc-123", ...}

# Step 2: Load your webhook signing secret from the environment
#   import os
#   secret = os.environ["LEAFMESH_WEBHOOK_SECRET"]
# (header: X-LeafMesh-Signature, format: sha256=<HMAC-SHA256 hex digest>)

# Step 3: Respond as the human.
#
# Inbound webhooks are HMAC-SHA256 signed and bound to a fresh
# timestamp + nonce so captured signed requests cannot be replayed.
# Three headers are required:
#   - X-LeafMesh-Signature  : sha256=<hex>
#   - X-LeafMesh-Timestamp  : Unix seconds
#   - X-LeafMesh-Nonce      : 8–128 chars [A-Za-z0-9_-], unique per request
#
# Signed material: `f"{timestamp}.{nonce}.".encode() + body`

BODY='{"session_id": "abc-123", "decision": "approved", "notes": "Budget approved"}'
SECRET="YOUR_SECRET"
TS=$(date +%s)
NONCE=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')
SIG=$(printf '%s' "$TS.$NONCE.$BODY" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $NF}')

curl -X POST http://127.0.0.1:18820/webhook/review_budget \
  -H "Content-Type: application/json" \
  -H "X-LeafMesh-Signature: sha256=$SIG" \
  -H "X-LeafMesh-Timestamp: $TS" \
  -H "X-LeafMesh-Nonce: $NONCE" \
  -d "$BODY"
# Returns: {"status": "resumed", "session_id": "abc-123", "agent": "human_reviewer"}
```

Key response statuses:
- `"resumed"` — LeafMesh found the pending session and resumed the flow
- `"accepted"` — No pending session found, treated as a new request

## Conditional Approval

Route to human review only when thresholds are exceeded:

```yaml
agents:
  processor:
    name: "processor"
    model: "gpt-4o"
    yields:
      recommendation: "string"
      risk_level: "string"
      amount: "number"
    can_call:
      - agent: "human_reviewer"
        condition: "amount > 1000 or risk_level == 'high'"
      - agent: "auto_approve"
        condition: "amount <= 1000 and risk_level != 'high'"
```

Low-risk items bypass human review entirely. High-risk items pause for human judgment.

## Multi-Level Approvals

Chain multiple human agents for escalating approval levels:

```yaml
agents:
  team_lead:
    name: "team_lead"
    agent_type: "human"
    is_human_powered: true
    human_timeout_seconds: 300
    webhook_config:
      outbound_url: "https://your-app.example.com/team-lead-review"
      inbound_endpoint: "/webhook/approve"
    can_call:
      - agent: "executor"
        condition: "decision == 'approved' and amount <= 10000"
      - agent: "director"
        condition: "decision == 'approved' and amount > 10000"
      - agent: "rejection_handler"
        condition: "decision == 'rejected'"

  director:
    name: "director"
    agent_type: "human"
    is_human_powered: true
    human_timeout_seconds: 1800
    webhook_config:
      outbound_url: "https://your-app.example.com/director-review"
      inbound_endpoint: "/webhook/approve"
    can_call:
      - agent: "executor"
        condition: "decision == 'approved'"
```

Each level has its own webhook, timeout, and routing conditions.

## Timeout Handling

When a human doesn't respond within the timeout:

```yaml
agents:
  human_reviewer:
    agent_type: "human"
    human_timeout_seconds: 300
    fallback_on_timeout: true
    fallback_response:
      decision: "timeout_default"
      message: "Request timed out — auto-escalated"
```

The `HUMAN_INPUT_TIMEOUT` event triggers Manager coordination:
- **Retry**: Send the request again
- **Escalate**: Route to a different human reviewer or Manager escalation target
- **Fallback**: Use `fallback_response` values and continue the chain
- **Stop**: Halt the workflow

## Human as Initiator

A human agent can also be the **entry point** — the person who starts workflows:

```yaml
agents:
  client:
    name: "client"
    agent_type: "human"
    is_human_powered: true
    human_interface: "api"
    webhook_config:
      inbound_endpoint: "/webhook/start"
    can_call:
      - agent: "greeter_agent"
```

```bash
# Human initiates via webhook
curl -X POST http://127.0.0.1:18820/webhook/start \
  -H "Content-Type: application/json" \
  -H "X-LeafMesh-Signature: sha256=..." \
  -d '{"message": "I need help with my account"}'
```

## Next Steps

- **[UI Integration](ui-integration)** — Building review interfaces with actual webhook payloads
- **[Notifications](notifications)** — Alert systems
- **[Human Agents Reference](../agents/human-agents)** — Full configuration reference

---

*LeafMesh — Structured approval workflows with human judgment*
