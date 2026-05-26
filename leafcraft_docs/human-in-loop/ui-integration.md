# UI Integration

Patterns for building user interfaces that integrate with LeafMesh's human-in-the-loop system.

## Outbound Webhook Payload

When the mesh routes to a human agent, LeafMesh sends an outbound webhook to your configured `outbound_url`. The payload contains everything the reviewer needs:

```json
{
  "agent_name": "human_reviewer",
  "session_id": "fa44356e-66dc-4cb6-8dc9-be7512c78a9f",
  "timestamp": "2026-03-31T15:48:06.123456",
  "input_data": {
    "summary": "Q1 budget analysis complete. Marketing spend up 12%.",
    "flagged_items": ["marketing_budget"],
    "total_variance": 12.3,
    "_llm_provider": "openai",
    "_llm_model": "gpt-4o-mini",
    "_success": true,
    "_agent_name": "analyzer"
  },
  "context": {
    "session_id": "fa44356e-66dc-4cb6-8dc9-be7512c78a9f",
    "agent_name": "human_reviewer",
    "agent_type": "human"
  },
  "session_data": {},
  "conversation_history": [
    {
      "timestamp": "2026-03-31T15:47:59.000000",
      "role": "user",
      "content": "Review our Q1 budget before I send to finance",
      "agent": null
    },
    {
      "timestamp": "2026-03-31T15:48:06.000000",
      "role": "assistant",
      "content": "{\"summary\": \"Q1 budget analysis complete...\"}",
      "agent": "analyzer"
    }
  ],
  "response_endpoint": "/webhook/review_budget",
  "timeout_seconds": 300
}
```

| Field | Content |
|-------|---------|
| `session_id` | Use this in your response to resume the correct session |
| `input_data` | Upstream agent's output — the data for the human to review |
| `conversation_history` | Full conversation context for the reviewer |
| `response_endpoint` | Where to send the human's response back |
| `timeout_seconds` | How long before the request expires |

## Webhook-Based Integration

Your backend receives the outbound webhook, stores the review request, and exposes it to your UI. When the human decides, your backend sends the response back to LeafMesh.

```
LeafMesh                    Your Backend              Your UI
   │                            │                       │
   ├── outbound webhook ──────▶ │                       │
   │   (session_id, data)       ├── store pending ─────▶│ show review
   │                            │                       │
   │   ◀── PAUSED ──            │                       │
   │                            │                       │
   │                            │  ◀── human decision ──┤
   │  ◀── POST /webhook ───────┤                       │
   │   (session_id, decision)   │                       │
   │                            │                       │
   ├── RESUMED ──▶              │                       │
```

### Backend Example (FastAPI)

```python
from fastapi import FastAPI, Request
import httpx
import hmac
import hashlib
import json

app = FastAPI()
pending_reviews = {}

import os

LEAFMESH_URL = "http://127.0.0.1:18820"
WEBHOOK_SECRET = os.environ["LEAFMESH_WEBHOOK_SECRET"]

@app.post("/review-needed")
async def receive_review(request: Request):
    """Outbound webhook from LeafMesh — a human review is needed"""
    payload = await request.json()
    session_id = payload["session_id"]

    pending_reviews[session_id] = {
        "input_data": payload["input_data"],
        "conversation_history": payload.get("conversation_history", []),
        "timeout_seconds": payload.get("timeout_seconds", 300),
        "status": "pending"
    }

    # Notify your UI (WebSocket, SSE, push notification, etc.)
    await notify_reviewers(session_id)
    return {"status": "received"}

@app.post("/review/{session_id}/respond")
async def submit_review(session_id: str, request: Request):
    """UI calls this when the human submits their decision"""
    response = await request.json()

    body = json.dumps({
        "session_id": session_id,
        "decision": response["decision"],
        "notes": response.get("notes", "")
    })

    # Sign the request with HMAC-SHA256
    signature = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    # Send response back to LeafMesh
    async with httpx.AsyncClient() as client:
        result = await client.post(
            f"{LEAFMESH_URL}/webhook/review_budget",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-LeafMesh-Signature": signature
            }
        )

    pending_reviews[session_id]["status"] = "completed"
    return result.json()
    # Expected: {"status": "resumed", "session_id": "...", "agent": "human_reviewer"}
```

## HMAC Signature Generation

All inbound webhooks to LeafMesh must include an HMAC-SHA256 signature.

### Python

```python
import hmac, hashlib, json

secret = "your-webhook-secret"
body = json.dumps({"session_id": "abc-123", "decision": "approved"})
signature = "sha256=" + hmac.new(
    secret.encode(), body.encode(), hashlib.sha256
).hexdigest()
# Header: X-LeafMesh-Signature: sha256=f4828d307baf41a33...
```

### Node.js

```javascript
const crypto = require('crypto');
const secret = 'your-webhook-secret';
const body = JSON.stringify({session_id: 'abc-123', decision: 'approved'});
const signature = 'sha256=' + crypto
  .createHmac('sha256', secret)
  .update(body)
  .digest('hex');
// Header: X-LeafMesh-Signature: sha256=f4828d307baf41a33...
```

### Get Your Secret

Rotate the secret from your LeafMesh settings and load it from an environment variable in your code:

```python
import os

secret = os.environ["LEAFMESH_WEBHOOK_SECRET"]
# Header on outbound requests: X-LeafMesh-Signature: sha256=<HMAC-SHA256 hex digest>
```

## Real-Time UI with WebSockets

For live review interfaces, combine the webhook receiver with WebSocket push:

```python
from fastapi import FastAPI, WebSocket
import json

app = FastAPI()
connected_reviewers = set()

@app.websocket("/ws/reviews")
async def review_websocket(websocket: WebSocket):
    await websocket.accept()
    connected_reviewers.add(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "review_response":
                await send_response_to_leafmesh(
                    data["session_id"], data["response"]
                )
    finally:
        connected_reviewers.discard(websocket)

@app.post("/review-needed")
async def review_webhook(payload: dict):
    """LeafMesh outbound webhook — push to all connected reviewers"""
    for client in connected_reviewers:
        await client.send_json({
            "type": "review_request",
            "session_id": payload["session_id"],
            "input_data": payload["input_data"],
            "conversation_history": payload.get("conversation_history", []),
            "timeout_seconds": payload.get("timeout_seconds", 300)
        })
    return {"status": "received"}
```

## Response Format

The human's response sent back to LeafMesh can contain any JSON fields. The `can_call` conditions on the human agent evaluate against these fields:

```json
{
  "session_id": "fa44356e-66dc-4cb6-8dc9-be7512c78a9f",
  "decision": "approved",
  "notes": "Budget looks good. Flag the 12% marketing increase.",
  "priority": "high"
}
```

The `session_id` is **required** — it tells LeafMesh which paused workflow to resume. All other fields are available for `can_call` condition evaluation:

```yaml
can_call:
  - agent: "executor"
    condition: "decision == 'approved'"
  - agent: "revision_handler"
    condition: "decision == 'revision_needed'"
  - agent: "urgent_executor"
    condition: "decision == 'approved' and priority == 'high'"
```

## Next Steps

- **[Notifications](notifications)** — Alert systems for reviewers
- **[Approval Workflows](workflows)** — Multi-step approval patterns
- **[Human Agents Reference](../agents/human-agents)** — Full configuration reference

---

*LeafMesh — Building human review interfaces*
