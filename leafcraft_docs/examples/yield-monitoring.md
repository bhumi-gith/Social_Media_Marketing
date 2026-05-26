# Multi-Agent Math Pipeline

A complete LeafMesh example that chains three agents together: a **solver** that computes answers, a **checker** that verifies correctness, and a **reporter** that summarizes results. This demonstrates YAML-driven routing, intelligence functions, and mesh communication.

## System Overview

```
User sends "2 + 1"
    │
    ▼
┌──────────┐   condition: answer > 0   ┌──────────┐   condition: is_correct == true   ┌──────────┐
│  Solver   │─────────────────────────▶│  Checker  │──────────────────────────────────▶│ Reporter │
│ (gpt-4o-  │                          │ (gpt-4o-  │                                   │ (gpt-4o- │
│  mini)    │                          │  mini)    │                                   │  mini)   │
│           │                          │           │                                   │          │
│ yields:   │                          │ yields:   │                                   │ yields:  │
│  answer   │                          │ is_correct│                                   │ summary  │
│  steps    │                          │ expected  │                                   │ grade    │
└──────────┘                           └──────────┘                                   └──────────┘
```

Three agents, zero direct calls between them. The routing is entirely declarative — defined in YAML `can_call` rules with conditions evaluated safely at runtime.

## Full YAML Configuration

Create `math_pipeline.yaml`:

```yaml
name: "math_pipeline"
version: "1.0.0"
architecture: "managed_mesh"

# Redis for state and mesh communication
redis:
  host: "localhost"
  port: 6379
  db: 0
  session_ttl: 3600  # 1 hour

# Manager provides automatic coordination
manager:
  enabled: true
  model: "gpt-4o-mini"
  coordination_rules:
    max_response_time: 30
    max_retry_attempts: 2

# Mesh communication settings
mesh:
  call_timeout: 60
  max_retries: 2
  retry_backoff: 2

# Observability: auto-enabled by LEAFMESH_LICENSE_KEY (no YAML config needed)

agents:
  # Agent 1: Solves math problems
  solver:
    name: "solver"
    model: "gpt-4o-mini"
    temperature: 0.1      # Low temperature for precise math
    max_tokens: 500
    prompt: |
      You are a math solver. Given a math problem, solve it step by step.
      Be precise and show your work clearly.
    yields:
      problem: "string"
      answer: "number"
      steps: "array"
      confidence: "number"
    can_call:
      - agent: "checker"
        condition: "answer >= 0"
        call_immediately: true

  # Agent 2: Verifies the solver's work
  checker:
    name: "checker"
    model: "gpt-4o-mini"
    temperature: 0.0      # Zero temperature for deterministic checking
    max_tokens: 300
    prompt: |
      You verify math solutions. Given a problem and a proposed answer,
      check if the answer is correct. Recompute independently and compare.
    yields:
      is_correct: "boolean"
      expected_answer: "number"
      explanation: "string"
    can_call:
      - agent: "reporter"
        condition: "is_correct == true"

  # Agent 3: Summarizes the pipeline result
  reporter:
    name: "reporter"
    model: "gpt-4o-mini"
    temperature: 0.3
    max_tokens: 200
    prompt: |
      You write brief, clear summaries of math problem results.
      Include the problem, answer, and whether it was verified correct.
    yields:
      summary: "string"
      grade: "string"
```

**What this config declares:**

- Three agents, each with their own model, temperature, and prompt
- **Yields**: Structured output schemas that are validated at runtime
- **can_call**: Conditional routing — the solver calls the checker when `answer >= 0`, the checker calls the reporter when `is_correct == true`
- **Manager**: Built-in coordination with a 30-second response time limit
- **Mesh**: 60-second timeout with 2 retries and exponential backoff

## Python Implementation

Create `math_pipeline.py`:

```python
import asyncio
from leafmesh import LeafMesh

leafmesh = LeafMesh.from_yaml("math_pipeline.yaml")


# --- Agent 1: Solver Intelligence ---
# Function name "solver" matches the YAML agent name — auto_discover finds it

async def solver(llm_response, input_data, context):
    """Deterministic math solving with LLM fallback"""
    problem = input_data.get("problem", "")
    import re
    numbers = re.findall(r'-?\d+\.?\d*', problem)

    if len(numbers) == 2:
        a, b = float(numbers[0]), float(numbers[1])

        if "+" in problem:
            answer = a + b
            steps = [f"Identify operands: {a} and {b}", f"Add: {a} + {b} = {answer}"]
        elif "-" in problem:
            answer = a - b
            steps = [f"Identify operands: {a} and {b}", f"Subtract: {a} - {b} = {answer}"]
        elif "*" in problem or "x" in problem.lower():
            answer = a * b
            steps = [f"Identify operands: {a} and {b}", f"Multiply: {a} * {b} = {answer}"]
        elif "/" in problem:
            if b == 0:
                return {"problem": problem, "answer": 0, "steps": ["Division by zero"], "confidence": 0.0}
            answer = a / b
            steps = [f"Identify operands: {a} and {b}", f"Divide: {a} / {b} = {answer}"]
        else:
            # Fall back to LLM for unrecognized operators
            return llm_response

        # Return integer if result is whole number
        if answer == int(answer):
            answer = int(answer)

        return {
            "problem": problem,
            "answer": answer,
            "steps": steps,
            "confidence": 1.0    # Deterministic = full confidence
        }

    # Fall back to LLM for complex expressions
    return llm_response


# --- Agent 2: Checker Intelligence ---
# Function name "checker" matches the YAML agent name — auto_discover finds it

async def checker(llm_response, input_data, context):
    """Independent verification of the solver's answer"""
    problem = input_data.get("problem", "")
    claimed_answer = input_data.get("answer", None)

    if claimed_answer is None:
        return {
            "is_correct": False,
            "expected_answer": 0,
            "explanation": "No answer provided to verify"
        }

    import re
    numbers = re.findall(r'-?\d+\.?\d*', problem)

    if len(numbers) == 2:
        a, b = float(numbers[0]), float(numbers[1])

        if "+" in problem:
            expected = a + b
        elif "-" in problem:
            expected = a - b
        elif "*" in problem or "x" in problem.lower():
            expected = a * b
        elif "/" in problem and b != 0:
            expected = a / b
        else:
            return llm_response

        if expected == int(expected):
            expected = int(expected)

        is_correct = abs(float(claimed_answer) - float(expected)) < 0.001

        return {
            "is_correct": is_correct,
            "expected_answer": expected,
            "explanation": f"Recomputed {problem} = {expected}. "
                          f"Claimed answer: {claimed_answer}. "
                          f"{'Correct!' if is_correct else 'INCORRECT.'}"
        }

    return llm_response


# --- Agent 3: Reporter Intelligence ---
# Function name "reporter" matches the YAML agent name — auto_discover finds it

async def reporter(llm_response, input_data, context):
    """Generate a clean summary of the pipeline result"""
    is_correct = input_data.get("is_correct", False)
    expected = input_data.get("expected_answer", "unknown")
    explanation = input_data.get("explanation", "")

    grade = "A" if is_correct else "F"
    summary = f"Result: {expected} | Verified: {'Yes' if is_correct else 'No'} | {explanation}"

    return {
        "summary": summary,
        "grade": grade
    }


# --- Main Entry Point ---

async def main():
    print("=== LeafMesh Math Pipeline ===\n")

    await leafmesh.start()
    print("Pipeline started: solver -> checker -> reporter\n")

    # Test 1: Simple addition
    print("Problem: 2 + 1")
    result = await leafmesh.mesh_call(
        "solver",
        input_data={"problem": "2 + 1"},
        session_id="pipeline_demo"
    )
    print(f"Solver: {result}\n")

    # Test 2: Multiplication
    print("Problem: 7 * 6")
    result2 = await leafmesh.mesh_call(
        "solver",
        input_data={"problem": "7 * 6"},
        session_id="pipeline_demo"
    )
    print(f"Solver: {result2}\n")

    # Test 3: Division
    print("Problem: 100 / 4")
    result3 = await leafmesh.mesh_call(
        "solver",
        input_data={"problem": "100 / 4"},
        session_id="pipeline_demo"
    )
    print(f"Solver: {result3}\n")

    # Test 4: Subtraction
    print("Problem: 50 - 17")
    result4 = await leafmesh.mesh_call(
        "solver",
        input_data={"problem": "50 - 17"},
        session_id="pipeline_demo"
    )
    print(f"Solver: {result4}\n")

    await leafmesh.stop()
    print("=== Pipeline complete ===")


if __name__ == "__main__":
    asyncio.run(main())
```

## How the Pipeline Executes

When you send `"2 + 1"` to the solver, here is what happens at each stage:

### Stage 1: Solver
1. The LLM receives the solver's prompt and yields schema (but our intelligence function intercepts)
2. `solver()` parses `"2 + 1"`, computes `3` deterministically
3. Returns `{"problem": "2 + 1", "answer": 3, "steps": [...], "confidence": 1.0}`
4. Yields are validated: `answer` is a number, `steps` is an array
5. `can_call` condition `answer >= 0` evaluates to `True`
6. The mesh dispatches a call to `checker`

### Stage 2: Checker
1. Receives the solver's output as `input_data`
2. `checker()` independently recomputes: `2 + 1 = 3`
3. Compares against claimed answer `3` — they match
4. Returns `{"is_correct": true, "expected_answer": 3, "explanation": "..."}`
5. `can_call` condition `is_correct == true` evaluates to `True`
6. The mesh dispatches a call to `reporter`

### Stage 3: Reporter
1. Receives the checker's output as `input_data`
2. `reporter()` generates summary: grade A, verified correct
3. Returns `{"summary": "Result: 3 | Verified: Yes | ...", "grade": "A"}`
4. No `can_call` rules — pipeline terminates

Total LLM calls: zero — all three intelligence functions handled everything deterministically.

## Expected Output

```
=== LeafMesh Math Pipeline ===

Pipeline started: solver -> checker -> reporter

Problem: 2 + 1
Solver: {'problem': '2 + 1', 'answer': 3, 'steps': ['Identify operands: 2.0 and 1.0', 'Add: 2.0 + 1.0 = 3'], 'confidence': 1.0}

Problem: 7 * 6
Solver: {'problem': '7 * 6', 'answer': 42, 'steps': ['Identify operands: 7.0 and 6.0', 'Multiply: 7.0 * 6.0 = 42'], 'confidence': 1.0}

Problem: 100 / 4
Solver: {'problem': '100 / 4', 'answer': 25, 'steps': ['Identify operands: 100.0 and 4.0', 'Divide: 100.0 / 4.0 = 25'], 'confidence': 1.0}

Problem: 50 - 17
Solver: {'problem': '50 - 17', 'answer': 33, 'steps': ['Identify operands: 50.0 and 17.0', 'Subtract: 50.0 - 17.0 = 33'], 'confidence': 1.0}

=== Pipeline complete ===
```

## Adding Mesh Calls Directly

Beyond `can_call` routing, you can make direct mesh calls from intelligence functions:

```python
async def solver(llm_response, input_data, context):
    """Solver that directly calls checker via mesh"""
    answer = compute_answer(input_data)

    # Direct mesh call to checker
    check_result = await leafmesh.mesh_call(
        from_agent="solver",
        to_agent="checker",
        data={"problem": input_data["problem"], "answer": answer},
        session_id=context.get("session_id", "default")
    )

    return {
        "answer": answer,
        "verified": check_result.get("is_correct", False)
    }
```

## Production Configuration

### Enable Self-Healing
```yaml
self_healing:
  enabled: true
```

If the checker agent fails, self-healing detects the failure and recovers automatically. See [Self-Healing Guide](../advanced/self-healing) for tunable options.

### Enable Evolution

Evolution runs as a co-located service alongside the runtime mesh — no YAML block needed. Operators kick off a run from Studio with their test scenarios (e.g. a few representative problems with expected answers) to verify the configuration still produces the expected outputs.

See [Evolution](../advanced/evolutionary-optimization) for the full workflow.

### Agent File Organization

For larger systems, organize agents into separate files. The `auto_discover` setting in your YAML config finds intelligence functions by matching function names to agent names:

```python
# agency/solver_agent.py

async def solver(llm_response, input_data, context):
    """Function name "solver" matches the YAML agent name — auto_discover finds it"""
    # ... solver implementation
    return result
```

```python
# agency/checker_agent.py

async def checker(llm_response, input_data, context):
    """Function name "checker" matches the YAML agent name — auto_discover finds it"""
    # ... checker implementation
    return result
```

```python
# main.py
import asyncio
from leafmesh import LeafMesh

# auto_discover in YAML config automatically finds intelligence functions
# that match agent names across your project modules
leafmesh = LeafMesh.from_yaml("math_pipeline.yaml")

async def main():
    await leafmesh.start()
    print("Math pipeline ready for requests")

    # Keep running for API traffic
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Patterns Demonstrated

| Pattern | Where It Appears |
|---------|-----------------|
| YAML-driven agent definition | `math_pipeline.yaml` — no Python needed for routing |
| Conditional routing | `can_call` with conditions like `answer >= 0` |
| Intelligence functions | Function name matches YAML agent name — auto_discover wires them |
| Multi-agent chaining | solver → checker → reporter |
| Structured yields | Type-safe schemas validated at each step |
| Independent verification | Checker recomputes independently |
| Safe condition evaluation | `can_call` conditions are parsed safely — no arbitrary code execution |
| Agent file organization | Separate files per agent, auto_discover matches by function name |

## Next Steps

- **[Architecture Guide](../core-concepts/architecture)** — How LeafMesh orchestrates agents
- **[Customer Service Bot](customer-service-bot)** — Multi-tier support example
- **[Data Pipeline](data-pipeline)** — ETL with validation and transformation
- **[Self-Healing Guide](../advanced/self-healing)** — Production resilience

---

*LeafMesh — Three agents, one YAML file, zero boilerplate*
