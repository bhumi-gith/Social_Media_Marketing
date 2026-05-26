# Deployment Overview

LeafMesh deployment requires Python, Redis, and LLM API access. This section covers requirements, deployment options, and operational considerations.

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.11 | 3.11 – 3.14 |
| Redis | 6.0+ | 7.0+ |
| Memory | 4GB | 8GB+ |
| LLM API Access | 1 provider | 2+ providers |

## Dependencies

**Required:**
- `aiohttp` — Async HTTP client
- `redis` — Redis client
- `pydantic` — Configuration validation
- `apscheduler` — Agent scheduling

**Optional:**
- `fastapi`, `uvicorn` — API services
- `pyyaml` — YAML configuration loading

Observability dependencies are bundled by LeafMesh — no extra packages required.

## Deployment Options

| Option | Best For |
|--------|----------|
| **Single process** | Development, small deployments |
| **Docker** | Reproducible deployments, CI/CD |
| **Kubernetes** | Production, auto-scaling, high availability |
| **Multi-instance** | Horizontal scaling with shared Redis |

## Minimal Deployment

```python
# app.py
import asyncio
from leafmesh import LeafMesh

leafmesh = LeafMesh.from_yaml("config.yaml")

async def main():
    await leafmesh.start()
    # Application logic...
    await leafmesh.stop()

asyncio.run(main())
```

With Redis running locally:

```bash
# Start Redis
redis-server

# Run the application
python app.py
```

## With API Server

```python
import asyncio
from leafmesh import LeafMesh

leafmesh = LeafMesh.from_yaml("config.yaml")

async def main():
    await leafmesh.start()
    # API server runs on port 18820 by default
    # Includes all service endpoints

asyncio.run(main())
```

## Network Requirements

- Redis: localhost:6379 (default) or cluster addresses
- LLM APIs: HTTPS to provider endpoints (api.openai.com, api.anthropic.com, etc.)
- API server: Port 18820 (configurable) for external access

## Next Steps

- **[Production Setup](production)** — Production configuration
- **[Docker Deployment](docker)** — Container deployment
- **[Kubernetes Deployment](kubernetes)** — Kubernetes orchestration
- **[Scaling](scaling)** — Scaling strategies

---

*LeafMesh — Deployment overview*
