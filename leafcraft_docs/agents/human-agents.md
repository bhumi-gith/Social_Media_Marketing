# Human Agents

Human agents are full mesh nodes that delegate execution to a real person via webhook. The mesh treats human responses identically to LLM responses — they have yields, can_call rules, and condition evaluation.

## Configuration

```yaml
agents:
  approver:
    name: "approver"
    agent_type: "human"
    is_human_powered: true
    human_interface: "api"
    human_timeout_seconds: 300
    communication_type: "dual"
    webhook_config:
      outbound_url: "https://your-dashboard.example.com/review-needed"
      outbound_headers:
        Authorization: "Bearer ${WEBHOOK_TOKEN}"
        Content-Type: "application/json"
      outbound_timeout: 30
      inbound_endpoint: "/webhook/process_request"
      inbound_auth_token: "${WEBHOOK_AUTH_TOKEN}"
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

## How It Works

Human agents use a single unified webhook endpoint: `POST /webhook/{entry_point}`. The same URL handles both new tasks and human responses — routing is automatic based on whether the body contains a `session_id` matching a paused workflow.

### Two Flows, One Endpoint

**Flow 1 — External system starts a new task:**
```
Slack/Zapier → POST /webhook/greet_user
Body: {"message": "Hello, I need help"}

LeafMesh: no session_id → looks up entry point "greet_user" → starts workflow
Response: {"status": "accepted", "session_id": "wh_greet_user_..."}
```

**Flow 2 — Human responds to a paused workflow:**
```
Earlier: mesh routed to human agent → sent outbound webhook
         with session_id and context → mesh PAUSED

Now: Human decides and sends response
POST /webhook/greet_user
Header: X-LeafMesh-Signature: sha256=<HMAC-SHA256>
Body: {"session_id": "abc-123", "decision": "approved", "notes": "Looks good"}

LeafMesh: session_id matches paused session → RESUMES workflow
Response: {"status": "resumed", "session_id": "abc-123", "agent": "approver"}
```

### Step-by-Step (Mid-Flow Human Review)

```
LLM Agent (analyzer, processor, etc.)
    │ can_call → human agent
    ▼
Human Agent triggered
    │
    ├── 1. Outbound webhook POST to outbound_url
    │      Payload: session_id, input_data, conversation_history, timeout
    │
    ├── 2. Flow PAUSES — Redis expectation key set
    │      (API returns the upstream agent's result immediately)
    │
    ├── 3. Human reviews data in your system (dashboard, Slack, email)
    │
    ├── 4. Human responds: POST /webhook/{entry_point}
    │      Header: X-LeafMesh-Signature: sha256=<HMAC>
    │      Body: {"session_id": "...", "decision": "approved"}
    │
    ├── 5. LeafMesh verifies HMAC → finds pending session → resumes
    │
    ├── 6. can_call evaluated against human's response
    │      decision == 'approved' → executor
    │      decision == 'rejected' → rejection_handler
    │
    └── 7. If no response within timeout → HUMAN_INPUT_TIMEOUT event
```

## Configuration Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `agent_type` | string | `"llm"` | Must be `"human"` |
| `is_human_powered` | boolean | false | Must be `true` |
| `human_interface` | string | `"api"` | Interface type: `"api"`, `"webhook"`, `"custom"` |
| `human_timeout_seconds` | int | 300 | Timeout in seconds before `HUMAN_INPUT_TIMEOUT` fires |
| `communication_type` | string | `"dual"` | `"dual"` (async — send webhook, return immediately, wait for inbound) or `"chain"` (blocking — wait for response before returning) |
| `fallback_on_timeout` | boolean | false | Use `fallback_response` values when timeout occurs |
| `fallback_response` | map | — | Default response values on timeout (e.g. `decision: "timeout"`) |

### Webhook Config Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `outbound_url` | string | — | URL to POST the review request to (your dashboard, Slack, etc.) |
| `outbound_headers` | map | — | HTTP headers for outbound requests |
| `outbound_timeout` | int | 30 | Timeout in seconds for outbound webhook delivery |
| `inbound_endpoint` | string | — | The webhook path for human responses (e.g. `/webhook/greet_user`) |
| `inbound_auth_token` | string | — | Optional Bearer token for authenticating inbound responses |
| `max_retries` | int | 3 | Max retry attempts for outbound webhook delivery |
| `retry_delay` | int | 5 | Base delay in seconds between retries (exponential backoff) |

## Outbound Webhook Payload

When the flow reaches a human agent, LeafMesh sends this payload to `outbound_url`:

```json
{
  "agent_name": "approver",
  "session_id": "fa44356e-66dc-4cb6-8dc9-be7512c78a9f",
  "timestamp": "2026-03-31T15:48:06.123456",
  "input_data": {
    "summary": "Q1 budget analysis complete",
    "flagged_items": ["marketing_budget"],
    "_agent_name": "analyzer"
  },
  "context": {
    "session_id": "fa44356e-...",
    "agent_name": "approver",
    "agent_type": "human"
  },
  "conversation_history": [
    {"role": "user", "content": "Review Q1 budget", "agent": null},
    {"role": "assistant", "content": "{...}", "agent": "analyzer"}
  ],
  "response_endpoint": "/webhook/process_request",
  "timeout_seconds": 300
}
```

## Inbound Response Format

The human's response must include `session_id`. All other fields are used for `can_call` condition evaluation:

```json
{
  "session_id": "fa44356e-66dc-4cb6-8dc9-be7512c78a9f",
  "decision": "approved",
  "notes": "Budget approved with note about 12% marketing increase"
}
```

The response must be signed with HMAC-SHA256:
```
X-LeafMesh-Signature: sha256=<HMAC-SHA256 hex digest of request body>
```

Inbound webhook requests are signed; rotate the signing secret from the LeafMesh settings panel.

## Conversation History in the Payload

Human agents have always shipped the last few conversation turns in
the webhook body so the human reviewer has context. Pre-v2.2.1 this
was hardcoded to 5 turns. From v2.2.1 onward it's configurable per
agent:

```yaml
agents:
  client:
    name: "client"
    agent_type: "human"
    receive_conversation_history: true
    history_limit: 30        # default 20, range 1-200
    webhook_config:
      url: "https://example.com/hitl"
```

**Backwards-compatibility note:** Human agents that have NOT set
`receive_conversation_history: true` continue to use the legacy
5-turn cap — your existing HITL integrations keep working unchanged.
Flip the flag to take advantage of the new `history_limit` range
(1–200).

Both the built-in HITL queue (the in-app Studio panel) and outbound
webhook payloads honour the same cap. The Studio "Inputs & Outputs"
panel and Playground inspector expose a single toggle for it.

## HITL Event Lifecycle

| Event | When |
|-------|------|
| `HUMAN_INPUT_REQUESTED` | Outbound webhook sent |
| `HUMAN_INPUT_RECEIVED` | Human provides a response via inbound webhook |
| `HUMAN_INPUT_TIMEOUT` | Human does not respond within timeout |
| `WORKFLOW_PAUSED` | Flow paused for human input |
| `WORKFLOW_RESUMED` | Flow resumed after human responds |
| `HUMAN_ESCALATION` | Manager escalates to human intervention |

The Manager subscribes to all HITL events. On timeout, it takes configured actions: retry, escalate, fallback, or stop.

## Native Channel Adapters

Beyond webhooks, human agents support **native channel adapters** for messaging platforms. Adapters handle inbound routing, outbound notifications, and session mapping automatically.

### Slack Adapter

```yaml
agents:
  human_support:
    name: "human_support"
    agent_type: "human"
    is_human_powered: true
    human_timeout_seconds: 600
    channels:
      slack:
        bot_token: "${SLACK_BOT_TOKEN}"
        signing_secret: "${SLACK_SIGNING_SECRET}"
        listen_channels:
          - "C0123456789"
        post_channel: "C0123456789"
```

### Channel Configuration

| Field | Type | Description |
|-------|------|-------------|
| `bot_token` | string | Slack bot token (starts with `xoxb-`). Use env vars. |
| `signing_secret` | string | Slack signing secret for request verification |
| `listen_channels` | array | Channel IDs to monitor for inbound messages |
| `post_channel` | string | Default channel for outbound messages |

### How Inbound Messages Are Routed

```
Slack message arrives
    │
    ├── Is there a pending webhook expectation for this user?
    │   └── Yes → Resume the existing session (human response)
    │
    ├── Is this human agent an entry point?
    │   └── Yes → Start a new session flow
    │
    └── Otherwise → Acknowledged but not processed
```

### Using Channels with Escalation Targets

```yaml
manager:
  escalation:
    targets:
      - type: "channel"
        provider: "slack"
        channel_id: "C0123456789"
        message_template: "Escalation: {{issue}} for customer {{customer_id}}"
```

## Timeout Handling

When the human doesn't respond within `human_timeout_seconds`:

```yaml
agents:
  approver:
    agent_type: "human"
    human_timeout_seconds: 300
    fallback_on_timeout: true
    fallback_response:
      decision: "timeout_default"
      message: "Request timed out — auto-escalated"
```

Timeout strategies:
- **Retry**: Send the request again to the same reviewer
- **Fallback**: Use `fallback_response` values and continue the chain
- **Escalate**: Route to a different human or Manager escalation target
- **Stop**: End the chain

## Email Channel

Email is a first-class channel — same model as Slack/Discord/Teams. Inbound mail arrives via a webhook from your email service provider, gets parsed + verified + threaded to a session, and is routed to the human agent. Outbound replies are sent over SMTP.

### When to Use

- Customer support inboxes (`support@yourcompany.com`)
- Approval requests where the reviewer prefers email over a dashboard
- Any case where the counterparty cannot install an app or sign into a portal

### Configuration

Add `channels.email` to a human agent. The full field reference is at **[Email Channel — ChannelConfig](../api-reference/agent-config-fields#email-channel)**.

```yaml
agents:
  email_responder:
    name: "email_responder"
    agent_type: "human"
    is_human_powered: true
    yields:
      reply: "string"
      decision: "string"
    channels:
      email:
        provider: "mailgun"             # mailgun | sendgrid | postmark
        region: "us"
        signing_secret: "${MAILGUN_SIGNING_KEY}"
        inbound_domain: "inbound.example.com"
        smtp_host: "smtp.mailgun.org"
        smtp_username: "${MAILGUN_SMTP_USER}"
        smtp_password: "${MAILGUN_SMTP_PASSWORD}"
        from_address: "support@example.com"
        subject_prefix: "[#TICKET-{thread_id}]"
```

### How Threading Works

The adapter threads inbound replies to the same session as the original conversation using two complementary mechanisms:

1. **Standard email headers** — `In-Reply-To` and `References` are the spec-defined way clients chain replies. The adapter tries these first.
2. **Plus-addressing reply token** — outbound mail is sent with `Reply-To: support+THREAD123@inbound.example.com`. When the user replies, the local part `support+THREAD123` carries the thread ID even when the client strips reply headers.
3. **Subject-token fallback** — if `subject_prefix` is set (e.g. `"[#TICKET-{thread_id}]"`), the adapter parses the thread ID out of the subject as a last-resort match.

Choose the strategy with the `threading` field:
- `references_first` (default) — try headers first, fall back to plus-addressing, then subject token.
- `reply_to_token` — skip headers, rely solely on plus-addressing. Use this when you don't trust upstream MTAs to preserve headers.

The thread token embedded in `Reply-To` is sanitized: `\r`, `\n`, `\x00`, and `@` are stripped to prevent header injection.

### Auto-Reply Filtering

`auto_reply_drop: true` (default) silently drops:

- Messages with `Auto-Submitted:` header set to anything other than `no`
- Messages with `Precedence:` set to `bulk`, `list`, `junk`, or `auto_reply` (matches any token in a multi-value header like `Precedence: bulk, list`)
- Senders matching common no-reply patterns (`noreply@`, `no-reply@`, `donotreply@`, etc.)

This prevents out-of-office replies, mailing list bounces, and vacation responders from creating noise sessions.

### Provider Setup

#### Mailgun

1. Configure an inbound route in Mailgun: `match_recipient(".*@inbound.example.com")` → forward to `https://your-leafmesh.example.com/channels/email/{agent_name}/mailgun/inbound`.
2. Get the **HTTP webhook signing key** from Mailgun → `Settings → Webhooks → HTTP webhook signing key`. Set as `signing_secret`.
3. Inbound requests are verified using Mailgun's signing scheme; stale / replayed requests are rejected.
4. SMTP credentials come from `Sending → Domain settings → SMTP credentials`. Use port 587 with STARTTLS.

#### SendGrid

1. Configure **Inbound Parse**: domain `inbound.example.com` → POST URL `https://your-leafmesh.example.com/channels/email/{agent_name}/sendgrid/inbound`. Enable **Check incoming emails for spam** but do not enable **Send Raw**.
2. Generate an **ECDSA P-256 verification key** (Settings → Mail Settings → Event Webhook → Signed Event Webhook). Paste the public key (PEM, base64) as `signing_secret`.
3. Outbound: use SendGrid SMTP relay (`smtp.sendgrid.net:587`) with API key as the SMTP password and `apikey` as the username.

#### Postmark

1. Create an **Inbound stream** with the inbound domain. Postmark POSTs to `https://your-leafmesh.example.com/channels/email/{agent_name}/postmark/inbound`.
2. Verification is HTTP Basic Auth — set the username/password under stream settings and configure the same on your reverse proxy or set `signing_secret` to the Basic Auth shared secret. Optionally restrict the inbound webhook by IP allowlist (Postmark publishes the source IPs).
3. Postmark's `MailboxHash` field carries the plus-addressing token (`support+THREAD123@inbound.example.com` → `MailboxHash="THREAD123"`). Threading uses this even when DNS routing strips the local part.
4. Outbound: Postmark SMTP (`smtp.postmarkapp.com:587`) with the server token as both username and password.

### Inbound Attachments (Opt-In)

Attachments are dropped by default. To surface them:

```yaml
channels:
  email:
    # ...
    attachments:
      receive: true
      max_size_mb: 25
      storage_url: "s3://example-attachments/inbound"
```

When enabled, attachments are uploaded to `storage_url` and the agent receives **presigned URLs** in `input_data.attachments` — never raw bytes. This caps memory pressure and keeps PII out of agent context windows.

### Webhook Endpoint Reference

| Provider | Inbound URL |
|----------|-------------|
| `mailgun` | `POST /channels/email/{agent_name}/mailgun/inbound` |
| `sendgrid` | `POST /channels/email/{agent_name}/sendgrid/inbound` |
| `postmark` | `POST /channels/email/{agent_name}/postmark/inbound` |

Request signatures are verified before the body is parsed. Requests that fail verification return `401` and never reach the agent.

## When to Use Human Agents

- Approval workflows (refunds, deployments, access requests)
- Quality review for high-stakes LLM outputs
- Escalation endpoints for critical incidents
- Compliance checkpoints requiring human judgment
- Any decision that should not be fully automated

## Next Steps

- **[Agent Types](overview)** — All four agent types
- **[HITL Workflows](../human-in-loop/workflows)** — Tested approval patterns
- **[UI Integration](../human-in-loop/ui-integration)** — Building review interfaces
- **[Manager — Escalation](../core-concepts/manager)** — Multi-target escalation

---

*LeafMesh — Human judgment as a first-class mesh node*
