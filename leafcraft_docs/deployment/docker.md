# Docker Deployment

Deploy LeafMesh applications using Docker containers.

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY configs/config.yaml .
COPY app.py .
COPY intelligence/ ./intelligence/
COPY tools/ ./tools/

# Expose API port
EXPOSE 18820

CMD ["python", "app.py"]
```

## requirements.txt

```
leafmesh>=1.0.0
aiohttp>=3.8.0
redis>=4.5.0
pydantic>=2.0.0
apscheduler>=3.10.0
fastapi>=0.100.0
uvicorn>=0.22.0
pyyaml>=6.0
```

## Docker Compose

Run the application with Redis:

```yaml
version: "3.8"

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  app:
    build: .
    ports:
      - "18820:18820"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - redis

volumes:
  redis_data:
```

## Configuration for Docker

Update your YAML configuration to use environment-based Redis:

```yaml
redis:
  host: "${REDIS_HOST:-localhost}"
  port: 6379
```

Or configure in your application:

```python
import os
from leafmesh import LeafMesh

# Override Redis host from environment
config = LeafMesh.from_yaml("configs/config.yaml")
# Redis host is configured in YAML or detected from environment
```

## Building and Running

```bash
# Build the image
docker build -t my-swarm-app .

# Run with Docker Compose
docker compose up -d

# Check logs
docker compose logs -f app

# Stop
docker compose down
```

## Multi-Instance Deployment

Run multiple LeafMesh instances behind a load balancer:

```yaml
version: "3.8"

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  app:
    build: .
    deploy:
      replicas: 3
    environment:
      - REDIS_HOST=redis
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - redis

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app
```

## Health Check

Add a health check to your Docker configuration:

```yaml
services:
  app:
    build: .
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:18820/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

## Next Steps

- **[Kubernetes Deployment](kubernetes)** — Kubernetes orchestration
- **[Scaling](scaling)** — Scaling strategies
- **[Production Setup](production)** — Production configuration

---

*LeafMesh — Docker container deployment*
