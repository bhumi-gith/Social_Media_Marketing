# Runtime Optimization

Techniques for optimizing LeafMesh performance in production.

## LLM Response Caching

LeafMesh includes built-in LLM response caching that deduplicates identical requests:

```yaml
redis:
  auto_storage: true    # Enables caching alongside auto-storage
```

When enabled, cache hits are served directly, saving both latency and cost. Hit rate and estimated savings are visible in the dashboard.

```python
# Check cache effectiveness
cache_stats = leafmesh.get_llm_cache_stats()
print(f"Hit rate: {cache_stats['hit_rate']}")
print(f"Cost savings: ${cache_stats['estimated_savings']}")
```

## Model Selection Optimization

Use the adaptive model selection to automatically pick the best model for each request:

```yaml
agents:
  # Fast, cheap model for simple classification
  triage:
    model: "gpt-4o-mini"
    optimization_strategy: "cost"

  # More capable model for complex analysis
  specialist:
    model: "gpt-4o"
    optimization_strategy: "performance"

  # Balanced approach
  general:
    model: "claude-3.5-sonnet"
    optimization_strategy: "performance"
```

LeafMesh categorizes requests and selects models based on the configured strategy. See [Adaptive Execution](../models/adaptive-execution) for details.

## Redis TTL Tuning

Adjust TTL values based on your access patterns:

```yaml
redis:
  default_ttl: 3600     # 1 hour for agent yields
  session_ttl: 7200     # 2 hours for sessions
```

- **Short TTL** (< 1h): High-throughput systems where data is consumed quickly
- **Default TTL** (1-2h): Standard interactive sessions
- **Long TTL** (24h+): Baseline data and configurations that change slowly
- **No TTL**: Global configuration data that should persist indefinitely

## Token Optimization

Control token usage per agent:

```yaml
agents:
  classifier:
    max_tokens: 500           # Short responses for classification
    temperature: 0.1          # Low randomness for consistent output

  writer:
    max_tokens: 2000          # Longer responses for content
    temperature: 0.7          # Higher creativity
```

## Reducing Mesh Latency

### Use `call_immediately`

For chains that should always fire, skip waiting for the current response to fully process:

```yaml
can_call:
  - agent: "logger"
    condition: "true"
    call_immediately: true    # Fire without waiting
```

### Limit Call Depth

Prevent deep chains that add latency:

```yaml
manager:
  coordination_rules:
    max_agent_calls: 10       # Limit total calls per session
```

## Monitoring Performance

```python
# Overall system analytics
analytics = leafmesh.get_usage_analytics()
print(f"Events processed: {analytics['total_events']}")
print(f"Error rate: {analytics['error_rate']}")

# Per-agent performance
agent_stats = leafmesh.get_agent_stats()
for agent, stats in agent_stats.items():
    print(f"{agent}: avg {stats['avg_response_ms']}ms, errors: {stats['error_count']}")
```

## Performance Characteristics

| Component | Overhead |
|-----------|----------|
| Request routing | ~10-50ms |
| Condition evaluation | ~1ms |
| LLM call | 500ms-5s (provider-dependent) |
| Tool execution | Varies by tool |

The LLM call dominates request latency. Optimization efforts should focus on model selection, prompt efficiency, and caching rather than framework-level tuning.

## Next Steps

- **[Adaptive Execution](../models/adaptive-execution)** — Automatic model selection
- **[Redis Integration](../memory/redis-integration)** — Redis configuration
- **[Scaling](../deployment/scaling)** — Horizontal scaling patterns

---

*LeafMesh — Production performance tuning*
