# Mesh Architecture

The managed mesh is the communication fabric that connects all agents in a LeafMesh deployment. The platform routes every inter-agent call through the control plane, enforces routing policies, and ensures that every agent interaction is observable and auditable.

## How Inter-Agent Calls Flow

LeafMesh routes all agent-to-agent calls through the control plane -- agents never talk to each other directly. From your code, an inter-agent call looks like a single function:

```python
# Direct mesh call (from intelligence functions)
result = await leafmesh.mesh_call(
    from_agent="coordinator",
    to_agent="specialist",
    input_data={"query": "analyze this data"},
    session_id="session_001"
)
```

The platform handles delivery, depth tracking, condition evaluation, and event publication.

## Condition Evaluation

`can_call` conditions are evaluated safely against the calling agent's yields:

```yaml
can_call:
  - agent: "specialist"
    condition: "urgency >= 7 and category == 'technical'"
```

- Conditions are parsed with a strict whitelist of operators
- `eval()` is never used -- conditions cannot execute arbitrary code from YAML
- Supports comparison, logical, membership, and string operations

## Routing Flow

```
Agent A completes execution
    │
    ▼
Yields parsed from LLM response
    │
    ▼
For each can_call rule:
    │
    ├── Evaluate condition against yields
    │
    ├── If condition matches:
    │   ├── call_immediately: true → Fire without waiting
    │   └── call_immediately: false → Queue for execution
    │
    └── If no conditions match: Chain ends
    │
    ▼
Mesh routes to target agent(s)
    │
    ▼
Target agent receives caller's yields as input_data
```

## Dual Response Pattern

Agents with `communication_type: "dual"` return two responses — one for the caller and one for the human/external system:

```yaml
agents:
  specialist:
    communication_type: "dual"
    yields:
      internal_analysis: "string"    # For downstream agents
      user_response: "string"        # For the end user
```

## Call Depth Control

The mesh tracks call depth to prevent infinite loops:

```yaml
manager:
  coordination_rules:
    max_agent_calls: 10    # Maximum calls per session
```

Each mesh call increments the depth counter. When the limit is reached, the coordinator prevents further calls.

## Mesh Communication Storage

Every mesh call is recorded automatically — which agents called which, with what data, and what came back. Query the history for any session through the REST API:

```bash
# Query mesh communications for a session
curl http://localhost:18820/mesh/{session_id}
```

You don't need to write any storage code — recording is handled automatically.

## Next Steps

- **[Agent Communication](communication)** — Data flow patterns
- **[Coordination Patterns](coordination)** — Automatic oversight and intervention
- **[Architecture](../core-concepts/architecture)** — System architecture overview

---

*LeafMesh — Managed mesh routing and policy enforcement*
