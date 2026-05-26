# Context Threading

Context threading supports parallel processing patterns where multiple agents work on different aspects of a problem simultaneously within the same session.

## How It Works

The system creates session "threads" that inherit context from parent sessions while maintaining independent execution paths. Thread results are merged back into the parent session on completion.

```
Parent Session (user_123)
    |
    |-- Thread A: Technical Analysis
    |   (inherits context, independent execution)
    |
    |-- Thread B: Financial Analysis
    |   (inherits context, independent execution)
    |
    +-- Thread C: Risk Assessment
        (inherits context, independent execution)
        |
        v
    Results merged back to parent session
```

## Use Cases

- **Parallel analysis**: Multiple specialist agents analyze the same input simultaneously
- **Fan-out / fan-in**: One agent distributes work, waits for parallel results, then synthesizes
- **Independent subtasks**: Complex requests decomposed into independent pieces

## Implementing with YAML Configuration

Context threading is configured through `can_call` rules. When an agent calls multiple downstream agents, they execute with shared session context:

```yaml
agents:
  coordinator:
    name: "coordinator"
    model: "gpt-4o"
    can_call:
      - agent: "technical_analyst"
        condition: "always"
      - agent: "financial_analyst"
        condition: "always"
      - agent: "risk_assessor"
        condition: "always"

  technical_analyst:
    name: "technical_analyst"
    model: "gpt-4o-mini"
    yields:
      technical_score: "number"
      findings: "array"

  financial_analyst:
    name: "financial_analyst"
    model: "gpt-4o-mini"
    yields:
      financial_score: "number"
      projections: "array"

  risk_assessor:
    name: "risk_assessor"
    model: "gpt-4o-mini"
    yields:
      risk_level: "string"
      factors: "array"
```

The coordinator's intelligence function can synthesize parallel results:

```python
async def coordinator(llm_response, input_data, context):
    # Results from parallel agents arrive via the mesh
    return {
        "summary": llm_response.get("summary", ""),
        "recommendation": llm_response.get("recommendation", "")
    }
```

## Next Steps

- **[State Management](state-management)** — State patterns
- **[Session Management](../core-concepts/sessions)** — Session lifecycle
- **[Multi-Agent Coordination](../multi-agent/coordination)** — Coordination patterns

---

*LeafMesh — Parallel processing with shared context*
