# Business Analysis Bot

A multi-agent system for analyzing business data using specialist agents with different models.

## Architecture

```
User Query
    │
    ▼
Analyst (gpt-4o) ─── Classifies and analyzes
    │
    ├── category == "financial" ──→ Financial Specialist (claude-3.5-sonnet)
    ├── category == "market"    ──→ Market Specialist (gpt-4o)
    └── category == "risk"      ──→ Risk Assessor (gpt-4o-mini)
                                         │
                                    confidence < 0.7
                                         │
                                         ▼
                                    Human Reviewer
```

## Configuration

```yaml
name: "business_analysis"
architecture: "managed_mesh"

agents:
  analyst:
    name: "analyst"
    model: "gpt-4o"
    prompt: |
      You are a business analyst. Classify the query by category
      (financial, market, or risk) and provide an initial assessment.
    yields:
      category: "string"
      initial_assessment: "string"
      data_points: "number"
    can_call:
      - agent: "financial_specialist"
        condition: "category == 'financial'"
      - agent: "market_specialist"
        condition: "category == 'market'"
      - agent: "risk_assessor"
        condition: "category == 'risk'"

  financial_specialist:
    name: "financial_specialist"
    model: "claude-3.5-sonnet"
    prompt: |
      Analyze the financial aspects of the business query.
      Provide specific metrics and recommendations.
    yields:
      analysis: "string"
      key_metrics: "string"
      recommendation: "string"
      confidence: "number"

  market_specialist:
    name: "market_specialist"
    model: "gpt-4o"
    prompt: |
      Analyze market conditions and competitive landscape.
    yields:
      market_analysis: "string"
      trends: "string"
      confidence: "number"

  risk_assessor:
    name: "risk_assessor"
    model: "gpt-4o-mini"
    prompt: |
      Assess business risks and provide mitigation strategies.
    yields:
      risk_level: "string"
      risks: "string"
      mitigations: "string"
      confidence: "number"
    can_call:
      - agent: "human_reviewer"
        condition: "confidence < 0.7"

  human_reviewer:
    name: "human_reviewer"
    agent_type: "human"
    timeout: 600
    webhook_config:
      url: "https://review.example.com/business"
      method: "POST"
    yields:
      approved: "boolean"
      notes: "string"

manager:
  enabled: true
  model: "gpt-4o-mini"
  coordination_rules:
    max_agent_calls: 10

redis:
  host: "localhost"
  port: 6379

entry_points:
  - name: "business_query"
    target: "analyst"
```

## Application Code

```python
import asyncio
from leafmesh import LeafMesh, pre_compose

leafmesh = LeafMesh.from_yaml("business_config.yaml")

# Pre-compose: load company data before LLM call
async def load_company_context(input_data, context):
    company = input_data.get("company", "default")
    # Load company data from your external database or API
    company_data = await database.get_company(company)
    return company_data if company_data else {"company": company}

@pre_compose(context_processor=load_company_context)
async def analyst(llm_response, input_data, context):
    return llm_response

# Function name "financial_specialist" matches the YAML agent name — auto_discover finds it
async def financial_specialist(llm_response, input_data, context):
    # Add upstream context
    llm_response["source_category"] = input_data.get("category")
    return llm_response

async def main():
    await leafmesh.start()

    result = await leafmesh.mesh_call(
        "business_query",
        {
            "user_message": "What are the financial risks of expanding into the Asian market?",
            "company": "acme_corp"
        },
        session_id="analysis_001"
    )

    print(result)
    await leafmesh.stop()

asyncio.run(main())
```

## Key Patterns

| Pattern | Implementation |
|---------|---------------|
| Multi-model | Different agents use different providers |
| Conditional routing | Category-based branching |
| Human gating | Low-confidence results routed to human |
| Pre-compose | Company data loaded before LLM call |
| Intelligence function | Business logic added post-LLM |

## Next Steps

- **[Financial Analysis](financial-analysis)** — Dedicated financial system
- **[Customer Service](customer-service)** — Service desk example
- **[Basic Swarm](basic-swarm)** — Minimal example

---

*LeafMesh — Business analysis with multi-model agents*
