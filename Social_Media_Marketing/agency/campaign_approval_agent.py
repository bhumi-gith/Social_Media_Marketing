"""Campaign Approval Agent — HITL gate #1.

Human reviews the campaign strategy (theme, colors, briefs) before
creative work begins. SDK handles the HITL webhook mechanism.

Webhook payload the human should send back:
  {
    "session_id": "<session_id>",
    "approval_status": "approved" | "revision_needed",
    "editor_notes": "optional notes for the strategist",
    "approved_strategy": "optional confirmation of what was approved"
  }
"""
from leafmesh import LeafMeshLogger

logger = LeafMeshLogger(__name__)


async def campaign_approval(llm_response, input_data, context):
    """HITL stub — SDK handles routing via human_interface: webhook."""
    logger.info("👤 Campaign Approval gate — waiting for human review...")
    # The SDK intercepts this agent and sends a HITL webhook.
    # This function is only called if human_interface: api is used.
    # With human_interface: webhook, the SDK handles everything.
    return {
        "approval_status": "",
        "approved_strategy": "",
        "editor_notes": "",
    }
