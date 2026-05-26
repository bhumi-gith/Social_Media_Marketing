# Event Listeners

Trigger agents from external event sources — Kafka, SQS, MQTT, Redis Streams, IMAP — without writing a single line of glue code. Configure brokers once, attach listeners to agents in YAML, and the SDK manages connections, retries, idempotency, and dead-lettering.

## When to Use

- A Kafka topic publishes orders and an agent should process each one
- SQS queues fan-in alerts that should escalate through the mesh
- MQTT sensor readings should kick off an analysis agent
- Redis Streams from an upstream service should drive workflow steps
- IMAP polling for environments where webhook-based email isn't possible

## Two-Block Model

LeafMesh separates **connections** from **subscriptions** — same pattern as Knative Brokers/Triggers, Dapr Components/Bindings, and Azure Functions `Connection=` parameters.

```
brokers:                            # Connection registry (top-level)
  prod_kafka: { type: kafka, ... }
  alerts_sqs: { type: sqs, ... }

agents:
  order_processor:
    listen_events:                  # Per-agent subscriptions
      - broker: "prod_kafka"
        topic: "orders.new"
      - broker: "alerts_sqs"
        queue: "high-priority"
```

One broker connection serves any number of listeners across any number of agents. The SDK opens one consumer per `(broker, topic/queue/stream)` group and fans messages out to the right agent.

## End-to-End Example

```yaml
name: "order_pipeline"
architecture: "managed_mesh"

brokers:
  prod_kafka:
    type: "kafka"
    bootstrap_servers: ["kafka-1:9092", "kafka-2:9092"]
    security_protocol: "SASL_SSL"
    sasl_mechanism: "SCRAM-SHA-512"
    sasl_username: "${KAFKA_USERNAME}"
    sasl_password: "${KAFKA_PASSWORD}"

  alerts_sqs:
    type: "sqs"
    region: "us-east-1"

agents:
  order_processor:
    name: "order_processor"
    agent_type: "llm"
    model: "gpt-4o-mini"
    prompt: |
      Process the order, validate inventory, and route to fulfillment or escalation.
    yields:
      action: "string"
      ticket_id: "string"
    listen_events:
      - broker: "prod_kafka"
        topic: "orders.new"
        group_id: "order-processor-v1"
        filter:
          type: "com.example.order.created"
        deserialize: "myapp.schemas:OrderEvent"
        delivery:
          max_attempts: 5
          backoff: "exponential"
          dead_letter:
            broker: "prod_kafka"
            topic: "orders.dlq"

  alert_handler:
    name: "alert_handler"
    agent_type: "llm"
    model: "gpt-4o-mini"
    listen_events:
      - broker: "alerts_sqs"
        queue: "high-priority-alerts"
        visibility_heartbeat: true
        delivery:
          max_attempts: 3
```

## Lifecycle

When the SDK starts:

- Each `listen_events` entry on every agent is validated against its broker. Validation errors fail SDK startup.
- One concurrent listener is spun up per `(broker, topic/queue/stream)` group.
- Listeners run until `SDK.stop()`, which drains in-flight messages with a 30-second timeout before closing connections (committing offsets, releasing leases).

## Per-Message Flow

For every inbound message, every listener runs the same five-stage pipeline:

```
        [external source]
                │
                ▼
        ┌───────────────────┐
        │ 1. Verify         │  ← signature/credentials at the connection layer
        └───────────────────┘
                │
                ▼
        ┌───────────────────┐
        │ 2. Filter         │  ← CloudEvents attribute equality (AND)
        └───────────────────┘   non-match → ack and skip
                │ match
                ▼
        ┌───────────────────┐
        │ 3. Idempotency    │  ← skip messages already seen within retention
        └───────────────────┘   already seen → ack and skip
                │ new
                ▼
        ┌───────────────────┐
        │ 4. Deserialize    │  ← Pydantic class (optional)
        └───────────────────┘   ValidationError → DLQ (no retry)
                │ ok
                ▼
        ┌───────────────────┐
        │ 5. Dispatch       │  ← Triggers the agent
        └───────────────────┘   same execution path as POST /webhook/{name}
                │
                ▼
        success → ack source     failure → retry per delivery.backoff
                                  exhausted → DLQ if configured
```

## At-Least-Once Delivery

Every listener uses **at-least-once** semantics. Messages may be delivered more than once on retry — the idempotency check at stage 3 ensures the agent sees each unique `message_id` exactly once within the configured retention window.

| Source | Idempotency Key Source |
|--------|------------------------|
| Kafka | `topic + partition + offset` |
| SQS | `MessageId` |
| Redis Streams | Stream entry ID (`<ms>-<seq>`) |
| MQTT | `packet_id` (QoS ≥ 1) or content hash (QoS 0) |
| IMAP | `Message-ID` header |

Idempotency retention defaults to 24 hours — long enough to absorb retry storms, short enough that storage doesn't grow unbounded.

## Filtering

Filters are CloudEvents-style attribute equality. All keys must match for the message to be delivered (AND semantics):

```yaml
listen_events:
  - broker: "prod_kafka"
    topic: "events"
    filter:
      type: "com.example.order.created"
      source: "checkout-service"
```

Non-matching messages are acked and skipped — they don't count against retries or hit the DLQ.

For filtering on payload contents (not envelope attributes), use `deserialize:` and let your handler decide.

## Deserialization

Set `deserialize:` to a `module.path:ClassName` string and the SDK will validate the payload through that Pydantic class before dispatching:

```yaml
listen_events:
  - broker: "prod_kafka"
    topic: "orders.new"
    deserialize: "myapp.schemas:OrderEvent"
```

```python
# myapp/schemas.py
from pydantic import BaseModel
from decimal import Decimal

class OrderEvent(BaseModel):
    order_id: str
    customer_id: str
    total: Decimal
    items: list[str]
```

`ValidationError` routes the message straight to DLQ — bad data won't fix itself by retrying.

## Retry & Dead Letter

Retries are configured per listener under `delivery:`:

```yaml
delivery:
  max_attempts: 5
  backoff: "exponential"             # or "linear"
  backoff_initial_s: 2.0
  backoff_max_s: 120.0
  dead_letter:
    broker: "prod_kafka"             # any broker in the registry
    topic: "orders.dlq"
```

Backoff curves:

- `exponential`: `min(initial * 2^(attempt-1), max)` — `2s, 4s, 8s, 16s, 32s, …`
- `linear`: `min(initial * attempt, max)` — `2s, 4s, 6s, 8s, …`

After `max_attempts`, the message is published to `dead_letter` (if set) with a `delivery_metadata` block that includes the original message, all attempt timestamps, and the last error. If `dead_letter` is unset, the message is logged and dropped.

DLQs can target any broker type — you can DLQ Kafka messages into SQS, IMAP messages into Redis Streams, etc. The listener validates that the destination shape (`topic` / `queue` / `stream`) matches the destination broker's type at startup.

## TriggerEvent Envelope

Every listener wraps the source-specific payload in a normalized `TriggerEvent` envelope (CloudEvents-shaped). The agent's intelligence function receives this as `input_data`:

```python
{
    "specversion": "1.0",
    "type": "com.example.order.created",
    "source": "kafka:orders.new",
    "id": "0-12345",                 # source-specific message ID
    "time": "2026-05-09T10:30:00Z",
    "data": { ... },                 # the deserialized payload
    "leafmesh": {
        "listener": "order_processor.0",
        "broker": "prod_kafka",
        "attempt": 1,
        "headers": { ... },          # original transport headers
    },
}
```

Inside an intelligence function:

```python
async def order_processor(llm_response, input_data, context):
    order = input_data["data"]                        # deserialized OrderEvent
    listener = input_data["leafmesh"]["listener"]
    return {"action": "fulfilled", "ticket_id": order["order_id"]}
```

## Metering & Audit

Listener-triggered invocations count toward [BRD-012 invocation metering](../advanced/invocation-metering) the same way HTTP-triggered ones do — the agent runs through `ENTRY_POINT`, which is the single chokepoint where invocation counters are incremented. There's no separate accounting for event-driven agents.

Audit log entries record the broker name, listener name, source-specific message ID, attempt count, and final outcome (success / retried / DLQ).

## Health & Observability

Check live listener status:

```
GET /api/system/event-listeners
```

Returns each listener's broker, source destination, current state (`running` / `paused` / `failed`), in-flight message count, last successful dispatch timestamp, and retry/DLQ counters since startup.

The dashboard surfaces per-listener metrics: messages received, messages dispatched, messages filtered, messages dead-lettered, and dispatch duration. Each metric is broken down by broker, listener name, agent, and source (topic/queue/stream/folder).

## Required Extras

Each broker type pulls in its own driver. Install the matching extras:

```bash
pip install leafmesh[kafka]      # aiokafka
pip install leafmesh[sqs]        # aioboto3
pip install leafmesh[mqtt]       # asyncio-mqtt
pip install leafmesh[imap]       # aioimaplib
pip install leafmesh[listeners]  # all of the above
```

`redis_streams` listeners use the SDK's existing Redis driver — no extra install required.

## Next Steps

- **[Agent Configuration — listen_events](../api-reference/agent-config-fields#agentconfig--core-fields-all-types)** — Field reference
- **[BrokerConfig](../api-reference/agent-config-fields#brokerconfig)** — Per-broker schemas
- **[EventListener](../api-reference/agent-config-fields#eventlistener)** — Listener-side fields, retry, DLQ
- **[Broker API Endpoints](../api-reference/configuration#brokers)** — REST CRUD for brokers
- **[Email Channel](../agents/human-agents#email-channel)** — Webhook-based email (companion to IMAP)

---

*LeafMesh — One YAML, every event source*
