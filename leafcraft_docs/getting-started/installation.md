# LeafMesh Installation

LeafMesh is distributed via **PyPI**. A valid **license key** is required to run LeafMesh.

## Quick Install

```bash
pip install leafmesh
```

Everything is included out of the box — all LLM providers (OpenAI, Anthropic, Google, Bedrock, Vertex, Microsoft Foundry) and all framework connectors (MCP, CrewAI, LangGraph, AutoGen, A2A, Composio, Zapier, n8n).

## Project Scaffolding (Recommended)

The fastest way to get started is with the `create-leafmesh` CLI:

```bash
pip install create-leafmesh
create-leafmesh my-project
cd my-project
```

This generates a complete project with:
- `configs/config.yaml` — Agent definitions and mesh wiring
- `agency/` — Auto-discovered agent implementations
- `main.py` — Entry point script
- `.env` — Environment variable template
- `requirements.txt` — Dependencies

## Requirements

### System Requirements

- **Python**: 3.11 – 3.14
- **Redis**: 6.0+ (7.0+ recommended)
- **OS**: Linux, macOS, Windows (WSL recommended)
- **Memory**: 4GB minimum, 8GB+ recommended

### Core Dependencies (Included)

All of these are installed automatically with `pip install leafmesh`:

- `pydantic>=2.0.0` — Data validation
- `redis>=5.0.0` — State management
- `PyYAML>=6.0.0` — Configuration
- `openai>=1.0.0` — Default LLM provider
- `structlog>=23.0.0` — Structured logging
- `aiohttp>=3.9.0` — Async HTTP
- **Observability** — Managed observability pipeline included by default

### Redis Setup

```bash
# macOS
brew install redis && redis-server

# Ubuntu/Debian
sudo apt-get install redis-server && redis-server

# Docker (recommended)
docker run -d -p 6379:6379 redis:7-alpine
```

## Environment Variables

```bash
# Required
export LEAFMESH_LICENSE_KEY="XXXX-XXXX-XXXX-..."    # License key (validated at startup)
export OPENAI_API_KEY="sk-..."                        # OpenAI API key

# Optional
export LEAFMESH_ENV_TOKEN="production"                # Environment identifier (default: "default")
export LEAFMESH_WEBHOOK_SECRET="..."                  # Webhook signing secret (rotate via Studio settings)

# Optional provider keys
export ANTHROPIC_API_KEY="sk-ant-..."                 # For Claude models
export GOOGLE_API_KEY="..."                           # For Google models

# Cloud gateway providers
export AWS_ACCESS_KEY_ID="..."                        # For Bedrock (or use IAM role / ~/.aws/credentials)
export AWS_SECRET_ACCESS_KEY="..."
export GOOGLE_CLOUD_PROJECT="my-project"              # For Vertex AI (or configure in mesh.vertex.project)
export GOOGLE_APPLICATION_CREDENTIALS="/path/key.json" # For Vertex AI (or use gcloud auth / GKE SA)

# Microsoft Foundry (Azure AI Foundry)
export AZURE_FOUNDRY_API_KEY="..."                     # API key from Azure Portal
# export AZURE_FOUNDRY_TOKEN="..."                     # Or Entra ID Bearer token
```

### Security & Hardening Knobs

All optional with safe defaults. Most operators won't need to touch any of these — they're documented here so you can tune them for your compliance regime.

```bash
# Observability — content redaction (defaults: ON; user content stripped from
# exported telemetry before it leaves the process).
export LEAFMESH_OTEL_REDACT_PII=1                       # 0 to ship raw content
export LEAFMESH_DISABLE_PROMPT_GUARDRAIL=0              # 1 disables prompt-injection guardrails

# Webhook hardening (signed payloads + replay protection)
export LEAFMESH_WEBHOOK_ALLOW_LEGACY_HMAC=0             # 1 to keep accepting legacy signatures
export LEAFMESH_WEBHOOK_REPLAY_SKEW_S=300               # default; configurable timestamp window
export LEAFMESH_WEBHOOK_RATE_LIMIT_MAX=60               # per-IP request limit
export LEAFMESH_WEBHOOK_RATE_LIMIT_WINDOW_S=60          # window in seconds
export LEAFMESH_WEBHOOK_MAX_PAYLOAD_BYTES=1048576       # 1 MiB

# Knowledge ingest / query caps
export LEAFMESH_KNOWLEDGE_MAX_DOCS_PER_INGEST=1000
export LEAFMESH_KNOWLEDGE_MAX_DOC_BYTES=2097152         # 2 MiB
export LEAFMESH_KNOWLEDGE_MAX_INGEST_TOTAL_BYTES=52428800 # 50 MiB
export LEAFMESH_KNOWLEDGE_QUERY_RATE_LIMIT_MAX=120
export LEAFMESH_KNOWLEDGE_QUERY_RATE_LIMIT_WINDOW_S=60

# LLM hard timeout (ceiling enforced on every LLM provider call)
export LEAFMESH_LLM_HARD_TIMEOUT_S=300

# Cron min-interval — schedules below this floor are rejected
export LEAFMESH_CRON_MIN_INTERVAL_SECONDS=60

# MCP subprocess allowlist (comma-separated absolute paths or basenames)
export LEAFMESH_MCP_COMMAND_ALLOWLIST=                  # empty = warn-only

# Teams adapter — fail-closed by default
export LEAFMESH_TEAMS_ALLOW_UNVERIFIED=0                # 1 only for local dev

# YAML env-var expansion blocklist (prevents YAML from reading credential env vars)
export LEAFMESH_YAML_ENV_BLOCKLIST=                     # empty disables, "" disables, otherwise prefix list
export LEAFMESH_YAML_ENV_BLOCKLIST_EXTRA=               # extend the default blocklist

# Conversation history hard byte cap (per session, on top of message-count cap)
export LEAFMESH_MAX_SESSION_HISTORY_BYTES=5242880       # 5 MiB

# Security headers
export LEAFMESH_HSTS_ENABLED=1
export LEAFMESH_REFERRER_POLICY=no-referrer
export LEAFMESH_CSP="default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
```

CORS origins are **not** configurable via env — use `api.cors_origins` in `config.yaml` instead. See [Configuration → API Server](../api-reference/configuration.md#api-server).

## License Activation

LeafMesh validates your license key against the LeafCraft auth backend at platform startup. If the key is invalid or expired, LeafMesh raises `LeafMeshLicenseError` and refuses to boot.

```python
import asyncio
from leafmesh import LeafMesh

async def main():
    leafmesh = LeafMesh.from_yaml("configs/config.yaml")
    await leafmesh.start()   # License validated here
    print("LeafMesh started successfully!")
    await leafmesh.stop()

asyncio.run(main())
```

**License types:**
- **Starter** — Free tier with basic features
- **Pro** — Extended features and retention
- **Enterprise** — Full features, dedicated support

Contact `info@leafcraft.ai` for license inquiries.

## Verification

After installation, verify everything works:

```python
import asyncio
from leafmesh import LeafMesh

async def verify():
    leafmesh = LeafMesh.from_yaml("configs/config.yaml")
    try:
        await leafmesh.start()
        print("LeafMesh started successfully!")
        print(f"API docs: http://127.0.0.1:18820/docs")
    finally:
        await leafmesh.stop()

asyncio.run(verify())
```

## Troubleshooting

### License Validation Failed
```
LeafMeshLicenseError: Invalid or expired license key
```
- Verify `LEAFMESH_LICENSE_KEY` is set correctly
- Check that your machine has outbound internet access for license validation

### Redis Connection Failed
```bash
redis-cli ping  # Should return "PONG"
```

### Import Errors
```bash
pip show leafmesh  # Verify installation
pip install --upgrade leafmesh  # Upgrade to latest
```

## Next Steps

1. **[Quick Start Guide](quickstart)** — Build your first mesh in 5 minutes
2. **[Architecture Guide](../core-concepts/architecture)** — How the control plane works
3. **[Agent Development](../agents/development)** — Create custom agents
4. **[Examples](../examples/customer-service)** — Real-world implementations

---

*LeafMesh — YAML-native multi-agent orchestration platform*
