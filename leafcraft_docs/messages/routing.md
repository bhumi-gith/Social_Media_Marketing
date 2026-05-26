# Message Routing

Messages in LeafMesh flow through the control plane, never directly between agents. Routing is determined by `can_call` conditions evaluated against agent yields.

## Routing Flow

```
Agent A produces yields
    │
    ▼
Condition evaluation
    │  Evaluates can_call conditions against yields
    │
    ├── condition: "urgency >= 7" → true  → Agent B called
    ├── condition: "category == 'billing'" → false → skipped
    └── condition: "satisfaction < 4" → true → Agent C called
```

## Declarative Routing

Routing rules are declared in YAML, not code:

```yaml
agents:
  triage:
    yields:
      urgency: "number"
      category: "string"
    can_call:
      - agent: "specialist"
        condition: "urgency >= 7"
        call_immediately: true
      - agent: "general_handler"
        condition: "urgency < 7"
```

## Condition Evaluation

Conditions are evaluated through the platform's secure expression evaluator. Expressions are parsed and executed against a strict allow-list of safe operations — `eval()` is never used, so YAML-authored conditions cannot escape into arbitrary code execution.

### Supported Operators

| Category | Operators | Example |
|----------|-----------|---------|
| Comparison | `==`, `!=`, `<`, `<=`, `>`, `>=` | `urgency >= 7`, `count == 0` |
| Boolean | `and`, `or`, `not`, `&&`, `\|\|` | `is_valid and count > 0` |
| Arithmetic | `+`, `-`, `*`, `/`, `%` | `score * 100 > 80` |
| Unary | `-x`, `+x`, `not x` | `not failed` |
| Chained | `low <= x <= high` | `0.5 <= confidence <= 0.9` |
| Nested attribute | `obj.field` | `calling_agent_response.score >= 0.7` |

`&&` and `||` are normalized to `and`/`or` before parsing — both forms work.

### Evaluation Context

Variables available inside a condition:

| Variable | Source |
|----------|--------|
| Top-level yields | The producing agent's parsed `yields` (e.g. `category`, `urgency`) |
| `calling_agent_response` | The full agent response dict — supports nested access (`calling_agent_response.score`) |
| Nested `yields` keys | If the response wraps yields under `yields:`, those keys are also lifted to the top scope |
| Nested `response` keys | If the response wraps fields under `response:`, those keys are also lifted to the top scope |
| Session context | Anything passed in `context` (lower priority than yields — yields override context if names collide) |
| `true`, `false`, `null` | YAML-style literals (also normalized to Python `True`, `False`, `None`) |

### Condition Cookbook

```yaml
# 1. Boolean check (yields a boolean directly)
condition: "approved"
condition: "not failed"

# 2. Numeric comparison
condition: "urgency >= 7"
condition: "confidence > 0.8"

# 3. Range (chained)
condition: "0.5 <= confidence <= 0.9"

# 4. String equality (single OR double quotes)
condition: "category == 'billing'"
condition: 'category == "billing"'

# 5. Compound (and / or / not)
condition: "category == 'tech' and urgency >= 5"
condition: "needs_escalation or risk_level == 'high'"
condition: "not approved"

# 6. Arithmetic in expressions
condition: "score * 100 > 80"
condition: "retries % 3 == 0"

# 7. Nested attribute access (full upstream response)
condition: "calling_agent_response.confidence >= 0.7"

# 8. Always-true (omit condition or use literal true)
condition: "true"
# (or simply omit the field — empty/missing = always callable)
```

### Empty / Missing Conditions

Omit `condition:` (or set it to an empty string) and the route is **always callable**. Use this when you want unconditional fan-out:

```yaml
can_call:
  - agent: "audit_logger"      # no condition → always called
  - agent: "primary_handler"
    condition: "category == 'support'"
```

### Failure Modes

| Situation | Behavior |
|-----------|----------|
| Variable not in context | Logs warning, condition returns `false`, route is skipped |
| Syntax error in expression | Logs warning, condition returns `false` |
| Unsupported operation (e.g. function call, lambda, subscript, comprehension) | Rejected by the evaluator, condition returns `false` |
| Access to a private attribute (`_x`, `__y`) | Blocked, condition returns `false` |
| Division / modulo by zero | Logs warning, condition returns `false` |
| Dot-path against missing key (e.g. `qualification.match_score` when `qualification` is None or `{}`) | Logs warning, condition returns `false`. See **[Auto-wrap for single object yields](../api-reference/agent-config-fields#auto-wrap-flat-llm-output-under-a-single-object-yield)** — the SDK fixes this automatically when the schema declares one `object` yield and the LLM returned a flat dict without the wrapper |

### When a Condition "Should Have" Matched but Didn't

If `can_call` dispatches **zero** routes, the [narration layer](#narration-routing) takes over and recommends a fallback target — the "things didn't go as planned, here's what to do next" path. That can look like the wrong agent firing.

The two most common causes when this happens unexpectedly:

1. **Yields shape mismatch.** Your LLM returned a different shape than your `yields:` declared, so the field the condition reads is `None` or empty. Look for a `YIELDS: <agent> produced incomplete output` warning right before the narration kicks in. The fix is in the agent's `yields:` schema or its prompt — see [Accessing Yields in Conditions](../api-reference/agent-config-fields#accessing-yields-in-can-call-conditions).
2. **Genuine condition miss.** Your output was correct but no `condition` matched. That's the intended path for narration to fire as a fallback.

Function calls, deep attribute chains (`a.b.c`), subscripts (`a[0]`), and any non-comparison operations are intentionally rejected. Conditions are predicates over yields — not a general-purpose scripting layer.

### Security Notes

- Conditions run through a secure expression evaluator — never `eval()`/`exec()`.
- Only an allow-listed set of comparison, boolean, arithmetic, and one-level attribute operations are permitted.
- Private/dunder attribute access (`obj._private`, `obj.__class__`) is blocked.
- Condition strings round-trip through YAML — embedded newlines, quotes, and unicode are preserved verbatim.

## Synchronous vs Asynchronous

- **`call_immediately: true`**: Downstream agent is called synchronously within the current pipeline
- **Default (false)**: Downstream calls are dispatched asynchronously

## Dual Response Pattern

With `communication_type: "dual"`, the agent returns its response immediately while can_call chains execute in the background:

```yaml
communication_type: "dual"
```

## Learning-Based Routing

By default, routing is **static** — all matching `can_call` targets are called. With `routing.mode: "learning"`, the platform learns from past outcomes and filters targets based on historical success rates.

```yaml
manager:
  routing:
    mode: "learning"
    confidence_threshold: 0.7
```

When learning mode is active, the routing flow becomes:

```
Agent A produces yields
    │
    ▼
Condition evaluation → 3 targets match conditions
    │
    ▼
Learning filter narrows by success rate
    │
    ├── Agent B: 92% success → keep
    ├── Agent C: 45% success → filter out (below 0.7)
    └── Agent D: no history  → keep (explore new routes)
    │
    ▼
Only B and D are called
```

Routing decisions are automatically evaluated and fed back into the learning layer. No additional code is needed — the system self-improves over time.

See **[Manager — Routing Authority](../core-concepts/manager)** for full configuration details.

## Narration Routing

Conditions handle **definitive** routes — boolean expressions you can pin down. But some routing logic is fuzzy, contextual, or based on tone and intent. For these, use `narration` — an agent-level field with plain-English routing hints.

```yaml
agents:
  triage:
    yields:
      category: "string"
      urgency: "number"
    can_call:
      - agent: "billing_agent"
        condition: "category == 'billing'"
      - agent: "technical_agent"
        condition: "category == 'technical'"
    narration: >
      If the customer mentions cancelling, route to retention_agent.
      If the customer mentions a competitor by name, route to win_back_agent.
```

### Priority

1. **Conditions first** — evaluated by the control plane, dispatched instantly, never re-evaluated
2. **Narration second** — evaluated by the platform's coordination layer, which dispatches any additional targets it identifies

Narration targets are **additive**. They never override or remove condition-based routing.

### Narration Can Reference Any Agent

Narration is not limited to agents in `can_call`. The coordination layer can see every registered agent in the mesh, so narration hints can reference any of them.

## Direct Mesh Calls

From intelligence functions, bypass declarative routing with direct calls:

```python
result = await leafmesh.mesh_call(
    from_agent="coordinator",
    to_agent="verifier",
    data={"claim": "..."},
    session_id=context.get("session_id")
)
```

## Next Steps

- **[Agent Communication](../multi-agent/communication)** — Full communication patterns
- **[Agent Configuration](../api-reference/agent-config)** — can_call reference

---

*LeafMesh — Declarative routing, secure expression evaluation*
