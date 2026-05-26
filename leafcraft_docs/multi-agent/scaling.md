# Scaling Strategies

Approaches for scaling LeafMesh deployments to handle increased load.

## Single-Process Architecture

The current LeafMesh architecture runs in a single Python process with async concurrency via `asyncio`. This means:

- All agents run in the same process
- Concurrency is achieved through async I/O (LLM calls, Redis operations, tool execution)
- CPU-bound work blocks the event loop

## Horizontal Scaling with Shared Redis

Multiple LeafMesh instances can share the same Redis backend:

```
                    ┌──────────┐
                    │  Redis   │
                    │ (shared) │
                    └────┬─────┘
                    ┌────┴─────┐
              ┌─────┤          ├─────┐
              │     │          │     │
         ┌────┴───┐│    ┌────┴───┐  │
         │ LeafMesh││    │ LeafMesh│  │
         │Instance││    │Instance│  │
         │   1    ││    │   2    │  │
         └────────┘│    └────────┘  │
                   │                │
              ┌────┴───┐      ┌────┴───┐
              │ LeafMesh│      │ LeafMesh│
              │Instance│      │Instance│
              │   3    │      │   4    │
              └────────┘      └────────┘
```

Each instance:
- Loads the same YAML configuration
- Connects to the same Redis instance/cluster
- Handles different sessions independently
- Shares auto-stored yields, mesh data, and session state

## Redis Cluster

For high-volume deployments, use Redis Cluster:

```yaml
redis:
  cluster_mode: true
  cluster_nodes:
    - "redis-1:6379"
    - "redis-2:6379"
    - "redis-3:6379"
```

LeafMesh handles node routing transparently. Data is distributed across cluster nodes based on key hash slots.

## Load Balancing Entry Points

Use the FastAPI services behind a load balancer:

```python
from leafmesh import LeafMesh

leafmesh = LeafMesh.from_yaml("config.yaml")

# Each instance runs its own API server
# Load balancer distributes requests across instances
await leafmesh.start()
api_server = leafmesh.api_server
```

Entry points provide stable names for external systems, while the load balancer distributes across LeafMesh instances.

## Scaling Considerations

| Concern | Approach |
|---------|----------|
| Session affinity | Not required — any instance can serve any session. Place instances behind any round-robin load balancer. |
| Agent state | Shared via Redis — any instance can process any session |
| Event processing | Cross-instance events propagate automatically through the shared backend |
| LLM rate limits | Distribute agents across instances to spread API calls |

## Provider-Based Scaling

Distribute load across LLM providers:

```yaml
agents:
  # High-volume agents on fast, cheap models
  triage_1:
    model: "gpt-4o-mini"
  triage_2:
    model: "gemini-2.0-flash"

  # Complex agents on capable models
  specialist:
    model: "claude-3.5-sonnet"
```

Different providers have independent rate limits, so spreading agents across providers increases total throughput.

## Current Limitations

- No built-in load balancing across LeafMesh instances
- No automatic instance coordination (each instance operates independently)
- Horizontal scaling requires external orchestration (Kubernetes, Docker Swarm, etc.)
- Redis becomes the bottleneck for extremely high-volume deployments

## Next Steps

- **[Docker Deployment](../deployment/docker)** — Container deployment
- **[Kubernetes Deployment](../deployment/kubernetes)** — Kubernetes orchestration
- **[Redis Integration](../memory/redis-integration)** — Redis configuration

---

*LeafMesh — Scaling multi-agent deployments*
