# Production Setup

Configuration and operational practices for running LeafMesh in production.

## Production Configuration

```yaml
name: "production_system"
architecture: "managed_mesh"

redis:
  host: "redis.internal.example.com"
  port: 6379
  password: "${REDIS_PASSWORD}"      # Use environment variables
  auto_storage: true
  default_ttl: 3600
  session_ttl: 7200
  cluster_mode: true                  # Enable for high volume
  cluster_nodes:
    - "redis-1.internal:6379"
    - "redis-2.internal:6379"
    - "redis-3.internal:6379"

manager:
  enabled: true
  model: "gpt-4o-mini"
  prompt: |                          # Optional: tell the Manager what success looks like
    Escalate if the same issue loops more than twice.
  coordination_rules:
    max_agent_calls: 10

agents:
  triage:
    model: "gpt-4o-mini"
    max_tokens: 500
    temperature: 0.1
    # ... agent configuration

entry_points:
  - name: "api_request"
    target: "triage"
    description: "Primary API entry point"
```

## Application Entry Point

```python
import asyncio
import signal
from leafmesh import LeafMesh

leafmesh = LeafMesh.from_yaml("config.yaml")

async def main():
    await leafmesh.start()

    # Graceful shutdown handler
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))

    # Keep running until shutdown
    await asyncio.Event().wait()

async def shutdown():
    print("Shutting down gracefully...")
    await leafmesh.stop()

asyncio.run(main())
```

## Configuration Validation

LeafMesh validates all configuration at load time:

- **Type validation**: Pydantic checks all field types
- **Required fields**: Agents need `name` and `prompt` (LLM agents)
- **File size limits**: YAML files checked against 10MB limit
- **YAML syntax**: Parse errors reported with file location
- **Agent type validation**: Different required fields per agent type
- **Encoding validation**: UTF-8 enforced

Invalid configurations are rejected with descriptive errors before any components initialize.

## Security Considerations

### AST-Safe Condition Evaluation
YAML conditions use Python's `ast` module with whitelisted node types. No `eval()` anywhere.

### Permission-Based Tool Access
Each agent's tools are declared in YAML. Unauthorized tool calls are rejected at the executor level.

### Input Validation
`LeafMesh.from_yaml()` validates file existence, size, syntax, required fields, and Pydantic models before initialization.

### Token Limits
Per-agent `max_tokens` and `max_tool_calls_per_message` prevent cost runaway.

### Encryption in Transit
Redis traffic can run over TLS — set `redis.ssl: true` and point `ssl_ca_certs` at your CA bundle. Mutual TLS supported via `ssl_certfile` / `ssl_keyfile`. See [Redis Integration](../memory/redis-integration.md#tls--encryption-in-transit).

### Webhook Replay Protection
Signed webhook endpoints (`/webhook/{entry_point}`, `/callback/{agent_name}`) bind each request to a fresh timestamp + nonce. Captured signed requests cannot be replayed beyond the configured skew window. See [HITL Workflows](../human-in-loop/workflows.md) for the signing recipe.

### PII Redaction in Observability Data (default ON)
User content captured in observability data — agent inputs/outputs, tool inputs/outputs, LLM prompts, and retrieval payloads — is redacted by default before any data leaves the LeafMesh process. Configure additional patterns or disable specific categories in settings. See [Tracing](../observability/tracing.md#pii-redaction-default-on).

### Right to Erasure (GDPR Art. 17)
`LeafMesh.erase_session(session_id)` hard-deletes all persisted state for a session — session data, conversation history, agent outputs, mesh communications, channel mirrors, and pending callbacks. Emits a `session.erased` audit event with `actor_id` / `request_id` for SOC 2 CC7.2 traceability.

### Secrets Masking in Config Views
When config is surfaced for editing (e.g. Studio's config view), API keys, passwords, signing secrets, and connection strings are returned as `***REDACTED***`. Saving the config back leaves redacted fields untouched — the server keeps the existing value rather than overwriting with the placeholder.

### Hardening Knobs
See [Installation → Security & Hardening Knobs](../getting-started/installation.md#security--hardening-knobs) for the full env-var reference: rate limits, replay skew window, MCP allowlist, knowledge ingest caps, LLM timeout ceiling, cron min-interval, security headers, etc.

### Current Limitations
- No built-in API authentication on management endpoints — gate with a reverse proxy (nginx + auth_request, Cloudflare Access, etc.) before exposing to the public internet.
- No role-based access control (RBAC) inside LeafMesh.
- No external audit log forwarding out of the box (audit events are emitted to the platform's event feed; an operator-side consumer can mirror them to SIEM).
- License gate enforcement (free vs. paid tier feature gating) is not yet wired.

## Health Checks

The API server exposes health endpoints:

```json
{
  "status": "healthy",
  "components": {
    "backend": {"status": "connected", "latency_ms": 2},
    "scheduler": {"status": "running"}
  }
}
```

Integrate with load balancer health checks and Kubernetes probes.

## Environment Variables

Use environment variables for secrets:

```bash
export REDIS_PASSWORD="your_redis_password"
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

LeafMesh detects available providers by checking for API keys at startup.

## Next Steps

- **[Docker Deployment](docker)** — Container deployment
- **[Kubernetes Deployment](kubernetes)** — Kubernetes orchestration
- **[Scaling](scaling)** — Scaling strategies
- **[Monitoring](../observability/monitoring)** — Production monitoring

---

*LeafMesh — Production deployment guide*
