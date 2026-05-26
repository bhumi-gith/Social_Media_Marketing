# Design Philosophy

LeafMesh is built on a set of architectural principles that guide every design decision. Understanding these principles helps you build better multi-agent systems.

## Configuration Over Code

Multi-agent systems are configured declaratively through YAML, not built imperatively through code. Agent definitions, routing rules, model assignments, and coordination settings live in version-controllable configuration files.

```yaml
agents:
  triage:
    name: "triage"
    model: "gpt-4o-mini"
    yields:
      category: "string"
      urgency: "number"
    can_call:
      - agent: "specialist"
        condition: "urgency >= 7"
```

**Why this matters:**
- Configuration changes don't require code deployments
- Non-developers can review and modify agent behavior
- The same YAML works across development, staging, and production
- Git diffs show exactly what changed in agent definitions

## Control Plane / Data Plane Separation

Agents never communicate directly. All coordination flows through the control plane — observation, coordination, mesh routing, and the event system. Agents only know about their own yields and can_call rules.

```
Agent A ──yields──▶ Control Plane ──evaluates can_call──▶ Agent B
                      │
                      ├── Observation (classifies events)
                      ├── Coordination (decides interventions)
                      └── Internal event backbone
```

**Why this matters:**
- Adding or removing agents doesn't require changing other agents
- The control plane can reroute traffic without agent awareness
- Self-healing can restart or replace agents transparently
- Every interaction is recorded and queryable via REST for debugging

## Deterministic Boundaries Around Non-Deterministic Systems

LLMs are non-deterministic. LeafMesh wraps them in deterministic mechanisms:

| Layer | Mechanism | What It Enforces |
|-------|-----------|-----------------|
| **Yields** | Schema parsing | Output structure (correct fields and types) |
| **Pre-compose** | Python processors | What the LLM sees (controlled input) |
| **Intelligence** | Intelligence function (name = agent name) | What downstream agents receive (controlled output) |
| **Conditions** | AST-safe evaluator | Routing logic (deterministic evaluation) |
| **Observation** | Anomaly classification | Coordination signal |
| **Coordination** | Deterministic logic | Intervention decisions |

The intelligence function is the key mechanism. It runs **after** the LLM call and can modify, validate, or replace the LLM's response entirely:

```python
async def solver(llm_response, input_data, context):
    # Deterministic math — LLM is only the fallback
    problem = input_data.get("problem", "")
    if "+" in problem:
        numbers = [float(n) for n in re.findall(r'-?\d+\.?\d*', problem)]
        if len(numbers) == 2:
            return {"answer": numbers[0] + numbers[1], "confidence": 1.0}

    return llm_response  # Fall back to LLM for complex cases
```

**Why this matters:**
- Deterministic tasks (calculations, validation, API calls) never depend on LLM accuracy
- LLM hallucination is contained — wrong format is caught by yields parsing, wrong content can be caught by intelligence functions
- The system's behavior is predictable at the routing level even when individual LLM responses vary

## Mixed Agent Types

Not every agent needs an LLM. LeafMesh supports four agent types that share the same mesh interface (yields, can_call, condition evaluation):

| Type | LLM Call | Best For |
|------|----------|----------|
| llm | Yes | Analysis, generation, classification |
| programmatic | No | Calculations, API calls, data processing |
| human | No (waits for human) | Approvals, quality review, escalation |
| external | Depends on connector | Bridging to external agent frameworks |

A data pipeline might use programmatic agents for validation and transformation (zero LLM cost), then an LLM agent only for the final summary. A support system might use an LLM for triage, then a human agent for approval.

**Why this matters:**
- LLM calls are expensive — use them only where non-deterministic reasoning is needed
- Programmatic agents are fast, cheap, and deterministic
- Human agents keep humans in the loop for high-stakes decisions
- All four types route through the same mesh, so mixing is natural

## Graduated Response to Failure

When things go wrong, the system responds proportionally:

1. **Yields parsing fails** → Retry the LLM call with the same prompt
2. **Agent error** → Automatic coordination decisions handle retry, rerouting, or escalation
3. **Repeated failures** → Self-healing restarts or replaces the agent
4. **Persistent failures** → Self-healing isolates the agent and brings up a backup
5. **Provider outage** → Other providers' agents continue operating

The self-healing system is event-driven — it only activates when errors occur, with zero overhead during normal operation.

**Why this matters:**
- Transient errors are handled automatically without human intervention
- Systematic failures trigger graduated responses (restart → backup → quarantine)
- Individual agent failures don't cascade into system-wide failures
- Provider outages only affect agents using that provider

## State is Explicit and Inspectable

All durable state — sessions, conversation history, agent yields, mesh communications, coordination decisions — is exposed through REST endpoints. Nothing is hidden in memory or log files.

To debug "why did Agent B give the wrong answer?":
1. Fetch the session's conversation history (`/session/{id}`)
2. Fetch each agent's yields in the chain (`/yields/{id}/{agent}`)
3. Inspect the mesh history via the API
4. Review coordination decisions through the API

Operational metrics (latency, throughput) flow to the managed observability pipeline, kept separate from business state. This separation means storage tuning and telemetry scaling are independent concerns.

## Multi-Provider by Design

Different agents can use different LLM providers. This is not just a convenience — it's a resilience mechanism:

- **Bias reduction**: Different models have different failure modes
- **Cost optimization**: Use expensive models only where needed
- **Provider redundancy**: An outage in one provider doesn't take down the system
- **Capability matching**: Different models excel at different tasks

```yaml
agents:
  triage:
    model: "gpt-4o-mini"         # Fast, cheap classification
  specialist:
    model: "claude-3.5-sonnet"    # Strong reasoning
  classifier:
    model: "gpt-4o-mini"         # High-throughput classification
```

## What LeafMesh Does Not Do

Understanding limitations is as important as understanding capabilities:

- **Does not prevent semantic hallucination.** Yields parsing catches structural errors (wrong format, missing fields), not factual errors. Tool calling reduces but doesn't eliminate this.
- **Does not replace domain expertise.** Configuration still requires understanding your domain, your agents' roles, and your routing logic.
- **Does not auto-optimize prompts.** Evolution runs your test scenarios on your current configuration to surface quality drift over time — it does not rewrite prompts.
- **Does not guarantee LLM quality.** The system provides structural mechanisms to detect, contain, and mitigate LLM failures — not to eliminate them.

## Next Steps

- **[Quick Start](quickstart)** — Build your first multi-agent system
- **[Architecture Guide](../core-concepts/architecture)** — Control plane internals
- **[Agent Types](../agents/overview)** — All four agent types in detail

---

*LeafMesh — Deterministic control over non-deterministic systems*
