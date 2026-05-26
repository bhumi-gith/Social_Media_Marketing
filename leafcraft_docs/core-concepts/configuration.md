# Configuration System

LeafMesh uses YAML as its primary configuration interface. All agent definitions, routing rules, Redis settings, and system options are declared in a single YAML file validated at load time.

## Loading Configuration

```python
from leafmesh import LeafMesh

# From YAML file (recommended)
leafmesh = LeafMesh.from_yaml("config.yaml")

# From Python dictionary
leafmesh = LeafMesh.from_dict({"name": "my_swarm", "architecture": "managed_mesh", "agents": {...}})
```

## Configuration Structure

```yaml
# Required
name: "my_swarm"                   # Unique swarm identifier
architecture: "managed_mesh"       # Architecture pattern
agents: {}                         # Agent definitions

# Optional
version: "1.0.0"                   # Config version

redis:                             # Redis connection
  host: "localhost"
  port: 6379
  db: 0
  password: null
  auto_storage: true               # Auto-persist yields and conversation
  default_ttl: 3600                # TTL for general data (seconds)
  session_ttl: 7200                # TTL for sessions (seconds)
  cluster_mode: false
  cluster_nodes: []

manager:                           # Automatic coordination & oversight
  enabled: true
  model: "gpt-4o-mini"            # Model used for event classification
  prompt: |                        # Optional: evaluation criteria
    Escalate if the same issue loops more than twice.
  coordination_rules:
    max_response_time: 30

mesh:                              # Mesh communication
  call_timeout: 60
  max_retries: 2

observability:                     # Built-in observability
  enabled: true
  tracing_enabled: true
  service_name: "my_swarm"
  metrics_retention_minutes: 1440

self_healing:                      # Automatic recovery
  enabled: true
  detection_interval: 15
  max_recovery_attempts: 5
  recovery_strategies:
    - "restart_agent"
    - "failover_to_backup"
    - "circuit_breaker"

entry_points:                      # Named API endpoints
  - name: "customer_inquiry"
    target: "triage_agent"
    description: "Incoming customer inquiries"
```

## Validation

Configuration is validated at load time. Validation includes:

- **Type checking**: All fields are type-checked
- **Required fields**: `name` and `agents` are required; LLM agents require `name` and `prompt`
- **Default values**: Sensible defaults for optional fields (`temperature: 0.1`, `session_ttl: 7200`)
- **File size limits**: YAML files are checked against a 10MB limit
- **YAML syntax**: Parse errors are caught with file location
- **Encoding**: UTF-8 encoding is validated

```python
try:
    leafmesh = LeafMesh.from_yaml("config.yaml")
except ConfigError as e:
    print(f"Configuration error: {e}")
```

## Environment-Specific Configuration

Use separate YAML files per environment:

```
configs/
├── development.yaml     # gpt-4o-mini, short TTLs
├── staging.yaml         # Production models, test Redis
└── production.yaml      # Full configuration
```

```python
import os
env = os.getenv("ENVIRONMENT", "development")
leafmesh = LeafMesh.from_yaml(f"configs/{env}.yaml")
```

### Development

```yaml
name: "my_swarm_dev"
redis:
  host: "localhost"
  session_ttl: 300            # Short TTL for dev

agents:
  solver:
    name: "solver"
    model: "gpt-4o-mini"      # Cost-effective for testing
    temperature: 0.1
```

### Production

```yaml
name: "my_swarm_prod"
redis:
  host: "redis.internal.company.com"
  password: "${REDIS_PASSWORD}"
  session_ttl: 7200
  cluster_mode: true
  cluster_nodes:
    - "redis-1:6379"
    - "redis-2:6379"
    - "redis-3:6379"

self_healing:
  enabled: true
  detection_interval: 10

# Observability is built-in and auto-enabled by your license key

## Runtime Configuration

### Hot-Reload via API

The `yaml_service` API enables uploading new YAML configurations and hot-reloading agent definitions without system restarts.

### Dynamic Scheduling

```python
leafmesh.schedule_agent("collector", "every 60 seconds")
leafmesh.unschedule_agent("collector")
```

## Next Steps

- **[Agent Configuration](../api-reference/agent-config)** — Complete agent YAML reference
- **[Architecture](architecture)** — How configuration maps to runtime components
- **[Installation](../getting-started/installation)** — Setting up your environment

---

*LeafMesh — YAML-first configuration, validated at load time*
