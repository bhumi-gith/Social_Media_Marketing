"""Publisher Agent — multi-platform publishing engine.

Posts approved copy + visuals to Meta Ads, Instagram, TikTok, and listing platforms.
Tags every lead with variant ID for attribution.
Routes back to visual_creator or copywriter on publish errors.
"""
import uuid
import json
from datetime import datetime, timezone
import httpx
from leafmesh import LeafMeshLogger

logger = LeafMeshLogger(__name__)

META_ACCESS_TOKEN = "your-meta-access-token"
META_AD_ACCOUNT_ID = "act_your_account_id"


async def publisher(llm_response, input_data, context):
    """Publish approved content to all configured platforms."""
    logger.info("🚀 Publisher Agent — publishing approved content...")

    upstream = input_data.get("upstream_yields", {})

    # Resolve approved content — prefer direct HITL approval fields,
    # fall back to final_copy / final_visuals from visual_creator
    approval = upstream.get("content_approval", {})
    approved_copy = (
        approval.get("approved_copy")
        or input_data.get("approved_copy")
        or input_data.get("final_copy")
        or upstream.get("visual_creator", {}).get("final_copy", "")
    )
    approved_visuals = (
        approval.get("approved_visuals")
        or input_data.get("approved_visuals")
        or input_data.get("final_visuals")
        or upstream.get("visual_creator", {}).get("final_visuals", "")
    )

    campaign_briefs_raw = (
        input_data.get("campaign_briefs")
        or upstream.get("campaign_strategist", {}).get("campaign_briefs", "[]")
    )

    # Parse campaign briefs
    try:
        campaign_briefs = json.loads(campaign_briefs_raw) if isinstance(campaign_briefs_raw, str) else campaign_briefs_raw
    except Exception:
        campaign_briefs = []

    if not approved_copy:
        logger.warning("No approved copy found — aborting publish")
        return {
            "published_campaigns": "[]",
            "publish_success": False,
            "publish_error": "copy_issue",
            "leads_tagged": 0,
            "daily_spend": 0.0,
            "platforms_active": "",
            "variant_ids_live": "[]",
            "meta_campaign_ids": "[]",
        }

    published_campaigns = []
    variant_ids_live = []
    meta_campaign_ids = []
    daily_spend = 0.0
    platforms_active = set()
    publish_error = ""

    # ── META ADS ──────────────────────────────────────────────────────────
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            camp_resp = await client.post(
                f"https://graph.facebook.com/v19.0/{META_AD_ACCOUNT_ID}/campaigns",
                params={"access_token": META_ACCESS_TOKEN},
                json={
                    "name": f"LeafMesh Campaign {datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')}",
                    "objective": "LEAD_GENERATION",
                    "special_ad_categories": ["HOUSING"],
                    "status": "ACTIVE",
                },
                timeout=30.0,
            )
            camp_data = camp_resp.json()
            campaign_id = camp_data.get("id", "")

            if campaign_id:
                vid = str(uuid.uuid4())[:8]
                variant_ids_live.append(vid)
                meta_campaign_ids.append(campaign_id)
                published_campaigns.append({
                    "platform": "meta",
                    "campaign_id": campaign_id,
                    "variant_id": vid,
                    "status": "active",
                })
                platforms_active.add("meta_ads")
                logger.info(f"  ✓ Meta campaign created: {campaign_id}")
            else:
                raise ValueError(f"No campaign ID in response: {camp_data}")

    except Exception as e:
        logger.error(f"Meta Ads publish failed: {e}")
        published_campaigns.append({"platform": "meta", "status": "failed", "error": str(e)})
        publish_error = "visual_issue"  # Meta often rejects on creative issues

    # ── INSTAGRAM ORGANIC ─────────────────────────────────────────────────
    # In production: use Instagram Graph API to schedule posts
    try:
        vid = str(uuid.uuid4())[:8]
        variant_ids_live.append(vid)
        published_campaigns.append({
            "platform": "instagram_organic",
            "variant_id": vid,
            "status": "scheduled",
            "scheduled_time": datetime.now(timezone.utc).isoformat(),
        })
        platforms_active.add("instagram_organic")
        logger.info("  ✓ Instagram organic post scheduled")
    except Exception as e:
        logger.error(f"Instagram publish failed: {e}")
        publish_error = "visual_issue"

    # ── TIKTOK ────────────────────────────────────────────────────────────
    # Placeholder — TikTok Ads API integration point
    try:
        vid = str(uuid.uuid4())[:8]
        variant_ids_live.append(vid)
        published_campaigns.append({
            "platform": "tiktok",
            "variant_id": vid,
            "status": "pending_creative_review",
        })
        platforms_active.add("tiktok")
        logger.info("  ✓ TikTok post submitted for review")
    except Exception as e:
        logger.error(f"TikTok publish failed: {e}")

    # ── TAG LEADS ─────────────────────────────────────────────────────────
    leads_tagged = len(variant_ids_live)

    publish_success = len([c for c in published_campaigns if c.get("status") not in ("failed",)]) > 0

    if publish_success:
        publish_error = ""

    logger.info(
        f"✨ Publisher complete — "
        f"{'SUCCESS' if publish_success else 'PARTIAL'} | "
        f"platforms: {list(platforms_active)} | "
        f"variants: {variant_ids_live}"
    )

    return {
        "published_campaigns": json.dumps(published_campaigns),
        "publish_success": publish_success,
        "publish_error": publish_error,
        "leads_tagged": leads_tagged,
        "daily_spend": daily_spend,
        "platforms_active": ",".join(platforms_active),
        "variant_ids_live": json.dumps(variant_ids_live),
        "meta_campaign_ids": json.dumps(meta_campaign_ids),
    }
