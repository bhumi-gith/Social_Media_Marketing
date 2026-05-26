"""Visual Creator Agent — creates visual design specs and poster layouts.

Manages the creative iteration loop with copywriter (up to 7 rounds).
Evaluates copy-visual alignment and provides feedback each round.
Finalises the complete creative package when alignment >= 8 or max rounds hit.
"""
import json
from leafmesh import LeafMeshLogger, pre_compose

logger = LeafMeshLogger(__name__)


@pre_compose()
async def visual_creator(llm_response, input_data, context):
    """Pre-compose: assemble visual context and track iteration round."""
    logger.info("🎨 Visual Creator — assembling visual context...")

    upstream = input_data.get("upstream_yields", {})

    # --- Campaign strategy (colors, theme, style) ---
    strategist = upstream.get("campaign_strategist", {})
    if strategist:
        input_data.setdefault("campaign_theme", strategist.get("campaign_theme", ""))
        input_data.setdefault("color_palette", strategist.get("color_palette", "{}"))
        input_data.setdefault("visual_style", strategist.get("visual_style", ""))
        input_data.setdefault("campaign_briefs", strategist.get("campaign_briefs", "[]"))
        input_data.setdefault("property_photos", strategist.get("property_photos", "[]"))

    # --- PMS photos (if not from strategist) ---
    pms = upstream.get("pms_data", {})
    if pms:
        input_data.setdefault("property_photos", pms.get("property_photos", "[]"))

    # --- Copy from copywriter ---
    copy_data = upstream.get("copywriter", {})
    if copy_data:
        copy_packages = copy_data.get("copy_packages", "[]")
        input_data["copy_packages"] = copy_packages
        logger.info("  ✓ Copy packages loaded from copywriter")

    # --- Determine current revision round ---
    # Round increments each time visual_creator is called
    prev_round = upstream.get("visual_creator", {}).get("revision_round", -1)
    if prev_round == -1:
        # First call — check if copywriter has a round reference
        current_round = 0
    else:
        current_round = int(prev_round) + 1

    input_data["_current_revision_round"] = current_round
    logger.info(f"  Revision round: {current_round}")

    # --- HITL editor notes (from content_approval requesting visual revision) ---
    approval = upstream.get("content_approval", {})
    if approval:
        notes = approval.get("editor_notes", "")
        if notes:
            input_data["editor_notes"] = notes
            logger.info(f"  ✓ HITL visual revision notes: {notes[:80]}")

    # --- Inject round into context for LLM ---
    # The LLM prompt instructs it to use revision_round from input
    if "_current_revision_round" in input_data:
        input_data["revision_round_context"] = (
            f"Current revision_round is {current_round}. "
            f"{'This is the final round — set creative_finalized=true.' if current_round >= 7 else ''}"
        )

    logger.info(f"  LLM generating visual specs (round {current_round})...")
    return None  # Let LLM run
