"""Analysis Agent — analyses published campaign performance 2x per day.

Scheduled: 9 AM and 9 PM daily (wake_up: "0 9,21 * * *").
Reviews engagement, ad metrics, platform performance, and spend efficiency.
Sends actionable recommendations to campaign_strategist when changes are needed.
"""
from leafmesh import LeafMeshLogger, pre_compose

logger = LeafMeshLogger(__name__)


@pre_compose()
async def analysis(llm_response, input_data, context):
    """Pre-compose: load published campaign data for analysis."""
    logger.info("📊 Analysis Agent — loading campaign performance data...")

    upstream = input_data.get("upstream_yields", {})

    # --- Published campaign data from publisher ---
    publisher_data = upstream.get("publisher", {})
    if publisher_data:
        input_data.setdefault("published_campaigns", publisher_data.get("published_campaigns", "[]"))
        input_data.setdefault("platforms_active", publisher_data.get("platforms_active", ""))
        input_data.setdefault("variant_ids_live", publisher_data.get("variant_ids_live", "[]"))
        input_data.setdefault("daily_spend", publisher_data.get("daily_spend", 0))
        logger.info("  ✓ Publisher data loaded from upstream")

    # When wake_up fires (scheduled run), there's no upstream publisher data.
    # In production: fetch from analytics APIs via data_lookup tool.
    is_scheduled = not publisher_data and not upstream
    if is_scheduled:
        logger.info("  Scheduled analysis run — fetching metrics from analytics APIs")
        input_data.setdefault("published_campaigns", "all_active")
        input_data.setdefault("platforms_active", "instagram_organic,meta_ads,tiktok")
        input_data.setdefault("variant_ids_live", "all_active")

    logger.info("  LLM generating analysis report...")
    return None  # Let LLM run
