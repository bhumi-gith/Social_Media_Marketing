"""Campaign Strategist Agent — defines creative direction for the campaign.

Takes campaign brief + PMS property data and determines:
- Theme, color palette, visual style, messaging tone
- Target audience and platform strategy
- Campaign briefs per priority floorplan

Also receives mid-cycle updates from competitor_monitor and analysis.
"""
import json
from leafmesh import LeafMeshLogger, pre_compose

logger = LeafMeshLogger(__name__)


@pre_compose()
async def campaign_strategist(llm_response, input_data, context):
    """Pre-compose: assemble context from upstream agents before LLM call."""
    logger.info("📋 Campaign Strategist — assembling strategy context...")

    upstream = input_data.get("upstream_yields", {})

    # --- Data from pms_data agent ---
    pms = upstream.get("pms_data", {})
    if pms:
        input_data.setdefault("vacancy_by_floorplan", pms.get("vacancy_by_floorplan", "{}"))
        input_data.setdefault("current_pricing", pms.get("current_pricing", "{}"))
        input_data.setdefault("active_concessions", pms.get("active_concessions", "{}"))
        input_data.setdefault("occupancy_rate", pms.get("occupancy_rate", 0.85))
        input_data.setdefault("priority_floorplans", pms.get("priority_floorplans", "[]"))
        input_data.setdefault("local_amenities", pms.get("local_amenities", "{}"))
        input_data.setdefault("property_photos", pms.get("property_photos", "[]"))
        input_data.setdefault("amenity_list", pms.get("amenity_list", "[]"))
        input_data.setdefault("matching_properties", pms.get("matching_properties", "{}"))
        logger.info("  ✓ PMS data loaded from upstream")

    # --- Data from competitor_monitor ---
    competitor = upstream.get("competitor_monitor", {})
    if competitor:
        input_data.setdefault(
            "competitor_report",
            competitor.get("competitor_report", "")
        )
        logger.info("  ✓ Competitor report loaded from upstream")

    # --- Data from analysis agent ---
    analysis = upstream.get("analysis", {})
    if analysis:
        input_data.setdefault(
            "analysis_recommendations",
            analysis.get("analysis_recommendations", "")
        )
        logger.info("  ✓ Analysis recommendations loaded from upstream")

    # Log what's being sent to LLM
    occ = input_data.get("occupancy_rate", 0)
    pf = input_data.get("priority_floorplans", "[]")
    prompt_text = input_data.get("campaign_prompt", "(no prompt)")
    logger.info(
        f"  Campaign: '{prompt_text[:60]}...' | "
        f"Occupancy: {float(occ):.1%} | "
        f"Priority floorplans: {pf}"
    )

    # The LLM (defined in YAML prompt) takes over here and returns structured JSON
    # pre_compose returns None to let the LLM run
    return None
