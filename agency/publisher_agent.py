import httpx
import uuid
from leafmesh import LeafMeshLogger

logger = LeafMeshLogger(__name__)

async def publisher(llm_response, input_data, context):
    logger.info("Running publisher agent...")
    
    approved_copy = input_data.get("approved_copy", "")
    approved_visuals = input_data.get("approved_visuals", "")
    current_pricing = input_data.get("current_pricing", "")
    
    # Safe conversion to float
    try:
        total_budget = float(input_data.get("total_budget_allocated", 0))
    except (ValueError, TypeError):
        total_budget = 0.0
    
    META_ACCESS_TOKEN = "your-meta-access-token"
    META_AD_ACCOUNT_ID = "act_your_account_id"
    
    published_campaigns = []
    variant_ids_live = []
    daily_spend = 0.0
    
    # Parse approved packages
    # In production this would be proper JSON parsing
    # For now treating as structured data from the approval agent
    
    try:
        async with httpx.AsyncClient() as client:
            
            # CREATE META AD CAMPAIGN
            campaign_response = await client.post(
                f"https://graph.facebook.com/v19.0/{META_AD_ACCOUNT_ID}/campaigns",
                params={"access_token": META_ACCESS_TOKEN},
                json={
                    "name": f"Leasing Campaign {context.get('session_id', '')}",
                    "objective": "LEAD_GENERATION",
                    "special_ad_categories": ["HOUSING"],
                    "status": "ACTIVE",
                    "daily_budget": int(total_budget * 100)
                },
                timeout=30.0
            )
            campaign_data = campaign_response.json()
            campaign_id = campaign_data.get("id", "")
            
            if campaign_id:
                # Generate unique variant ID for tracking
                variant_id = str(uuid.uuid4())[:8]
                variant_ids_live.append(variant_id)
                
                published_campaigns.append({
                    "platform": "meta",
                    "campaign_id": campaign_id,
                    "variant_id": variant_id,
                    "status": "active"
                })
                
    except Exception as e:
        logger.error(f"Meta Ad Campaign creation failed: {e}")
        published_campaigns.append({
            "platform": "meta",
            "status": "failed",
            "error": str(e)
        })
    
    # SETUP RETARGETING AUDIENCES
    retargeting_audiences = []
    
    try:
        async with httpx.AsyncClient() as client:
            # Floorplan page visitors audience
            audience_response = await client.post(
                f"https://graph.facebook.com/v19.0/{META_AD_ACCOUNT_ID}/customaudiences",
                params={"access_token": META_ACCESS_TOKEN},
                json={
                    "name": "Floorplan Page Visitors - 30 Days",
                    "subtype": "WEBSITE",
                    "retention_days": 30,
                    "rule": {
                        "inclusions": {
                            "operator": "or",
                            "rules": [{"event_sources": [{"id": "your_pixel_id", "type": "pixel"}]}]
                        }
                    }
                },
                timeout=30.0
            )
            audience_data = audience_response.json()
            retargeting_audiences.append({
                "name": "floorplan_visitors",
                "audience_id": audience_data.get("id", ""),
                "status": "created"
            })
    except Exception as e:
        logger.error(f"Meta Audience creation failed: {e}")
        retargeting_audiences.append({
            "name": "floorplan_visitors",
            "status": "failed",
            "error": str(e)
        })
    
    return {
        "published_campaigns": str(published_campaigns),
        "retargeting_audiences": str(retargeting_audiences),
        "leads_tagged": 0,
        "daily_spend": daily_spend,
        "platforms_active": "meta,instagram",
        "variant_ids_live": str(variant_ids_live),
        "meta_campaign_ids": str([c.get("campaign_id") for c in published_campaigns if c.get("platform") == "meta"]),
        "instagram_post_ids": "[]",
        "tiktok_video_ids": "[]"
    }
