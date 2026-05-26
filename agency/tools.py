"""Custom tools that LLM agents can call during generation.

Two decorator types:
  @global_tool — Auto-registers in GlobalToolRegistry on import
  @tool        — Creates a local FunctionTool (register manually)

Tools are referenced in YAML agent config:
  tools: ["word_count", "timestamp"]       # specific tools by name
  tool_categories: ["text", "utility"]     # all tools in a category
  tool_choice: "auto"

Import these in main.py so @global_tool registration runs:
  from agency.tools import word_count, timestamp, format_as_markdown
"""
from leafmesh import global_tool, tool


@global_tool(
    name="word_count",
    description="Count the number of words in a text string",
    category="text",
)
def word_count(text: str) -> dict:
    """Count words in the given text."""
    words = text.split()
    return {"word_count": len(words), "character_count": len(text)}


@global_tool(
    name="timestamp",
    description="Get the current UTC timestamp",
    category="utility",
)
def timestamp() -> dict:
    """Return the current UTC time."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return {"utc": now.isoformat(), "unix": int(now.timestamp())}


@global_tool(
    name="math_eval",
    description="Evaluate a simple math expression (addition, subtraction, multiplication, division)",
    category="data",
)
def math_eval(expression: str) -> dict:
    """Safely evaluate a math expression."""
    allowed = set("0123456789+-*/.(). ")
    if not all(c in allowed for c in expression):
        return {"error": "Invalid characters in expression"}
    try:
        result = eval(expression, {"__builtins__": {}})  # noqa: S307
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": str(e)}


@global_tool(
    name="sensitive_data_lookup",
    description="Look up sensitive data records (restricted access)",
    category="data",
    allowed_agents=["researcher_agent", "advisor_agent"],
    requires_confirmation=True,
    timeout_seconds=15,
)
def sensitive_data_lookup(record_id: str) -> dict:
    """Look up a sensitive data record by ID.

    - allowed_agents: only researcher_agent and advisor_agent can call this
    - requires_confirmation: manager must approve before execution
    - timeout_seconds: auto-cancel if it takes longer than 15s
    """
    return {
        "record_id": record_id,
        "data": f"Record {record_id} contents",
        "classification": "internal",
    }


# ─── @tool example (local, not auto-registered) ──────────────
# Use @tool for agent-specific tools that don't need global access.

@tool(
    name="format_as_markdown",
    description="Format a list of items as a markdown checklist",
    timeout_seconds=10,
    requires_confirmation=False,
)
def format_as_markdown(items: list) -> str:
    """Convert a list to markdown checklist."""
    return "\n".join(f"- [ ] {item}" for item in items)


# ═══════════════════════════════════════════════════════════════
# BUILT-IN TOOLS REFERENCE
# These are provided by LeafMesh — no code needed, just reference
# them by name in your YAML config under `tools:` or by category
# under `tool_categories:`.
#
# Category: "web"
#   - web_search       — Search the web (requires API key config)
#   - web_scrape       — Scrape a URL and return content
#
# Category: "data"
#   - json_parse       — Parse and validate JSON strings
#   - csv_parse        — Parse CSV data into structured format
#
# Category: "text"
#   - text_summarize   — Summarize long text passages
#   - text_translate   — Translate text between languages
#
# Category: "utility"
#   - file_read        — Read file contents
#   - file_write       — Write content to a file
#   - http_request     — Make HTTP requests
#
# YAML usage:
#   tools: ["calculator", "web_search"]       # pick specific tools
#   tool_categories: ["data", "utility"]      # pick entire categories
#   tool_choice: "auto"                       # auto | none | required
#   allow_parallel_tool_calls: true           # LLM can call multiple tools at once
#   max_tool_calls_per_message: 10            # safety limit per LLM turn
# ═══════════════════════════════════════════════════════════════
