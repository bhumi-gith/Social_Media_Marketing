# Redis Integration

Redis is the platform's state backend for business-logic data: sessions, conversation history, agent yields, mesh communications, and coordination decisions. Redis is configured in YAML and works automatically — no direct Redis calls are needed in your application code.

## Configuration

```yaml
redis:
  host: "localhost"
  port: 6379
  db: 0
  password: null
  auto_storage: true          # Auto-persist yields and conversation
  default_ttl: 3600           # 1 hour for general data
  session_ttl: 7200           # 2 hours for sessions
  cluster_mode: false         # Enable for Redis Cluster
  cluster_nodes: []           # Cluster node addresses

  # TLS / encryption-in-transit
  # Enable when your Redis server requires TLS (rediss://).
  ssl: false                          # Default: plaintext
  ssl_cert_reqs: required             # required | optional | none
  ssl_ca_certs: null                  # Path to CA bundle
  ssl_certfile: null                  # Client cert path (mTLS, optional)
  ssl_keyfile: null                   # Client key path (mTLS, optional)
  ssl_check_hostname: true            # Verify server hostname against cert
```

### TLS / Encryption in Transit

For SOC 2 / ISO 27001 deployments, Redis traffic must be encrypted. Set `ssl: true` and point `ssl_ca_certs` at your CA bundle:

```yaml
redis:
  host: "redis.internal.example.com"
  port: 6380                          # Common rediss:// port
  ssl: true
  ssl_cert_reqs: required             # Reject untrusted certs
  ssl_ca_certs: /etc/ssl/certs/redis-ca.crt
  ssl_check_hostname: true
```

Mutual TLS — pair `ssl_certfile` + `ssl_keyfile` to authenticate LeafMesh to Redis. `ssl_cert_reqs: none` exists for development only and disables peer verification entirely.

## Auto-Storage

When `auto_storage: true` (default), LeafMesh automatically persists all state without explicit save calls:

| Data | TTL |
|------|-----|
| Session metadata | `session_ttl` |
| Conversation history | `session_ttl` |
| Agent yields | `default_ttl` |
| Mesh communications | `default_ttl` |
| Coordination analyses | `default_ttl` |
| Coordination decisions | `default_ttl` |

## How It Works

When you call `await leafmesh.mesh_call(...)`, LeafMesh handles all persistence automatically:

1. **Session load/create** — Looks up or creates the session by `session_id`
2. **History retrieval** — Loads recent conversation messages for LLM context
3. **Yield storage** — After agent execution, stores structured yields
4. **Conversation recording** — Appends the exchange (role, content, timestamp, agent name)
5. **Mesh forwarding** — Records mesh communication data when `can_call` triggers downstream agents

## Inspecting Session Data

Browse sessions in **Studio's Sessions tab**, or query session state via the platform's REST API.

## Redis Cluster

For high-volume deployments, enable cluster mode:

```yaml
redis:
  cluster_mode: true
  cluster_nodes:
    - "redis-1:6379"
    - "redis-2:6379"
    - "redis-3:6379"
```

LeafMesh connects to the cluster and handles node routing transparently.

## Event Backbone

LeafMesh uses Redis as its event backbone for in-cluster coordination. You don't interact with the event topology directly — the platform handles it for you. See [Event System](../core-concepts/events) for the customer-facing event model.

## Requirements

- Redis 6.0+ minimum
- Redis 7.0+ recommended (improved performance and memory efficiency)
- Network connectivity from LeafMesh to Redis

## Next Steps

- **[Short-Term Memory](short-term)** — Session and state management
- **[State Management](state-management)** — State patterns in intelligence functions
- **[Event System](../core-concepts/events)** — Redis Streams architecture

---

*LeafMesh — Redis-backed persistence*
