"""Competitor Monitor Agent — monitors the leasing market 3x per day.

Scheduled: 8 AM, 1 PM, 7 PM daily (wake_up: "0 8,13,19 * * *").
Researches similar properties, active leasings, competitor pricing,
concessions, ad activity, and review sentiment.
Feeds strategic intel to campaign_strategist.
"""
from leafmesh import LeafMeshLogger, pre_compose

logger = LeafMeshLogger(__name__)

# List of competitor properties to monitor (configure per deployment)
COMPETITOR_PROPERTIES = [
    "The Riverview Apartments, Denver CO",
    "Park Place Residences, Denver CO",
    "Downtown Lofts, Denver CO",
]


@pre_compose()
async def competitor_monitor(llm_response, input_data, context):
    """Pre-compose: load competitor list and current pricing context."""
    logger.info("🔍 Competitor Monitor — scanning leasing market...")

    upstream = input_data.get("upstream_yields", {})

    # Provide competitor list to LLM
    if not input_data.get("competitor_properties"):
        input_data["competitor_properties"] = str(COMPETITOR_PROPERTIES)
        logger.info(f"  Monitoring {len(COMPETITOR_PROPERTIES)} competitor properties")

    # Provide our current pricing for comparison
    pms = upstream.get("pms_data", {})
    if pms:
        input_data.setdefault("our_current_pricing", pms.get("current_pricing", "{}"))
    else:
        # Fallback: use cached pricing from previous session if available
        input_data.setdefault("our_current_pricing", "{}")

    logger.info("  LLM scanning competitor landscape...")
    return None  # Let LLM run with web_search + web_request tools
