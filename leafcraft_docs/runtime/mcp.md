# Model Context Protocol (MCP)

LeafMesh's context management follows structured patterns for assembling, routing, and managing context across multi-agent workflows.

## Context Flow Architecture

In a multi-agent system, context flows through the mesh via structured yields and session state:

```
User Request
    │
    ▼
Entry Agent (receives raw input)
    │ yields: {category, urgency, summary}
    │
    ▼ (can_call condition met)
Specialist Agent (receives upstream yields as input_data)
    │ yields: {analysis, resolution, confidence}
    │
    ▼ (can_call condition met)
Review Agent (receives specialist yields as input_data)
    │ yields: {approved, feedback}
    │
    ▼
Session stores complete chain
```

## Context Inheritance

Each agent in a chain receives its caller's yields as `input_data`. This creates a structured context inheritance where each agent builds on the previous agent's structured output:

```python
async def specialist(llm_response, input_data, context):
    # input_data = upstream agent's yields
    # context includes session_id, agent_name, etc.

    # Access upstream context
    category = input_data.get("category")   # From triage agent
    urgency = input_data.get("urgency")     # From triage agent

    return llm_response
```

## Session Context

The session stores all interactions across the chain automatically. Browse the full conversation history — agent attribution, roles, content for each message — in the **Studio Sessions tab**.

## Context Enrichment with Pre-Compose

Pre-compose processors add external context before the LLM sees any data:

```python
async def enrich_context(input_data, context):
    """Pull relevant data based on upstream yields"""
    category = input_data.get("category", "general")

    # Load category-specific knowledge from your external data source
    knowledge = await database.get_knowledge(category) or {}

    return {
        "domain_knowledge": knowledge,
        "category": category
    }

@pre_compose(context_processor=enrich_context)
async def specialist(llm_response, input_data, context):
    return llm_response
```

## Context Boundaries

LeafMesh enforces clear boundaries between different types of context:

| Context Type | Lifetime | Access |
|-------------|----------|--------|
| Session state | `session_ttl` (2h default) | Studio Sessions tab |
| Agent yields | `default_ttl` (1h default) | Auto-passed via `input_data` |
| Mesh communications | `default_ttl` | Managed automatically |
| Conversation history | `session_ttl` | Studio Sessions tab |
| Long-term data | Custom | Your application code (external database) |

## Next Steps

- **[Context Engineering](context-engineering)** — How prompts are assembled
- **[Session Management](../core-concepts/sessions)** — Session lifecycle
- **[State Management](../memory/state-management)** — Session state patterns

---

*LeafMesh — Structured context management across agents*
