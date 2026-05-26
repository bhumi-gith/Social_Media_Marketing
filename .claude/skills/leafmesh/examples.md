# LeafMesh Agent Patterns — Copy-Paste Templates

## Pattern 1: Customer Support Hub (Router + Specialists)

### config.yaml
```yaml
entry_points:
  - name: "support"
    target: "router_agent"
    condition: "always"

agents:
  router_agent:
    agent_type: "llm"
    model: "gpt-4o-mini"
    prompt: |
      You are a customer support router. Classify the customer's intent
      and respond with: intent (billing/technical/general), urgency (low/medium/high),
      and a brief summary.
    yields: {intent: string, urgency: string, summary: string}
    can_call:
      - agent: "billing_agent"
        condition: "intent == 'billing'"
      - agent: "technical_agent"
        condition: "intent == 'technical'"
      - agent: "general_agent"
        condition: "intent == 'general'"

  billing_agent:
    agent_type: "llm"
    model: "gpt-4o"
    prompt: "You are a billing specialist. Help resolve billing inquiries."
    tools: ["lookup_account", "check_invoice"]
    tool_categories: ["data"]

  technical_agent:
    agent_type: "llm"
    model: "gpt-4o"
    prompt: "You are a technical support specialist."
    tools: ["check_status", "search_kb"]
    memory: true

  general_agent:
    agent_type: "llm"
    model: "gpt-4o-mini"
    prompt: "You are a friendly general support agent."
```

### agency/router_agent.py
```python
from leafmesh import pre_compose

def detect_language(input_data, context):
    msg = input_data.get("message", "")
    return {"language": "en", "char_count": len(msg)}

@pre_compose(context_processor=detect_language)
async def router_agent(llm_response, input_data, context):
    return {
        "intent": llm_response.get("intent", "general"),
        "urgency": llm_response.get("urgency", "low"),
        "summary": llm_response.get("summary", input_data.get("message", "")),
    }
```

---

## Pattern 2: Research Pipeline (Fan-Out + Fan-In)

### config.yaml
```yaml
entry_points:
  - name: "research"
    target: "coordinator_agent"
    condition: "always"

agents:
  coordinator_agent:
    agent_type: "llm"
    model: "gpt-4o-mini"
    prompt: "Break down the research query into sub-questions."
    can_call:
      - {agent: "web_researcher"}
      - {agent: "data_analyst"}
      - {agent: "domain_expert"}

  web_researcher:
    agent_type: "llm"
    model: "gpt-4o"
    prompt: "Research the web for relevant information on the topic."
    tools: ["web_search"]
    parallel: true

  data_analyst:
    agent_type: "programmatic"
    parallel: true

  domain_expert:
    agent_type: "llm"
    model: "claude-sonnet-4-5-20250929"
    prompt: "Provide domain expertise and analysis."

  synthesizer_agent:
    agent_type: "llm"
    model: "gpt-4o"
    prompt: "Synthesize all research findings into a coherent report."
    wait_for: "web_researcher AND data_analyst AND domain_expert?"
    wait_for_timeout: 120
```

### agency/synthesizer_agent.py
```python
from leafmesh import chain

def add_citations(result, context):
    sources = result.get("sources", [])
    result["citation_count"] = len(sources)
    return result

def format_report(result, context):
    result["format"] = "markdown"
    result["report"] = f"# Research Report\n\n{result.get('synthesis', '')}"
    return result

@chain(add_citations, format_report)
async def synthesizer_agent(llm_response, input_data, context):
    upstream = input_data.get("upstream_yields", {})
    web = upstream.get("web_researcher", {})
    data = upstream.get("data_analyst", {})
    domain = upstream.get("domain_expert", {})  # May be empty (optional)

    return {
        "synthesis": llm_response,
        "sources": web.get("sources", []) + data.get("sources", []),
        "confidence": 0.9 if domain else 0.7,
    }
```

---

## Pattern 3: HITL Dual-Mode (Human Reviews Agent Output)

System triggers a workflow, agent processes, human reviews before continuing.

### config.yaml
```yaml
entry_points:
  - name: "greet_user"
    target: "greeter_agent"
  - name: "human_contact"
    target: "client"

agents:
  client:
    name: "client"
    agent_type: "human"
    human_interface: "webhook"          # required to actually use webhook_config below
    communication_type: "dual"
    human_timeout_seconds: 300
    webhook_config:
      outbound_url: "http://127.0.0.1:9999/human-notify"
      outbound_headers:
        Content-Type: "application/json"
      outbound_timeout: 30
      # inbound_endpoint is auto-derived from entry_points — no need to set it
      max_retries: 1
      retry_delay: 2
    can_call:
      - agent: "greeter_agent"
        condition: "not calling_agent_response.from_agent"
      - agent: "processor_agent"
        condition: "calling_agent_response.from_agent == 'greeter_agent'"

  greeter_agent:
    agent_type: "llm"
    model: "gpt-4o-mini"
    communication_type: "dual"
    can_call:
      - agent: "client"    # Routes to human for review

  processor_agent:
    agent_type: "programmatic"
    can_call:
      - agent: "researcher_agent"
        condition: "calling_agent_response.item_count > 0"
```

### How it works
```
Scenario 1 (system-initiated):
  POST /api/mesh/request {"entry_point": "greet_user", ...}
    -> greeter -> client (HITL, webhook sent)
    -> human responds via POST /webhook/greet_user
    -> from_agent=="greeter_agent" -> processor -> ...

Scenario 2 (human-initiated):
  POST /webhook/human_contact {"message": "I need help"}
    -> client (no from_agent -> greeter)
    -> greeter (dual callback -> client HITL, webhook sent)
    -> human responds -> from_agent=="greeter_agent" -> processor -> ...

Scenario 3 (same session, new message):
  POST /webhook/human_contact {"session_id": "existing", "message": "Now check refund"}
    -> session not paused -> new request, conversation history preserved
```

### Testing HITL locally
```bash
# Terminal 1: stub receiver (captures outbound webhooks)
python hitl_stub_receiver.py

# Terminal 2: mesh server
python main.py

# Terminal 3: trigger + respond
SECRET=$(curl -s http://127.0.0.1:18820/api/webhook/secret | jq -r .secret)
curl -X POST http://127.0.0.1:18820/api/mesh/request \
  -H "Content-Type: application/json" \
  -d '{"entry_point": "greet_user", "data": {"message": "Help me"}}'

# ... stub prints session_id, then respond:
BODY='{"session_id": "SESSION_ID", "decision": "approved", "message": "Proceed"}'
SIG=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')
curl -X POST http://127.0.0.1:18820/webhook/greet_user \
  -H "Content-Type: application/json" \
  -H "X-LeafMesh-Signature: sha256=$SIG" \
  -d "$BODY"
```

---

## Pattern 4: Scheduled Background Jobs

### config.yaml
```yaml
agents:
  daily_report_agent:
    agent_type: "programmatic"
    wake_up: "0 9 * * *"           # Every day at 9 AM
    communication_type: "execute"   # Fire-and-forget

  hourly_monitor_agent:
    agent_type: "llm"
    model: "gpt-4o-mini"
    prompt: "Analyze system metrics and flag anomalies."
    wake_up: "0 * * * *"           # Every hour
    tools: ["check_metrics", "send_alert"]
```

### agency/daily_report_agent.py
```python
async def daily_report_agent(llm_response, input_data, context):
    from datetime import datetime, timezone
    return {
        "report": "Daily system health: all green",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "checks": ["redis_ok", "agents_healthy", "sessions_active"],
        "status": "completed",
    }
```

---

## Pattern 5: Multi-Model Strategy (Cost Optimization)

### config.yaml
```yaml
agents:
  triage_agent:
    agent_type: "llm"
    model: "gpt-4o-mini"           # Cheap, fast triage
    optimization_strategy: "speed"
    prompt: "Classify query complexity: simple, moderate, or complex."
    can_call:
      - agent: "simple_handler"
        condition: "complexity == 'simple'"
      - agent: "complex_handler"
        condition: "complexity == 'complex'"
      - agent: "moderate_handler"
        condition: "complexity == 'moderate'"

  simple_handler:
    agent_type: "llm"
    model: "gpt-4o-mini"           # Cheap for simple queries
    optimization_strategy: "cost"

  moderate_handler:
    agent_type: "llm"
    model: "gpt-4o"                # Balanced
    optimization_strategy: "cost"

  complex_handler:
    agent_type: "llm"
    model: "claude-sonnet-4-5-20250929"   # Best quality for hard tasks
    optimization_strategy: "performance"
    reasoning: true                # Enable chain-of-thought
```

---

## Pattern 6: External Framework Integration

### CrewAI (connector-only, no Python needed)
```yaml
agents:
  crewai_research:
    agent_type: "external"
    framework: "crewai"
    connector_config:
      endpoint: "http://localhost:9000"
      api_key: "${CREWAI_API_KEY}"              # Bearer Token
      # user_api_key: "${CREWAI_USER_API_KEY}"  # User Bearer Token (preferred over api_key)
      poll_interval: 2.0
      max_poll_seconds: 300
    can_call:
      - agent: "internal_processor"
    yields: {result: object}
    inputs: {task: string}
```

### Programmatic + Connector (connector-only, no Python needed)
```yaml
agents:
  zapier_sheets:
    agent_type: "programmatic"
    integration: "zapier"
    connector_config:
      connection: "google_sheets"
      action: "create_spreadsheet_row"
      api_key: "${ZAPIER_API_KEY}"
    yields: {status: string}
    inputs: {row_data: object}

  n8n_workflow:
    agent_type: "programmatic"
    integration: "n8n"
    connector_config:
      webhook_url: "http://localhost:5678/webhook/my-workflow"
      mode: "callback"
      callback_timeout: 120
    yields: {result: object}
    inputs: {data: object}
```

The connector response is returned as-is. To post-process, add `@sdk.intelligence()`:

### Programmatic + Connector + Python (post-process connector result)
```python
async def zapier_sheets(connector_response, input_data, context):
    # connector_response = Zapier's raw response
    return {
        "status": "logged" if connector_response.get("success") else "failed",
        "row_id": connector_response.get("content", {}).get("id"),
    }
```

### Using Zapier as @pre_compose helper (enrichment before LLM)
```python
from leafmesh import pre_compose, zapier

@pre_compose(
    context_processor=zapier(
        action="slack_send_message",
        api_key="${ZAPIER_NLA_API_KEY}",
    )
)
async def notification_agent(llm_response, input_data, context):
    slack_result = context["prepared_data"]["business_context"]
    return {"notified": True, "channel": slack_result.get("channel")}
```

---

## Pattern 7: Memory-Aware Agent (Learning from History)

### config.yaml
```yaml
agents:
  advisor_agent:
    agent_type: "llm"
    model: "gpt-4o"
    prompt: |
      You are a financial advisor. Use the memory of past interactions
      to provide personalized, context-aware advice. Reference previous
      conversations when relevant.
    memory: true
    memory_limit: 20       # Load last 20 feed posts
    tools: ["market_data", "portfolio_lookup"]
```

### agency/advisor_agent.py
```python
from leafmesh import chain_with_results

def check_portfolio(result, context):
    memory = context.get("memory_posts", [])
    prior_topics = [p.get("content", "") for p in memory[-5:]]
    result["prior_context"] = prior_topics
    return result

def personalize(result, context):
    if result.get("prior_context"):
        result["personalized"] = True
        result["greeting"] = "Welcome back! Continuing from where we left off..."
    return result

@chain_with_results(check_portfolio, personalize)
async def advisor_agent(llm_response, input_data, context):
    memory_posts = context.get("memory_posts", [])
    return {
        "advice": llm_response,
        "session_count": len(memory_posts),
        "confidence": 0.85,
    }
```

---

## Pattern 8: Conditional Processing with @conditional_chain

```python
from leafmesh import conditional_chain

def needs_translation(result, context):
    return result.get("language") != "en"

def translate_to_english(result, context):
    result["original_language"] = result["language"]
    result["translated"] = True
    # In real code, call translation API here
    return result

def add_disclaimer(result, context):
    result["disclaimer"] = "This response was auto-translated"
    return result

@conditional_chain(needs_translation, translate_to_english, add_disclaimer)
async def intake_agent(llm_response, input_data, context):
    return {
        "response": llm_response,
        "language": input_data.get("language", "en"),
    }
```

---

## Pattern 9: Custom Global Tools

```python
from leafmesh import global_tool
import httpx

@global_tool(
    name="fetch_weather",
    description="Get current weather for a city",
    category="web",
    timeout_seconds=10,
)
async def fetch_weather(city: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://wttr.in/{city}?format=j1")
        data = resp.json()
        current = data.get("current_condition", [{}])[0]
        return {
            "city": city,
            "temp_c": current.get("temp_C"),
            "description": current.get("weatherDesc", [{}])[0].get("value"),
        }

@global_tool(
    name="db_query",
    description="Run a read-only database query",
    category="data",
    allowed_agents=["analyst_agent", "report_agent"],
    requires_confirmation=True,
    timeout_seconds=30,
)
async def db_query(sql: str) -> dict:
    # Validate read-only
    if any(kw in sql.upper() for kw in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]):
        return {"error": "Only SELECT queries allowed"}
    # Execute query...
    return {"rows": [], "count": 0}
```

---

## Quick Reference: Decorator Stacking

```python
# All decorators can be combined. Execution order (bottom to top):

@chain(step1, step2)                    # 4. Post-process pipeline
@compose(                               # 3. Shape per-target payloads
    agent_a=lambda r, c: {"key": r["x"]},
    agent_b=lambda r, c: {"key": r["y"]},
)
@pre_compose(                           # 1. Prepare inputs (before LLM)
    context_processor=enrich,
    input_processor=clean,
)
async def my_agent(llm_response, input_data, context):
    return {"x": 1, "y": 2}            # 2. Agent logic + LLM
```

## Docker Deployment

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]

  app:
    build: .
    ports: ["18820:18820"]
    env_file: .env
    depends_on:
      redis:
        condition: service_healthy
```

```dockerfile
# Dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY configs/ configs/
COPY agency/ agency/
COPY main.py .
EXPOSE 18820
CMD ["python", "main.py"]
```
