# LeafMesh Overview

> Build production-ready multi-agent AI systems with configuration-first orchestration, self-healing networks, and adaptive LLM execution.

**Commercial Software by LeafCraft** — Requires commercial licensing for business use. 30-day evaluation period available.

## What is LeafMesh?

LeafMesh is a Python framework for building multi-agent AI systems. You define agents in YAML — their prompts, output schemas, routing rules, and tools — and the framework handles orchestration, state management, observability, and failure recovery.

The core idea: **YAML is the primary interface, Python is optional enhancement.**

```python
from leafmesh import LeafMesh

# Load your swarm from a YAML config
leafmesh = LeafMesh.from_yaml("math_swarm.yaml")

# Optionally add business logic (function name = agent name)
async def calculator(llm_response, input_data, context):
    problem = input_data.get("problem", "")
    # Add deterministic validation on top of LLM output
    if "+" in problem:
        nums = [int(n) for n in problem.split("+")]
        return {"answer": sum(nums), "verified": True}
    return llm_response

# Start and process requests
await leafmesh.start()
result = await leafmesh.mesh_call(
    "calculator",
    input_data={"problem": "2 + 1"},
    session_id="demo"
)
# result: {"answer": 3, "verified": True}
```

## How It Works

LeafMesh is a **control plane for multi-agent systems**. Agents are the data plane — they call LLMs, run tools, and produce outputs. LeafMesh is the control plane — it routes requests between agents, enforces policies defined in YAML, observes every event, and intervenes when problems are detected.

Agents never call each other directly. Every inter-agent communication flows through the control plane, where it is validated, logged, and subject to policy enforcement.

### A Simple Example: Math Tutor Swarm

Imagine a system where one agent solves math problems and another agent checks the work:

```yaml
name: "math_tutor_swarm"
version: "1.0.0"
architecture: "managed_mesh"

redis:
  host: "localhost"
  port: 6379

manager:
  enabled: true
  model: "gpt-4o-mini"

agents:
  solver:
    name: "solver"
    model: "gpt-4o-mini"
    prompt: |
      You solve math problems step by step.
      Always show your work clearly.
    yields:
      problem: "string"
      answer: "number"
      steps: "array"
    can_call:
      - agent: "checker"
        condition: "answer > 0"

  checker:
    name: "checker"
    model: "gpt-4o-mini"
    prompt: |
      You verify math solutions. Check if the answer
      is correct and explain any errors you find.
    yields:
      is_correct: "boolean"
      explanation: "string"
```

**What happens when you send "2 + 1":**

1. The `solver` agent receives the problem and produces `{"answer": 3, "steps": ["2 + 1 = 3"]}`
2. The yields are validated against the declared schema (answer must be a number)
3. The `can_call` condition `answer > 0` evaluates to `True`
4. The `checker` agent receives the solver's output and verifies it
5. The platform observes each event and detects anomalies automatically
6. Built-in coordination intervenes only when an issue is flagged

Two agents, zero Python required. The routing, validation, and coordination are all declarative.

## Core Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     LeafMesh Control Plane                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   YAML Config ──▶ Agent Routing ──▶ Mesh Communication           │
│                                                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│   │ Observation  │  │ Coordination │  │ Condition Evaluator   │  │
│   │ & anomaly    │  │ & automatic  │  │ (AST-safe routing)    │  │
│   │ detection    │  │ intervention │  │ No eval(), no inject  │  │
│   └──────────────┘  └──────────────┘  └───────────────────────┘  │
│                                                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐  │
│   │ Self-Healing │  │ Evolution    │  │ Adaptive LLM          │  │
│   │ Network      │  │ (health      │  │ Execution             │  │
│   │ Auto         │  │  check)      │  │ Multi-provider        │  │
│   │ recovery     │  │              │  │ Smart model selection │  │
│   └──────────────┘  └──────────────┘  └───────────────────────┘  │
│                                                                  │
│   ┌──────────────────────────────────────────────────────────┐   │
│   │  Durable state: sessions, yields, mesh history, decisions│   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Managed observability pipeline ──── separate boundary          │
└──────────────────────────────────────────────────────────────────┘
```

### Key Components

**Configuration as Code** — Agents, routing rules, coordination parameters, and scheduling are all defined in YAML. Diffable in pull requests, auditable by security teams.

**Multi-Layer Validation Pipeline** — Every agent response passes through a multi-layer validation pipeline before it can trigger downstream actions. Many layers are fully deterministic:

| Layer | What It Catches | Example |
|-------|----------------|---------|
| Yield parsing | Schema violations | Agent returns `answer: "three"` instead of `answer: 3` |
| Condition evaluation | Invalid routing | Solver answer doesn't meet checker threshold |
| Intelligence function | Business logic errors | Missing required validation step |
| Anomaly review | Workflow anomalies | Agent claims success but output suggests failure |
| Coordination rules | Coordination problems | Chain timeout, repeated failures |
| Downstream validation | Input contract violations | Upstream output incompatible with downstream |

**Multi-Provider LLM Support** — OpenAI, Anthropic, Google, DeepSeek, and local models supported out of the box. No vendor lock-in.

**Event-Driven Communication** — Components communicate over an internal event backbone. Loose coupling, replay capability, and natural observability boundaries.

## Production Features

### Self-Healing Networks
```yaml
self_healing:
  enabled: true
  detection_interval: 30
  max_recovery_attempts: 3
```
Automatic failure detection and recovery — restart, reroute, isolate, or roll back — without human intervention.

### Evolution (Health Check)
Re-runs your test scenarios against your current configuration on a schedule and produces per-agent scores so you can catch quality drift over time. Each agent receives a 0–100 score combining structural and value compliance.

Runs as a co-located service alongside the runtime mesh — operators kick off runs from Studio with their test scenarios; the runtime mesh keeps serving customer traffic in isolation. See [Evolution](advanced/evolutionary-optimization).

### Adaptive Model Selection
```yaml
adaptive_llm:
  enabled: true
  cost_optimization: true
  fallback_models: ["gpt-4o-mini", "gpt-3.5-turbo"]
```
Routes each request to an appropriate model with automatic fallback chains.

### Enterprise Observability

Distributed tracing, performance metrics, real-time dashboard, and structured logging — all built in. Auto-enabled by your license key.

## Key Differentiators

### 1. Mesh Architecture, Not Linear Chains
Agents communicate in mesh patterns — any agent can call any other agent, subject to `can_call` rules. Not just A → B → C.

```python
# Direct mesh call between any two agents
await leafmesh.mesh_call(
    from_agent="solver",
    to_agent="checker",
    data={"problem": "2 + 1", "answer": 3}
)
```

### 2. Intelligence Enhancement
Add deterministic Python logic on top of LLM responses — no framework-specific DSLs, no class hierarchies:

```python
async def checker(llm_response, input_data, context):
    """Deterministic verification layer"""
    problem = input_data.get("problem", "")
    claimed_answer = input_data.get("answer", 0)

    # Simple programmatic check
    if "+" in problem:
        parts = problem.split("+")
        expected = int(parts[0].strip()) + int(parts[1].strip())
        return {
            "is_correct": claimed_answer == expected,
            "explanation": f"{problem} = {expected}"
        }
    return llm_response
```

### 3. AST-Safe Condition Evaluation
Routing conditions in YAML are evaluated using Python's `ast` module — never `eval()`. Only whitelisted node types (comparisons, boolean logic, arithmetic) are allowed. Code injection through YAML configuration is prevented at the parser level.

```yaml
can_call:
  - agent: "checker"
    condition: "answer > 0"          # Simple comparison
  - agent: "escalator"
    condition: "confidence < 0.5 && answer > 100"  # Compound
```

### 4. Built-in Oversight
LeafMesh provides a closed-loop control system:
- **Observation**: Every event is observed and classified for anomalies
- **Coordination**: Automatic coordination decisions handle retry, escalation, and halt behavior using deterministic logic

## Getting Started

### 1. Install
```bash
pip install leafmesh
```

### 2. Configure
```yaml
name: "my_swarm"
architecture: "managed_mesh"

redis:
  host: "localhost"
  port: 6379

agents:
  calculator:
    name: "calculator"
    model: "gpt-4o-mini"
    prompt: "You solve math problems step by step."
    yields:
      answer: "number"
      steps: "array"
```

### 3. Run
```python
from leafmesh import LeafMesh

leafmesh = LeafMesh.from_yaml("config.yaml")
await leafmesh.start()

result = await leafmesh.mesh_call(
    "calculator",
    input_data={"problem": "2 + 1"},
    session_id="demo"
)
```

## Commercial Licensing

LeafMesh is commercial software owned by LeafCraft.

**Licensing Options:**
- **Evaluation**: 30 days for development and testing
- **Commercial**: Required for revenue-generating use
- **Enterprise**: Advanced features, priority support, and SLAs

**Contact:**
- Email: `info@leafcraft.ai`
- Website: `https://leafcraft.ai`

## Next Steps

- **[Quick Start](getting-started/quickstart)** — Build your first swarm in 5 minutes
- **[Installation Guide](getting-started/installation)** — Setup and requirements
- **[Architecture Deep Dive](core-concepts/architecture)** — Control plane internals
- **[API Reference](core-concepts/leafmesh-adk)** — LeafMesh class documentation
- **[Multi-Agent Example](examples/yield-monitoring)** — Calculator → Validator pipeline

---

*LeafMesh — Configuration-first multi-agent orchestration for production systems*
