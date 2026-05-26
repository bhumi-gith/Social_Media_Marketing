# Scaling & Load Balancing

Strategies for scaling LeafMesh deployments to handle production workloads.

## Architecture for Scale

```
                Load Balancer
                     │
          ┌──────────┼──────────┐
          │          │          │
     ┌────┴────┐ ┌───┴─────┐ ┌──┴──────┐
     │LeafMesh │ │LeafMesh │ │LeafMesh │
     │ Pod 1   │ │ Pod 2   │ │ Pod 3   │
     └────┬────┘ └───┬─────┘ └──┬──────┘
          │          │          │
          └──────────┼──────────┘
                     │
               ┌─────┴──────┐
               │   Shared    │
               │   Backend   │
               └────────────┘
```

## Horizontal Scaling

Scale by adding instances. All instances share the same backend, so state is handled automatically. Each instance:
- Loads the same YAML configuration
- Handles different sessions independently
- Shares state through the shared backend

No session affinity required — any instance can process any session.

## Redis Scaling

### Single Redis → Redis Cluster

```yaml
# Development
redis:
  host: "localhost"
  port: 6379

# Production
redis:
  cluster_mode: true
  cluster_nodes:
    - "redis-1:6379"
    - "redis-2:6379"
    - "redis-3:6379"
```

### Redis Performance Tuning

- **Connection pooling**: LeafMesh maintains a connection pool to the backend
- **Pipeline commands**: Batch Redis operations where possible
- **Key expiration**: TTLs prevent unbounded storage growth
- **Cluster sharding**: Data distributed across nodes by key hash

## LLM Provider Scaling

Distribute agents across providers to avoid rate limits:

```yaml
agents:
  # Spread across providers
  triage_1:
    model: "gpt-4o-mini"         # OpenAI
  triage_2:
    model: "gemini-2.0-flash"    # Google
  specialist:
    model: "claude-3.5-sonnet"   # Anthropic
```

Each provider has independent rate limits, increasing total throughput.

## Performance Characteristics

| Component | Latency | Scaling Factor |
|-----------|---------|---------------|
| LeafMesh routing overhead | 10-50ms | Per-instance |
| Backend operations | 1-10ms | Scales with cluster |
| LLM calls | 500ms-5s | Scales with providers |
| Event processing | Async | Per-instance |

## Bottleneck Analysis

| Bottleneck | Symptom | Solution |
|-----------|---------|----------|
| Backend | High latency in state operations | Redis Cluster |
| LLM rate limits | 429 errors from providers | Multi-provider, caching |
| CPU (single process) | Event loop blocking | Multiple instances |
| Network | Slow external API calls | Pre-compose caching |

## Monitoring at Scale

```python
# Per-instance metrics
analytics = leafmesh.get_usage_analytics()
```

Monitor backend health and overall throughput via the Studio dashboard. If end-to-end latency rises while per-instance CPU stays low, add more instances — the shared backend handles state coordination automatically.

## Current Limitations

- No built-in cross-instance load balancing
- No distributed agent scheduling (each instance runs its own scheduler)
- The shared backend is the state bottleneck
- Single-process architecture per instance

## Next Steps

- **[Kubernetes Deployment](kubernetes)** — Auto-scaling with K8s
- **[Docker Deployment](docker)** — Container deployment
- **[Runtime Optimization](../runtime/optimization)** — Performance tuning

---

*LeafMesh — Scaling for production workloads*
