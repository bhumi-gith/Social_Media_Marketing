# Customer Service System

A 4-agent customer service system with triage, specialist routing, and human review.

## Architecture

```
Customer Message
    │
    ▼
Triage Agent (gpt-4o-mini)
    │ yields: {category, urgency, summary}
    │
    ├── category == "technical" ──→ Technical Support (gpt-4o)
    │                                   │ yields: {solution, confidence}
    │
    ├── category == "billing"   ──→ Billing Support (gpt-4o-mini)
    │                                   │ yields: {resolution, amount}
    │                                   │
    │                               amount > 500
    │                                   │
    │                                   ▼
    │                              Human Reviewer
    │
    └── urgency >= 9            ──→ Human Reviewer (immediate escalation)
```

## Configuration

```yaml
name: "customer_service"
architecture: "managed_mesh"

agents:
  triage:
    name: "triage"
    model: "gpt-4o-mini"
    temperature: 0.1
    max_tokens: 500
    prompt: |
      You are a customer service triage agent.
      Classify the request by category (technical, billing, general)
      and urgency (1-10).
    context_parts:
      care: |
        Acknowledge the customer's frustration before classifying.
        Use warm, professional language even in the summary.
      guardrails: |
        Never disclose internal routing logic or agent names.
        Do not promise specific resolution timelines.
    yields:
      category: "string"
      urgency: "number"
      summary: "string"
    can_call:
      - agent: "technical_support"
        condition: "category == 'technical' and urgency < 9"
      - agent: "billing_support"
        condition: "category == 'billing' and urgency < 9"
      - agent: "human_reviewer"
        condition: "urgency >= 9"

  technical_support:
    name: "technical_support"
    model: "gpt-4o"
    tools: ["web_request", "text_analyzer"]
    max_tool_calls_per_message: 3
    prompt: |
      You are a technical support specialist.
      Diagnose the issue and provide step-by-step resolution.
    context_parts:
      care: |
        Be patient with non-technical users. Explain jargon.
        Offer to clarify steps if the solution is complex.
      sentiment_analysis: |
        If the user is frustrated or angry, acknowledge their
        experience and assure them you're working on it.
      guardrails: |
        Never suggest workarounds that compromise security.
        Do not share internal infrastructure details.
    yields:
      diagnosis: "string"
      solution: "string"
      confidence: "number"

  billing_support:
    name: "billing_support"
    model: "gpt-4o-mini"
    prompt: |
      You are a billing support specialist.
      Resolve billing inquiries and calculate any adjustments.
    yields:
      resolution: "string"
      amount: "number"
      requires_refund: "boolean"
    can_call:
      - agent: "human_reviewer"
        condition: "amount > 500 or requires_refund == true"

  human_reviewer:
    name: "human_reviewer"
    agent_type: "human"
    timeout: 300
    webhook_config:
      url: "https://support.example.com/review"
      method: "POST"
    communication_type: "dual"
    yields:
      approved: "boolean"
      notes: "string"

manager:
  enabled: true
  model: "gpt-4o-mini"
  coordination_rules:
    max_agent_calls: 10
    max_retries: 2

redis:
  host: "localhost"
  port: 6379

entry_points:
  - name: "customer_inquiry"
    target: "triage"
    description: "Incoming customer support requests"
```

## Application Code

```python
import asyncio
from leafmesh import LeafMesh, pre_compose

leafmesh = LeafMesh.from_yaml("customer_service.yaml")

# Load customer account data before triage
async def load_customer(input_data, context):
    customer_id = input_data.get("customer_id")
    if not customer_id:
        return {}
    # Load customer data from your external database or API
    customer = await database.get_customer(customer_id)
    return customer if customer else {}

@pre_compose(context_processor=load_customer)
async def triage(llm_response, input_data, context):
    return llm_response

# Function name "technical_support" matches the YAML agent name — auto_discover finds it
async def technical_support(llm_response, input_data, context):
    # Resolutions are automatically stored in the session via yields
    # Log to your external system if needed
    await log_resolution(context.get("session_id"), llm_response.get("diagnosis"))
    return llm_response

async def main():
    await leafmesh.start()

    # Test case 1: Technical issue
    result = await leafmesh.mesh_call(
        "customer_inquiry",
        {
            "user_message": "My API calls are returning 500 errors since yesterday",
            "customer_id": "cust_123"
        },
        session_id="ticket_001"
    )
    print(f"Technical: {result}")

    # Test case 2: High-urgency billing
    result = await leafmesh.mesh_call(
        "customer_inquiry",
        {
            "user_message": "I was charged $2000 incorrectly and need an immediate refund",
            "customer_id": "cust_456"
        },
        session_id="ticket_002"
    )
    print(f"Billing: {result}")

    await leafmesh.stop()

asyncio.run(main())
```

## Execution Walkthrough

### Test Case 1: Technical Issue

1. Triage classifies: `{category: "technical", urgency: 6, summary: "API 500 errors"}`
2. Condition `category == 'technical' and urgency < 9` matches
3. Technical Support receives triage yields, uses tools to research
4. Returns: `{diagnosis: "...", solution: "...", confidence: 0.9}`
5. Intelligence function logs resolution to Redis

### Test Case 2: High-Value Billing

1. Triage classifies: `{category: "billing", urgency: 7, summary: "Incorrect $2000 charge"}`
2. Condition `category == 'billing' and urgency < 9` matches
3. Billing Support returns: `{resolution: "...", amount: 2000, requires_refund: true}`
4. Condition `amount > 500 or requires_refund == true` matches
5. Human Reviewer receives webhook, reviews the refund request

## Next Steps

- **[Basic Swarm](basic-swarm)** — Minimal example
- **[Business Analysis](business-analysis)** — Analysis system
- **[Human-in-the-Loop](../human-in-loop/overview)** — HILT patterns

---

*LeafMesh — Customer service with human escalation*
