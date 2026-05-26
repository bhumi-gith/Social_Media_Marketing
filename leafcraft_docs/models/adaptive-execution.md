# Adaptive Execution

LeafMesh can automatically select the best model for each request at runtime. Instead of always using the single model specified in your agent's YAML, the platform evaluates the incoming request, learns from historical performance, and routes it to the model most likely to succeed for your chosen strategy -- all transparently.

This is opt-in. Without `optimization_strategy`, your agent always uses the model you configured.

## Quick Start

Add `optimization_strategy` to any agent in your YAML:

```yaml
agents:
  support_agent:
    name: "support_agent"
    model: "gpt-4o"                    # Default fallback model
    optimization_strategy: "cost"      # Minimize token costs at runtime
    prompt: |
      You handle customer support inquiries and return structured results.
    yields:
      resolution: "string"
      category: "string"
```

That is the only change required. The system handles everything else: classifying requests, selecting models, tracking performance, and falling back on failure.

---

## How It Works

When an agent with `optimization_strategy` receives a request, the platform automatically:

1. **Evaluates the request** against your chosen strategy.
2. **Selects a model** using learned performance data across the providers you have configured.
3. **Executes** the request and records the outcome to improve future selections.
4. **Falls back automatically** to alternative models if the selected one fails, with your configured `model:` as the final fallback.

The platform learns model performance over time and adapts -- early requests rely on built-in defaults, and selections become more accurate as usage data accumulates.

---

## Optimization Strategies

Three strategies are available in YAML configuration:

| Strategy | YAML Value | Optimizes For | Best For |
|----------|-----------|--------------|----------|
| Performance | `"performance"` | Overall quality and reliability | Production systems where correctness matters most |
| Cost | `"cost"` | Minimize token costs | High-volume workloads, simple classification, bulk processing |
| Speed | `"speed"` | Minimize response latency | Real-time applications, user-facing chat, time-sensitive pipelines |

### Choosing a Strategy

**Use `"performance"` when** the quality of the output directly affects business outcomes -- customer-facing analysis, financial decisions, complex reasoning chains. The system favors models with the highest combined quality and success rate, even if they cost more or respond slower.

**Use `"cost"` when** you are processing high volumes of relatively simple or repetitive tasks -- classification, extraction, routing. The system favors the cheapest model that still meets a baseline quality threshold.

**Use `"speed"` when** response time is the primary constraint -- interactive chat, real-time pipelines, latency-sensitive APIs. The system favors the fastest-responding model for the given request category.

### Per-Agent Strategy

Different agents in the same system can use different strategies:

```yaml
agents:
  # Fast triage -- minimize latency for instant routing
  triage:
    name: "triage"
    model: "gpt-4o-mini"
    optimization_strategy: "speed"
    prompt: |
      Classify the request into: billing, technical, general.
    yields:
      category: "string"

  # Deep analysis -- maximize output quality
  analyst:
    name: "analyst"
    model: "claude-3.5-sonnet"
    optimization_strategy: "performance"
    prompt: |
      Perform detailed technical analysis of the issue.
    yields:
      analysis: "string"
      confidence: "number"

  # Bulk processor -- minimize cost across thousands of requests
  extractor:
    name: "extractor"
    model: "gpt-4o-mini"
    optimization_strategy: "cost"
    prompt: |
      Extract structured fields from the input document.
    yields:
      fields: "object"
```

Agents without `optimization_strategy` always use their configured model directly, with no adaptive behavior.

---

## Automatic Fallback

If the selected model fails (provider outage, rate limit, network error), the platform automatically tries alternative models before giving up. Your configured `model:` field is always tried as the final fallback. No configuration is needed -- fallback is enabled by default whenever `optimization_strategy` is set.

This means your agents stay operational during partial provider outages. If your agent is configured with `model: "gpt-4o"` and OpenAI is unreachable, the platform will try other available providers automatically.

---

## Performance Learning

The platform records the outcome of every LLM call and uses that history to improve future selections. Early requests rely on built-in defaults; as usage accumulates, selections become more accurate for your specific workload. Recent performance is weighted more heavily than older data.

### Practical Example

Suppose you have three providers configured (OpenAI, Anthropic, Google) and an agent with `optimization_strategy: "cost"`. Over time, the platform learns which model is cheapest for the kinds of requests your agent actually handles, and routes each request accordingly -- no manual tuning required.

---

## Multi-Provider Support

Adaptive execution works across all configured providers. If you have API keys for OpenAI, Anthropic, and Google, the platform can select from models across all three providers for any single agent. Cloud gateway providers (Amazon Bedrock, Google Vertex AI, and Microsoft Foundry) are also supported and participate in adaptive selection alongside direct-provider models.

The available model pool depends on which providers are configured with valid credentials at startup. Providers that are missing API keys or are unreachable are skipped with a warning.

For full provider setup instructions, see **[LLM Providers](providers)**.

---

## Cost Tracking

LeafMesh tracks the cost of every LLM call -- model used, prompt and completion tokens, estimated cost in USD, response time, and whether the response was served from cache. A built-in pricing table covers the major OpenAI, Anthropic, and Google models; models not in the table use a fallback estimate.

Access aggregated cost data at runtime:

```python
# Get usage analytics (costs, token counts, per-model breakdown)
analytics = await leafmesh.get_usage_analytics()

# Get LLM cache statistics (hit rate, savings)
cache_stats = await leafmesh.get_llm_cache_stats()
```

---

## Full Configuration Reference

All adaptive execution settings are configured per-agent in YAML:

```yaml
agents:
  my_agent:
    name: "my_agent"
    model: "gpt-4o"                    # Required: default/fallback model
    optimization_strategy: "cost"      # Optional: "performance", "cost", or "speed"
    temperature: 0.3                   # Standard LLM parameter
    max_tokens: 1000                   # Standard LLM parameter
    prompt: |
      Your agent prompt here.
    yields:
      result: "string"
```

| Field | Required | Values | Description |
|-------|----------|--------|-------------|
| `model` | Yes | Any supported model name | The model used when adaptive selection is off, and the final fallback when it is on |
| `optimization_strategy` | No | `"performance"`, `"cost"`, `"speed"` | Enables adaptive execution with the specified strategy. Omit to disable. |

---

## Next Steps

- **[LLM Providers](providers)** -- Multi-provider setup and local model configuration
- **[Agent Configuration](../api-reference/agent-config)** -- Full YAML reference for all agent settings

---

*LeafMesh -- Intelligent model selection, automatic fallback, zero configuration overhead*
