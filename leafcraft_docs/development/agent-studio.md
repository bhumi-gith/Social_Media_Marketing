# Agent Studio

Agent Studio refers to the development environment and tools for building, testing, and iterating on LeafMesh agent configurations.

## Development Setup

### Project Structure

```
my_project/
├── configs/config.yaml       # Agent configuration
├── app.py                  # Application entry point
├── intelligence/           # Intelligence functions
│   ├── __init__.py
│   ├── triage.py
│   └── specialist.py
├── tools/                  # Custom tools
│   ├── __init__.py
│   └── database.py
├── processors/             # Pre-compose processors
│   ├── __init__.py
│   └── context.py
└── tests/                  # Test files
    ├── test_agents.py
    └── test_tools.py
```

### Minimal Entry Point

```python
import asyncio
from leafmesh import LeafMesh

leafmesh = LeafMesh.from_yaml("configs/config.yaml")

# Register intelligence functions
from intelligence.triage import triage_handler
from intelligence.specialist import specialist_handler

# Register custom tools
from tools.database import register_tools
register_tools()

async def main():
    await leafmesh.start()

    result = await leafmesh.mesh_call(
        "triage_agent",
        input_data={"user_message": "Test request"},
        session_id="dev_session"
    )
    print(result)
    await leafmesh.stop()

asyncio.run(main())
```

## Playground Service

LeafMesh includes an interactive playground for testing:

```python
from leafmesh import LeafMesh

leafmesh = LeafMesh.from_yaml("config.yaml")
await leafmesh.start()

# The playground_service provides endpoints for:
# - Testing agent configurations
# - Validating can_call chains
# - Testing pre-compose pipelines
# - Experimenting with different inputs
```

Access via the API server (default port: 18820).

## YAML Configuration Iteration

The `yaml_service` enables hot-reload of configurations:

```python
# Validate a new configuration without deploying
# POST /yaml/validate with YAML body

# Load a new configuration at runtime
# POST /yaml/load with YAML body
```

This allows iterating on agent prompts, yields schemas, and routing rules without restarting the system.

## Auto-Discovery

For larger projects, use auto-discovery to automatically register intelligence functions:

```python
leafmesh = LeafMesh.from_yaml("config.yaml")

# Auto-discover intelligence functions whose names match YAML agent names
# in the specified module path
leafmesh.discover("intelligence")
```

## Interactive Testing

Test individual agents interactively:

```python
async def test_agent():
    await leafmesh.start()

    # Test with different inputs
    test_cases = [
        {"user_message": "Simple question"},
        {"user_message": "Complex technical issue with database"},
        {"user_message": "Billing dispute for $5000"},
    ]

    for case in test_cases:
        result = await leafmesh.mesh_call(
            "triage_agent",
            input_data=case,
            session_id=f"test_{hash(str(case))}"
        )
        print(f"Input: {case['user_message'][:50]}")
        print(f"Output: {result}")
        print("---")

    await leafmesh.stop()
```

## Next Steps

- **[Testing Framework](testing)** — Automated testing
- **[Debugging Tools](debugging)** — Debugging techniques
- **[Agent Chat UI](chat-ui)** — Interactive chat interface

---

*LeafMesh — Development environment for agent building*
