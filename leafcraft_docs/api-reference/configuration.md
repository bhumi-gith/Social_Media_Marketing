# Configuration API

Complete reference for LeafMesh YAML configuration schema. All configuration is validated through Pydantic models at load time.

## Top-Level: LeafMeshConfig

```yaml
name: "my_system"                    # Default: "default_mesh"
version: "1.0.0"                     # Default: "1.0.0"
architecture: "managed_mesh"         # Required: always "managed_mesh"
environment: "production"            # Default: "development"
debug: false                         # Default: false
log_level: "INFO"                    # Default: "INFO"
agents: {}                           # Required: agent definitions
manager: {}                          # Optional: coordination config
redis: {}                            # Optional: Redis config
mesh: {}                             # Optional: mesh network config
entry_points: []                     # Optional: external access points
data_structures: {}                  # Optional: custom data types
auto_discover:                       # Optional: auto-discover agent files
  directory: "./agents"
  pattern: "*_agent.py"
  recursive: true
observability: {}                    # Optional: observability config
```

## AgentConfig

### Required Fields

```yaml
agents:
  my_agent:
    name: "my_agent"                 # Required: unique identifier
```

### LLM Fields

```yaml
    model: "gpt-4o-mini"            # Default: "gpt-4o-mini"
    prompt: "Your instructions"      # System prompt (optional)
    description: "Agent purpose"     # Description (optional)
    temperature: 0.1                 # Default: 0.1
    max_tokens: 800                  # Default: 800
    max_completion_tokens: 1000      # For newer models (optional)
    reasoning: false                 # Chain-of-thought (default: false)
```

### Agent Type

```yaml
    agent_type: "llm"               # "llm" | "human" | "programmatic" | "external"
```

### External Agent Fields

```yaml
    agent_type: "external"
    framework: "crewai"             # "crewai" | "langgraph" | "autogen" | "custom"
    connector_config: {}            # Framework connection config
```

### Yields & Inputs

```yaml
    yields:                          # Expected output schema
      category: "string"
      confidence: "number"
      is_valid: "boolean"
    inputs:                          # Expected inputs (documentation)
      user_message: "string"
```

### Routing (can_call)

```yaml
    can_call:
      - agent: "target_agent"
        condition: "confidence >= 0.8 && category == 'technical'"
        call_immediately: false      # Default: false
```

Conditions support `&&` and `||` syntax (converted to `and`/`or` internally).

#### Condition Operators

| Type | Operators |
|------|-----------|
| Comparison | `==`, `!=`, `>`, `<`, `>=`, `<=` |
| Logical | `and`/`&&`, `or`/`||`, `not` |
| Arithmetic | `+`, `-`, `*`, `/`, `%` |
| Attribute | `calling_agent_response.field` (nested access) |
| Constants | `true`, `false`, `null` |

### Communication

```yaml
    communication_type: "dual"       # "dual" | "chain" | "execute"
    parallel: false                  # Enable parallel processing (default: false)
    auto_store_response: true        # Auto-store responses (default: true)
    auto_store_yields: true          # Auto-store yields (default: true)
```

### Tool Configuration

```yaml
    tools: ["calculator", "web_request"]
    tool_choice: "auto"              # "auto" | "none" | specific tool name
    max_tool_calls_per_message: 5    # Range: 0-20, default: 5
    tool_call_timeout: 30.0          # Range: 0.1-300 seconds
    allow_parallel_tool_calls: true  # Default: true
    tool_categories: ["math", "web"] # Tool categories to grant
```

### Adaptive Model Selection

```yaml
    optimization_strategy: "performance"  # "performance" | "cost" | "speed" | null
```

### Context Parts

Behavioral instructions injected as separate system messages alongside the agent's prompt. Shapes **how** the agent responds (tone, safety, flow-awareness) independently from **what** it does.

| Key | Label injected | Purpose |
|-----|---------------|---------|
| `care` | `[EMPATHY & TONE]` | Warmth and empathy instructions |
| `sentiment_analysis` | `[SENTIMENT ANALYSIS]` | Tone detection instructions |
| `guardrails` | `[SAFETY GUARDRAILS]` | Safety rules — what the agent must never do |
| `flows` | `[FLOW INSTRUCTIONS]` | Per-caller routing behaviour — what to do differently based on who called the agent |

Custom keys are also supported and receive an auto-generated label (`my_key` → `[MY KEY]`).

```yaml
    context_parts:
      care: |
        Always be empathetic. Acknowledge frustration before solving.
      sentiment_analysis: |
        Detect emotional tone. Adapt response to user mood.
      guardrails: |
        No PII disclosure. No internal system details. No timeline promises.
      flows: |
        When called from the entry point (no from_agent):
          - New user. Greet warmly and gather their primary need.
        When called from client (human agent):
          - Human has already responded. Skip re-greeting. Summarise and proceed.
        When called from scheduler_agent:
          - Scheduled run. Skip greeting entirely. Produce a structured summary.
```

All keys are optional — use any combination. See [Guardrails](../middleware/guardrails) for patterns.

### Human Agent Fields

```yaml
    agent_type: "human"
    is_human_powered: true
    human_interface: "webhook"       # "api" | "webhook" | "custom"
    human_timeout_seconds: 300       # Default: 300
    human_context_template: "..."    # Template for human context
    human_prompt_template: "..."     # Template for human prompts
    fallback_on_timeout: true        # Default: true
    fallback_response: {}            # Response if timeout
    require_human_confirmation: false # Default: false
    human_escalation_triggers: []    # Conditions for escalation
    webhook_config:
      outbound_url: "https://example.com/review"
      outbound_headers: {}
      outbound_timeout: 30           # Default: 30
      inbound_endpoint: "/webhook/greet_user"
      inbound_auth_token: "secret"
      response_mapping: {}
      max_retries: 3                 # Default: 3
      retry_delay: 5                 # Default: 5 seconds
```

### Scheduling

```yaml
    wake_up: "0 9 * * *"            # Cron | "every N seconds" | "daily"/"hourly"/"weekly"
```

## ManagerConfig

```yaml
manager:
  enabled: true                      # Default: true
  model: "gpt-4o-mini"             # LLM model for Manager analysis
  temperature: 0.1                   # Default: 0.1
  max_tokens: 800                    # Default: 800
  domain: "generic"                  # Manager domain specialization
  analysis_style: "coordination"     # Default: "coordination"
  prompt: |                          # Optional: evaluation criteria injected into every analysis
    This mesh handles customer support.
    Escalate if the same issue loops more than twice.
    Watch for advisor confidence scores below 0.6.
  coordination_rules: {}             # Custom rules
  chain_completion_timeout: 60.0     # Seconds before checking chain (default: 60)
  health_check_interval: 60          # Seconds between health checks
  agent_timeout_threshold: 180       # Seconds before agent timeout
  can_intervene: true                # Allow interventions (default: true)
  intervention_triggers:             # What triggers intervention
    - "mesh_loop_detected"
    - "coordination_rule_violation"
    - "agent_conflict"
  routing:                           # Routing authority (learning-based routing)
    mode: "static"                   # "static" (default) or "learning"
    memory_size: 100                 # Max routing decisions to track per pair
    confidence_threshold: 0.7        # Min success rate to keep a route
  escalation:                        # Escalation targets
    targets:
      - type: "human_agent"          # "human_agent" | "webhook" | "channel"
        agent: "senior_support"
        entry_point: "escalation_request"
      - type: "webhook"
        url: "https://api.example.com/escalate"
        method: "POST"
        headers:
          X-API-Key: "${ESCALATION_API_KEY}"
        payload_template:
          customer_id: "{{customer_id}}"
          severity: "critical"
      - type: "channel"
        provider: "slack"
        channel_id: "C0123456789"
        message_template: "Escalation: {{issue}}"
  human_input_rules:
    max_concurrent_requests: 3
    max_agent_requests: 5
    enable_request_queuing: true
  timeout_rules:
    max_timeouts_before_escalation: 2
    timeout_escalation_enabled: true
  workflow_pause_rules:
    max_pause_duration_minutes: 30
    max_concurrent_paused_workflows: 2
```

## MeshConfig

```yaml
mesh:
  call_timeout: 30                   # Per-call timeout seconds (default: 30)

  # Amazon Bedrock — route LLM calls through AWS Bedrock
  bedrock:
    region: "us-east-1"              # AWS region (default: us-east-1)
    profile: "prod"                  # Optional: AWS CLI profile
    endpoint_url: "https://..."      # Optional: VPC endpoint

  # Google Vertex AI — route LLM calls through Vertex AI
  vertex:
    project: "my-gcp-project"        # Required: GCP project ID
    location: "us-central1"          # GCP region (default: us-central1)

  # Microsoft Foundry — route LLM calls through Azure AI Foundry
  foundry:
    endpoint: "https://my-resource.openai.azure.com"  # Required: Foundry endpoint
    # api_version: "2024-10-21"                       # Optional: legacy versioned API
```

Use `bedrock/`, `vertex/`, or `foundry/` model prefixes on agents to route through these gateways:

```yaml
agents:
  via_bedrock:
    model: "bedrock/claude-3.5-sonnet"
  via_vertex:
    model: "vertex/gemini-2.5-flash"
  via_foundry:
    model: "foundry/gpt-4o"
```

## RedisConfig

```yaml
redis:
  host: "localhost"                  # Default: "localhost"
  port: 6379                        # Default: 6379
  db: 0                             # Default: 0
  password: null                    # Default: null
  decode_responses: true            # Default: true
  auto_storage: true                # Default: true
  default_ttl: 3600                 # Default: 3600
  session_ttl: 7200                 # Default: 7200
  cluster_mode: false               # Default: false
  cluster_nodes: []                 # Cluster addresses

  # TLS / encryption-in-transit
  ssl: false                        # Default: false (plaintext)
  ssl_cert_reqs: required           # required | optional | none
  ssl_ca_certs: null                # Path to CA bundle
  ssl_certfile: null                # Client cert (mTLS)
  ssl_keyfile: null                 # Client key (mTLS)
  ssl_check_hostname: true          # Default: true
```

## API Server

```yaml
api:
  cors_origins: []                  # Additional CORS origins
```

LeafMesh ships with a built-in CORS allowlist — `https://platform.leafcraft.ai` plus localhost dev ports (`3000`, `3001`, `5173`, `5174`, `8080`). Origins listed under `api.cors_origins` are appended to that default; you don't need to re-list the built-in entries.

```yaml
api:
  cors_origins:
    - https://my-internal-tool.example.com
    - https://staging-studio.acme.com
```

There is **no env var override**: the YAML key is the single extension point. The API server has no built-in authentication, so the allowlist policy is intentionally narrow — gate broader access via a reverse proxy with auth.

## Entry Points

```yaml
entry_points:
  - name: "support_request"         # Stable external name
    target: "triage_agent"          # Target agent
    description: "Description"
    condition: "always"             # When to trigger
```

## Complete Example

```yaml
name: "support_system"
version: "1.0.0"
architecture: "managed_mesh"
environment: "production"

agents:
  triage:
    name: "triage"
    model: "gpt-4o-mini"
    temperature: 0.1
    max_tokens: 800
    prompt: "Classify requests by urgency and category."
    yields:
      urgency: "number"
      category: "string"
    can_call:
      - agent: "specialist"
        condition: "urgency >= 7"

  specialist:
    name: "specialist"
    model: "gpt-4o"
    tools: ["web_request", "calculator"]
    max_tool_calls_per_message: 5
    prompt: "Provide detailed analysis."
    yields:
      analysis: "string"
      confidence: "number"

manager:
  enabled: true
  model: "gpt-4o-mini"
  coordination_rules:
    max_agent_calls: 10

mesh:
  max_call_depth: 5
  loop_detection: true

redis:
  host: "localhost"
  port: 6379

entry_points:
  - name: "support"
    target: "triage"
```

## Next Steps

- **[LeafMesh Class](leafmesh-adk)** — LeafMesh reference
- **[Agent Classes](agents)** — Agent API reference
- **[Configuration System](../core-concepts/configuration)** — Configuration overview

---

*LeafMesh — Configuration API reference*
