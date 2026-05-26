# Multi-Agent Overview

LeafMesh is designed for multi-agent orchestration. Multiple agents work together through the managed mesh, with the control plane handling routing, validation, and coordination.

## Core Concepts

- **Agents are the data plane**: They execute tasks and produce structured outputs
- **The mesh is the control plane**: It routes traffic, enforces policies, and maintains state
- **Agents never communicate directly**: Every interaction crosses the control plane boundary

## Architecture: MANAGED_MESH

All LeafMesh deployments use the `MANAGED_MESH` architecture:

```
                    ┌─────────────────────────────────────┐
                    │           CONTROL PLANE              │
                    │                                      │
                    │  Routing       Condition evaluation  │
                    │  Coordination  Self-healing          │
                    │  Events        Scheduling            │
                    │                                      │
                    └────┬──────┬──────┬──────┬───────────┘
                         │      │      │      │
                    ┌────┴──┐ ┌─┴───┐ ┌┴────┐ ┌┴──────┐
                    │Agent A│ │Agent│ │Agent│ │Human  │
                    │ (LLM) │ │  B  │ │  C  │ │Agent D│
                    └───────┘ └─────┘ └─────┘ └───────┘
                              DATA PLANE
```

## Agent Communication Flow

```yaml
agents:
  triage:
    yields:
      category: "string"
      urgency: "number"
    can_call:
      - agent: "specialist"
        condition: "urgency >= 7"
      - agent: "general"
        condition: "urgency < 7"

  specialist:
    yields:
      analysis: "string"
    can_call:
      - agent: "human_review"
        condition: "true"

  general:
    yields:
      response: "string"
```

When triage produces `urgency: 8`:
1. The condition `urgency >= 7` matches
2. The platform routes the call to specialist
3. Specialist's yields are passed to human_review
4. The coordinator observes every event and intervenes only when needed
5. Session state and yields are persisted automatically

## Mixed Agent Types

A single system can combine all four agent types:

| Type | Purpose | Example |
|------|---------|---------|
| LLM | AI-powered processing | Triage, analysis, content generation |
| Programmatic | Deterministic logic | Data validation, calculations |
| Human | Manual review | Approvals, quality checks |
| Scheduled | Time-based activation | Monitoring, reports, maintenance |

## Coordination Components

The control plane provides automatic coordination:

- **Coordinator**: Observes every event and intervenes deterministically -- retry, halt, or escalate -- based on coordination rules you configure.
- **Self-healing**: Detects failures and executes graduated recovery actions.
- **Event delivery**: Real-time event propagation between components, with durable history for replay and audit.

## Next Steps

- **[Mesh Architecture](mesh-architecture)** — How the mesh works
- **[Agent Communication](communication)** — Routing and data flow
- **[Coordination Patterns](coordination)** — Automatic oversight and intervention
- **[Event Listeners](event-listeners)** — Trigger agents from Kafka, SQS, MQTT, Redis Streams, IMAP
- **[Scaling](scaling)** — Scaling multi-agent systems

---

*LeafMesh — Multi-agent orchestration through managed mesh*
