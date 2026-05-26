"""Custom tools that LLM agents can call during generation.

Tools registered here:
  - db_lookup     : query mock_database — property briefs, photos, amenities
  - data_lookup   : PMS / CRM / analytics data lookup
  - word_count    : count words in text
  - timestamp     : current UTC time
  - math_eval     : safe math expression evaluator

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
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from leafmesh import global_tool, tool
import json
from mock_database import (
    MOCK_DATABASE,
    get_campaign_brief,
    get_property_photos,
    get_local_amenities,
    get_amenity_listing,
    get_all_properties,
    prepare_visual_creator_input,
)


# ─── db_lookup — mock_database (properties, briefs, photos, amenities) ────────

@global_tool(
    name="db_lookup",
    description=(
        "Query the property database. Use this to get property-specific data needed "
        "for campaign creation. "
        "Accepted 'query' values:\n"
        "  - 'all_properties'              : list all property IDs and names\n"
        "  - 'property:<id>'               : full data for one property\n"
        "  - 'briefs:<id>'                 : campaign briefs for a property\n"
        "  - 'photos:<id>'                 : property photos with URLs\n"
        "  - 'local_amenities:<id>'        : local amenities near the property\n"
        "  - 'property_amenities:<id>'     : on-site amenities for the property\n"
        "  - 'full:<id>'                   : everything for a property (briefs + photos + amenities)\n"
        "Property IDs: riverside_luxury, downtown_modern, suburban_family"
    ),
    category="data",
)
def db_lookup(query: str) -> dict:
    """Query mock_database for property campaign data."""
    q = query.strip().lower()

    # List all properties
    if q == "all_properties":
        return {
            "properties": [
                {"id": p["id"], "name": p["name"], "address": p["address"]}
                for p in MOCK_DATABASE["properties"]
            ]
        }

    # Parse "action:property_id" format
    if ":" in q:
        action, prop_id = q.split(":", 1)
        prop_id = prop_id.strip()
        action = action.strip()
    else:
        # Fallback: treat whole query as property id lookup
        action = "full"
        prop_id = q

    if action == "property":
        for p in MOCK_DATABASE["properties"]:
            if p["id"] == prop_id:
                return {
                    "id": p["id"],
                    "name": p["name"],
                    "address": p["address"],
                    "brief_count": len(p.get("campaign_briefs", [])),
                    "photo_count": len(p.get("property_photos", [])),
                }
        return {"error": f"Property '{prop_id}' not found"}

    if action == "briefs":
        result = []
        for p in MOCK_DATABASE["properties"]:
            if p["id"] == prop_id:
                result = p.get("campaign_briefs", [])
                break
        return {"property_id": prop_id, "campaign_briefs": result} if result else {"error": f"No briefs for '{prop_id}'"}

    if action == "photos":
        photos = get_property_photos(prop_id)
        return {"property_id": prop_id, "photos": photos} if photos else {"error": f"No photos for '{prop_id}'"}

    if action == "local_amenities":
        amenities = get_local_amenities(prop_id)
        return {"property_id": prop_id, "local_amenities": amenities}

    if action == "property_amenities":
        amenities = get_amenity_listing(prop_id)
        return {"property_id": prop_id, "property_amenities": amenities}

    if action == "full":
        data = prepare_visual_creator_input(prop_id)
        return data if data else {"error": f"Property '{prop_id}' not found"}

    return {"error": f"Unknown query: '{query}'. See tool description for accepted formats."}


# ─── data_lookup — PMS / CRM / Analytics mock data ───────────────────────────

@global_tool(
    name="data_lookup",
    description=(
        "Look up property data, campaign metrics, or CRM records. "
        "Pass a 'query' string describing what you need "
        "(e.g. 'vacancy rates', 'ad performance last 7 days', 'tour bookings by variant')."
    ),
    category="data",
)
def data_lookup(query: str) -> dict:
    """Return mock PMS / CRM / analytics data based on the query."""
    q = query.lower()

    if any(kw in q for kw in ("vacanc", "occupanc", "floorplan", "pricing", "unit")):
        return {
            "source": "PMS",
            "vacancy_by_floorplan": {
                "studio": {"vacant": 5, "total": 40, "price": 1200, "vacancy_pct": 0.125},
                "one_bedroom": {"vacant": 8, "total": 80, "price": 1650, "vacancy_pct": 0.10},
                "two_bedroom": {"vacant": 12, "total": 100, "price": 2100, "vacancy_pct": 0.12},
                "three_bedroom": {"vacant": 3, "total": 30, "price": 2800, "vacancy_pct": 0.10},
            },
            "overall_occupancy": 0.879,
            "active_concessions": {
                "two_bedroom": [{"type": "waived_deposit", "value": 500}],
                "studio": [{"type": "move_in_credit", "value": 100}],
            },
        }

    if any(kw in q for kw in ("performance", "metric", "ctr", "cpl", "spend", "impression", "click")):
        return {
            "source": "analytics",
            "period": "last_7_days",
            "meta_ads": {
                "impressions": 45200, "clicks": 1356, "ctr": 0.030,
                "leads": 87, "cpl": 23.45, "spend": 2040.15,
            },
            "instagram_organic": {
                "reach": 8900, "impressions": 12300, "saves": 234,
                "profile_visits": 456, "link_clicks": 89,
            },
            "tiktok": {
                "views": 22400, "completion_rate": 0.42, "shares": 67,
                "profile_visits": 312, "link_clicks": 44,
            },
            "crm_funnel": {
                "leads": 87, "tours_booked": 23, "applications": 8, "leases_signed": 3,
                "cost_per_tour": 88.70, "cost_per_lease": 680.05,
            },
        }

    if any(kw in q for kw in ("tour", "booking", "applicat", "lease", "crm")):
        return {
            "source": "CRM",
            "tours_booked_7d": 23,
            "applications_7d": 8,
            "leases_signed_7d": 3,
            "top_source": "meta_ads",
            "cost_per_tour": 88.70,
            "cost_per_lease": 680.05,
        }

    if any(kw in q for kw in ("amenity", "amenities", "feature", "property")):
        return {
            "source": "PMS",
            "amenities": [
                "Swimming pool", "Fitness center", "Dog park", "Community room",
                "Rooftop lounge", "Concierge", "24-hour security", "Reserved parking",
                "Package room", "Bike storage",
            ],
            "address": "1450 Riverside Drive, Denver, CO 80210",
            "nearby": ["Coffee shop 0.2mi", "Grocery 0.4mi", "Park 0.3mi", "Light rail 0.6mi"],
        }

    return {"source": "data_lookup", "query": query, "result": "no matching data found"}


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
