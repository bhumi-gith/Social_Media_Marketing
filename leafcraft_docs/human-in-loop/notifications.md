# Notifications & Alerts

Setting up notification systems for human-in-the-loop workflows.

## Event-Based Notifications

Subscribe to HILT events to trigger notifications:

```python
from leafmesh import LeafMesh

leafmesh = LeafMesh.from_yaml("config.yaml")

async def notify_on_review_needed(event):
    """Triggered when a human agent receives a request"""
    session_id = event.session_id
    agent_name = event.data.get("agent_name", "unknown")

    # Send notification through your preferred channel
    await send_slack_notification(
        channel="#reviews",
        message=f"Review needed: {agent_name} (session: {session_id})"
    )

async def notify_on_timeout(event):
    """Triggered when a human doesn't respond in time"""
    session_id = event.session_id

    await send_slack_notification(
        channel="#reviews-urgent",
        message=f"TIMEOUT: Review expired for session {session_id}"
    )

# These notifications are triggered automatically via webhook_config in YAML.
# Configure the human agent's webhook_config to point to your notification service,
# which handles Slack, email, or other alerting.
```

## Webhook Notifications

Configure the human agent's webhook to point to your notification service:

```yaml
agents:
  urgent_reviewer:
    agent_type: "human"
    timeout: 120
    webhook_config:
      url: "https://notifications.example.com/urgent-review"
      method: "POST"
    yields:
      approved: "boolean"
      notes: "string"
```

Your notification service receives the webhook, notifies the appropriate reviewer, collects their response, and returns it.

## Escalation Notifications

Set up escalation when reviews are not handled in time:

```yaml
agents:
  primary_reviewer:
    agent_type: "human"
    timeout: 300
    webhook_config:
      url: "https://review.example.com/primary"
      method: "POST"
    yields:
      decision: "string"
    can_call:
      - agent: "backup_reviewer"
        condition: "decision == 'escalate'"

  backup_reviewer:
    agent_type: "human"
    timeout: 600
    webhook_config:
      url: "https://review.example.com/backup"
      method: "POST"
    yields:
      decision: "string"
```

When the primary reviewer escalates (or times out and the Manager routes to backup), the backup reviewer receives a notification with full context.

## Notification Channels

Common integration patterns:

| Channel | Integration Method |
|---------|-------------------|
| Slack | Webhook POST to Slack API |
| Email | SMTP via notification service |
| SMS | Twilio or similar API |
| In-app | WebSocket push to browser |
| PagerDuty | Event API for urgent escalations |

## Next Steps

- **[Approval Workflows](workflows)** — Multi-step patterns
- **[UI Integration](ui-integration)** — Review interfaces
- **[Event System](../core-concepts/events)** — Event reference

---

*LeafMesh — Notification systems for human review*
