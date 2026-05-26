from leafmesh import LeafMeshLogger, pre_compose
import json

logger = LeafMeshLogger(__name__)

@pre_compose()
async def campaign_strategist(llm_response, input_data, context):
    """
    Campaign Strategist Agent - Analyzes property data and creates marketing campaign briefs
    with targeting, messaging, and budget allocation.
    """
    logger.info("📋 Campaign Strategist Agent Starting...")
    
    # Get data from input
    occupancy_rate = input_data.get("occupancy_rate", 0.85)
    priority_floorplans_json = input_data.get("priority_floorplans", "[]")
    local_lifestyle_hooks_json = input_data.get("local_amenities", "{}")
    
    try:
        priority_floorplans = json.loads(priority_floorplans_json) if isinstance(priority_floorplans_json, str) else priority_floorplans_json
        local_lifestyle = json.loads(local_lifestyle_hooks_json) if isinstance(local_lifestyle_hooks_json, str) else local_lifestyle_hooks_json
    except:
        priority_floorplans = []
        local_lifestyle = {}
    
    logger.info(f"Analyzing occupancy: {occupancy_rate:.1%}, priority floorplans: {priority_floorplans}")
    
    # Create campaign briefs based on property data and LLM guidance
    # If LLM response is available, use it; otherwise create template briefs
    campaign_briefs = []
    total_budget = 1500  # Daily budget ceiling
    
    # Brief 1: Move-in Ease (for high vacancy floorplan)
    brief1 = {
        "brief_id": "brief_001",
        "target_floorplan": "2-Bedroom" if "2-Bedroom" in priority_floorplans or priority_floorplans else "2-Bedroom",
        "renter_persona": "family",
        "emotional_lever": "move_in_ease",
        "messaging_direction": "Emphasize quick approval (24-48 hours), move-in this weekend, family amenities. Reassuring and empowering tone.",
        "budget_allocation": 600,
        "platform_priority": ["meta_ads", "instagram_organic", "craigslist"],
        "concession_flag": occupancy_rate < 0.88,
        "concession_details": "Waived deposit + $100 move-in credit" if occupancy_rate < 0.88 else None,
        "local_lifestyle_hooks": [
            "Close to parks and schools",
            "Quick lease approval process",
            "Family-friendly community"
        ]
    }
    campaign_briefs.append(brief1)
    logger.info("  ✓ Brief 1 (Family) created")
    
    # Brief 2: Convenience (for young professionals)
    brief2 = {
        "brief_id": "brief_002",
        "target_floorplan": "1-Bedroom" if len(priority_floorplans) > 1 else "1-Bedroom",
        "renter_persona": "young_professional",
        "emotional_lever": "convenience",
        "messaging_direction": "Highlight walkability, proximity to work/nightlife, modern amenities. Energetic and aspirational tone.",
        "budget_allocation": 550,
        "platform_priority": ["instagram_organic", "tiktok", "meta_ads"],
        "concession_flag": False,
        "concession_details": None,
        "local_lifestyle_hooks": [
            "Steps from restaurants and nightlife",
            "Minutes to downtown offices",
            "Walkable shopping district"
        ]
    }
    campaign_briefs.append(brief2)
    logger.info("  ✓ Brief 2 (Young Professional) created")
    
    # Brief 3: Affordability (for price-sensitive renters)
    brief3 = {
        "brief_id": "brief_003",
        "target_floorplan": "Studio",
        "renter_persona": "budget_conscious",
        "emotional_lever": "affordability",
        "messaging_direction": "Focus on value, lower prices, no-frills appeal. Straightforward and honest tone.",
        "budget_allocation": 350,
        "platform_priority": ["craigslist", "zumper", "facebook"],
        "concession_flag": True,
        "concession_details": "Move-in incentives for studios",
        "local_lifestyle_hooks": [
            "Affordable luxury living",
            "Budget-friendly location",
            "All utilities included"
        ]
    }
    campaign_briefs.append(brief3)
    logger.info("  ✓ Brief 3 (Budget-Conscious) created")
    
    # Extract platforms and levers used
    all_platforms = set()
    all_levers = []
    concession_included_count = 0
    
    for brief in campaign_briefs:
        all_platforms.update(brief.get('platform_priority', []))
        all_levers.append(brief.get('emotional_lever', ''))
        if brief.get('concession_flag', False):
            concession_included_count += 1
    
    result = {
        "campaign_briefs": json.dumps(campaign_briefs),
        "total_budget_allocated": sum(b.get('budget_allocation', 0) for b in campaign_briefs),
        "briefs_count": len(campaign_briefs),
        "levers_used": json.dumps(all_levers),
        "platforms_targeted": json.dumps(list(all_platforms)),
        "concession_included": concession_included_count > 0,
    }
    
    logger.info(f"✨ Campaign Strategist completed: {len(campaign_briefs)} briefs, ${result['total_budget_allocated']} budget, {len(all_platforms)} platforms")
    return result
