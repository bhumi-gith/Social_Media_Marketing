# Best Practices

Guidelines for building production-quality LeafMesh systems.

## Agent Design

### Keep Agents Focused

Each agent should have a single responsibility:

```yaml
# Good: focused agents
agents:
  classifier:
    prompt: "Classify the request by category and urgency."
    yields:
      category: "string"
      urgency: "number"

  resolver:
    prompt: "Resolve the technical issue."
    yields:
      solution: "string"
      confidence: "number"
```

```yaml
# Bad: agent doing too much
agents:
  do_everything:
    prompt: "Classify the request, resolve it, write a response, and log it."
    yields:
      category: "string"
      urgency: "number"
      solution: "string"
      response: "string"
      log_entry: "string"
```

### Use Appropriate Agent Types

| Task | Agent Type |
|------|-----------|
| Classification, analysis, content generation | LLM |
| Data validation, calculations, API calls | Programmatic |
| Approvals, quality review | Human |
| Monitoring, reports, maintenance | Scheduled |

### Design Clear Yields Schemas

```yaml
# Good: clear, typed outputs
yields:
  category: "string"
  confidence: "number"
  is_urgent: "boolean"

# Avoid: vague or overly complex schemas
yields:
  result: "string"          # Too vague
  data: "string"            # What data?
```

## Configuration

### Use Environment-Specific Configs

```yaml
# config.dev.yaml
redis:
  host: "localhost"
agents:
  classifier:
    model: "gpt-4o-mini"     # Cheaper for development

# config.prod.yaml
redis:
  host: "redis-cluster.internal"
  cluster_mode: true
agents:
  classifier:
    model: "gpt-4o"          # More capable for production
```

### Set Appropriate Token Limits

```yaml
agents:
  classifier:
    max_tokens: 500           # Short classification output
  writer:
    max_tokens: 2000          # Longer content output
  analyzer:
    max_tokens: 1000          # Medium analysis output
```

### Configure Sensible Timeouts

```yaml
agents:
  human_reviewer:
    timeout: 300              # 5 minutes for human response

manager:
  coordination_rules:
    max_agent_calls: 10       # Prevent runaway chains
```

## Intelligence Functions

### Keep Business Logic in Intelligence Functions

```python
async def processor(llm_response, input_data, context):
    # Business rules belong here, not in prompts
    if llm_response.get("amount", 0) > 10000:
        llm_response["requires_approval"] = True
    return llm_response
```

### Use Pre-Compose for Data Assembly

```python
# Good: deterministic context before LLM
@pre_compose(context_processor=fetch_account_data)
async def specialist(llm_response, input_data, context):
    return llm_response
```

```python
# Avoid: fetching data inside intelligence function
# (too late - LLM already ran without this context)
async def specialist(llm_response, input_data, context):
    account = await fetch_account_data(...)  # LLM didn't see this
    return llm_response
```

## Routing

### Use Explicit Conditions

```yaml
# Good: clear, specific conditions
can_call:
  - agent: "specialist"
    condition: "urgency >= 7 and category == 'technical'"

# Avoid: overly broad conditions
can_call:
  - agent: "specialist"
    condition: "true"    # Everything routes here
```

### Design for Failure

Include fallback paths in your routing:

```yaml
can_call:
  - agent: "specialist"
    condition: "confidence > 0.8"
  - agent: "human_reviewer"
    condition: "confidence <= 0.8"    # Fallback for low confidence
```

## Monitoring

### Check System Health Regularly

```python
# Periodic health check
analytics = leafmesh.get_usage_analytics()
agent_stats = leafmesh.get_agent_stats()
cache_stats = leafmesh.get_llm_cache_stats()
```

### Monitor Error Rates

High error rates indicate configuration or provider issues. Check:
- Agent error rates via `leafmesh.get_agent_stats()`
- Provider availability
- Redis connectivity

## Next Steps

- **[Agent Development](../agents/development)** — Agent building guide
- **[Testing Framework](testing)** — Testing strategies
- **[Production Setup](../deployment/production)** — Production deployment

---

*LeafMesh — Development best practices*
