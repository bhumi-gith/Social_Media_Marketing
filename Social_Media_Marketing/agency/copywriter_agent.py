"""Copywriter Agent — writes platform-specific ad copy.

Fair Housing compliant. Iterates with visual_creator up to 7 rounds.
Revises copy based on visual alignment feedback each round.
"""
from leafmesh import LeafMeshLogger, pre_compose

logger = LeafMeshLogger(__name__)


@pre_compose()
async def copywriter(llm_response, input_data, context):
    """Pre-compose: assemble creative context before LLM generates copy."""
    logger.info("✍️  Copywriter — assembling copy context...")

    upstream = input_data.get("upstream_yields", {})

    # --- Campaign strategy from campaign_approval (via campaign_strategist upstream) ---
    strategist = upstream.get("campaign_strategist", {})
    if strategist:
        input_data.setdefault("campaign_briefs", strategist.get("campaign_briefs", "[]"))
        input_data.setdefault("campaign_theme", strategist.get("campaign_theme", ""))
        input_data.setdefault("color_palette", strategist.get("color_palette", "{}"))
        input_data.setdefault("messaging_tone", strategist.get("messaging_tone", ""))
        logger.info("  ✓ Campaign strategy loaded from upstream")

    # --- PMS pricing data ---
    pms = upstream.get("pms_data", {})
    if pms:
        input_data.setdefault("current_pricing", pms.get("current_pricing", "{}"))
        input_data.setdefault("active_concessions", pms.get("active_concessions", "{}"))

    # --- Visual feedback from visual_creator (if this is a revision round) ---
    visual = upstream.get("visual_creator", {})
    if visual:
        feedback = visual.get("visual_feedback", "")
        if feedback:
            input_data["visual_feedback"] = feedback
            revision_round = visual.get("revision_round", 0)
            logger.info(
                f"  ✓ Visual feedback received (round {revision_round}): "
                f"{feedback[:80]}..."
            )

    # --- HITL editor notes (from content_approval requesting copy revision) ---
    approval = upstream.get("content_approval", {})
    if approval:
        notes = approval.get("editor_notes", "")
        if notes:
            input_data["editor_notes"] = notes
            logger.info(f"  ✓ HITL editor notes: {notes[:80]}")

    logger.info("  LLM generating copy...")
    return None  # Let LLM run with prepared context
