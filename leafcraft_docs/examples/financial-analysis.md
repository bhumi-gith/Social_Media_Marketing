# Financial Analysis Platform

A multi-agent financial analysis system with scheduled data collection, multi-model analysis, and human approval for high-value recommendations.

## Architecture

```
Scheduled Data Collector (every hour)
    │ yields: {data_points, source, timestamp}
    │
    ▼
Analyzer (claude-3.5-sonnet)
    │ yields: {trend, risk_score, recommendation, confidence}
    │
    ├── risk_score > 7 ──→ Human Reviewer
    │
    └── risk_score <= 7 ──→ Report Generator (gpt-4o-mini)
                                │ yields: {report, summary}
```

## Configuration

```yaml
name: "financial_analysis"
architecture: "managed_mesh"

agents:
  data_collector:
    name: "data_collector"
    agent_type: "programmatic"
    wake_up: "0 * * * *"         # Every hour
    yields:
      data_points: "number"
      source: "string"
      timestamp: "string"
    can_call:
      - agent: "analyzer"
        condition: "data_points > 0"

  analyzer:
    name: "analyzer"
    model: "claude-3.5-sonnet"
    tools: ["calculator", "web_request"]
    max_tool_calls_per_message: 5
    prompt: |
      You are a financial analyst. Analyze the provided data,
      identify trends, assess risk (1-10), and provide a recommendation.
    yields:
      trend: "string"
      risk_score: "number"
      recommendation: "string"
      confidence: "number"
    can_call:
      - agent: "human_reviewer"
        condition: "risk_score > 7 or confidence < 0.6"
      - agent: "report_generator"
        condition: "risk_score <= 7 and confidence >= 0.6"

  human_reviewer:
    name: "human_reviewer"
    agent_type: "human"
    timeout: 1800                 # 30 minutes for financial decisions
    webhook_config:
      url: "https://finance.example.com/review"
      method: "POST"
    yields:
      approved: "boolean"
      adjusted_recommendation: "string"
    can_call:
      - agent: "report_generator"
        condition: "approved == true"

  report_generator:
    name: "report_generator"
    model: "gpt-4o-mini"
    prompt: |
      Generate a concise financial report based on the analysis.
      Include key findings, risk assessment, and actionable recommendations.
    yields:
      report: "string"
      summary: "string"

manager:
  enabled: true
  model: "gpt-4o-mini"
  coordination_rules:
    max_agent_calls: 10

redis:
  host: "localhost"
  port: 6379
  default_ttl: 7200
  session_ttl: 14400             # 4 hours for financial sessions

entry_points:
  - name: "analysis_request"
    target: "analyzer"
    description: "Ad-hoc financial analysis requests"
```

## Application Code

```python
import asyncio
import json
from datetime import datetime
from leafmesh import LeafMesh, pre_compose

leafmesh = LeafMesh.from_yaml("financial_config.yaml")

# Function name "data_collector" matches the YAML agent name — auto_discover finds it
async def data_collector(llm_response, input_data, context):
    """Scheduled: collect financial data every hour"""
    # In production, fetch from real data sources
    data = {
        "data_points": 100,
        "source": "market_feed",
        "timestamp": datetime.now().isoformat(),
        "metrics": {"price": 150.25, "volume": 50000, "change": -2.3}
    }

    # Data is automatically stored in the session via yields
    # and passed to downstream agents through the can_call chain
    return data

# Load historical data for analyzer using pre-compose
async def load_financial_context(input_data, context):
    # Use an external database or API to load historical data
    # Upstream yields are automatically passed as input_data
    return {"latest_data": input_data, "analysis_time": datetime.now().isoformat()}

@pre_compose(context_processor=load_financial_context)
async def analyzer(llm_response, input_data, context):
    return llm_response

# Function name "report_generator" matches the YAML agent name — auto_discover finds it
async def report_generator(llm_response, input_data, context):
    # Reports are automatically stored in the session via yields.
    # Browse them in Studio's Sessions tab.
    return llm_response

async def main():
    await leafmesh.start()

    # Ad-hoc analysis request
    result = await leafmesh.mesh_call(
        "analysis_request",
        {
            "user_message": "Analyze the current market position and recommend next steps",
            "portfolio": "growth_fund"
        },
        session_id="analysis_001"
    )

    print(f"Analysis result: {result}")

    # The scheduled data_collector runs automatically every hour
    # It feeds data to the analyzer, which routes based on risk

    await leafmesh.stop()

asyncio.run(main())
```

## Key Patterns

| Pattern | Implementation |
|---------|---------------|
| Scheduled collection | `wake_up: "0 * * * *"` on programmatic agent |
| Multi-model | Claude for analysis, GPT-4o-mini for reports |
| Risk-based routing | `risk_score > 7` → human review |
| Long-term storage | Reports stored with 24h TTL |
| Pre-compose | Historical data loaded before analysis |
| Human gating | High-risk recommendations require approval |

## Next Steps

- **[Business Analysis](business-analysis)** — General business analysis
- **[Scheduled Agents](../agents/scheduling)** — Scheduling patterns
- **[Human-in-the-Loop](../human-in-loop/overview)** — HILT patterns

---

*LeafMesh — Financial analysis with scheduled data and human approval*
