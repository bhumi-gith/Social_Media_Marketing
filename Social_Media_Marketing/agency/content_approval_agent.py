"""Content Approval Agent — HITL gate #2 (marketing team).

Marketing team reviews the FINAL copy + visuals before publishing.
SDK handles the HITL webhook mechanism.

Webhook payload the human should send back:
  {
    "session_id": "<session_id>",
    "approval_status": "approved" | "revision_visuals" | "revision_copy",
    "reviewer_name": "Jane Smith",
    "review_timestamp": "2026-05-26T10:30:00Z",
    "editor_notes": "specific feedback if revision requested",
    "approved_copy": "optional: paste the approved copy text",
    "approved_visuals": "optional: confirmation of approved visuals"
  }
"""
from leafmesh import LeafMeshLogger

logger = LeafMeshLogger(__name__)


async def content_approval(llm_response, input_data, context):
    """HITL stub — SDK handles routing via human_interface: webhook."""
    logger.info("👥 Content Approval gate (marketing team) — waiting for review...")
    # The SDK intercepts this agent and sends a HITL webhook.
    # This function is only called if human_interface: api is used.
    return {
        "approval_status": "",
        "approved_copy": "",
        "approved_visuals": "",
        "reviewer_name": "",
        "review_timestamp": "",
        "editor_notes": "",
    }
