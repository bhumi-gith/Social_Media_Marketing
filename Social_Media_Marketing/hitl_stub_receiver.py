"""
HITL Stub Receiver — captures outbound webhook notifications from LeafMesh.

When the SDK's human agent (client) receives a task mid-flow, it sends an
outbound webhook to this stub. This simulates the external system that would
notify a real human (Slack, email, dashboard, etc).

The stub prints the webhook payload and a ready-to-use curl command so you
can respond as the human and continue the agent chain.

Usage:
    # Terminal 1: start the stub receiver
    python hitl_stub_receiver.py

    # Terminal 2: start the mesh
    python main.py

    # Terminal 3: trigger the mesh (Scenario 1 — system-initiated)
    curl -X POST http://127.0.0.1:18820/api/mesh/request \\
      -H "Content-Type: application/json" \\
      -d '{"entry_point": "greet_user", "data": {"message": "I need help with my order"}}'

    # ... the stub will print the outbound webhook + curl command to respond

See README.md for full HITL walkthrough (Scenario 1 and Scenario 2).
"""
import json
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime


class StubHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        print(f"\n{'='*60}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] OUTBOUND WEBHOOK RECEIVED")
        print(f"Path: {self.path}")
        print(f"{'='*60}")

        try:
            payload = json.loads(body)
            print(json.dumps(payload, indent=2, default=str))

            # Extract useful info for the human response
            session_id = payload.get("session_id", "unknown")
            agent = payload.get("agent_name", payload.get("from_agent", "unknown"))
            print(f"\n>>> To respond as the human, POST to the LeafMesh server.")
            print(f">>> The SDK binds HMAC to a fresh timestamp + nonce —")
            print(f">>> see the helper at the bottom of this file for a working example.")
            print(f"")
            print(f"    SECRET=$(curl -s http://127.0.0.1:18820/api/webhook/secret | jq -r .webhook_secret)")
            print(f"    TS=$(date +%s)")
            print(f"    NONCE=$(python3 -c 'import secrets; print(secrets.token_urlsafe(16))')")
            print(f"    BODY='{{\"session_id\": \"{session_id}\", \"decision\": \"approved\", \"message\": \"Looks good, proceed\"}}'")
            print(f"    SIG=$(printf '%s' \"$TS.$NONCE.$BODY\" | openssl dgst -sha256 -hmac \"$SECRET\" -hex | awk '{{print $NF}}')")
            print(f"    curl -X POST http://127.0.0.1:18820/webhook/greet_user \\\\")
            print(f'      -H "Content-Type: application/json" \\\\')
            print(f'      -H "X-LeafMesh-Signature: sha256=$SIG" \\\\')
            print(f'      -H "X-LeafMesh-Timestamp: $TS" \\\\')
            print(f'      -H "X-LeafMesh-Nonce: $NONCE" \\\\')
            print(f"      -d \"$BODY\"")
        except Exception:
            print(body.decode(errors="replace"))

        print(f"{'='*60}\n")
        sys.stdout.flush()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "received"}).encode())

    def log_message(self, format, *args):
        pass  # Suppress default logging


def sign_and_post_response(
    session_id: str,
    decision: str = "approved",
    message: str = "Looks good, proceed",
    leafmesh_url: str = "http://127.0.0.1:18820",
    entry_point: str = "greet_user",
) -> int:
    """Reference implementation for signing a HITL response on the SDK's
    HMAC-with-timestamp-and-nonce scheme.

    Pulls the webhook secret from /api/webhook/secret, builds the canonical
    signed material (`f"{ts}.{nonce}.".encode() + body`), and POSTs to
    /webhook/{entry_point} with all three headers.

    Returns the HTTP status code.
    """
    import hmac as _hmac
    import hashlib as _hashlib
    import secrets as _secrets
    import time as _time
    import urllib.request as _ur

    # Fetch the signing secret from the SDK.
    try:
        with _ur.urlopen(f"{leafmesh_url}/api/webhook/secret", timeout=5) as resp:
            secret_data = json.loads(resp.read())
    except Exception as e:
        print(f"Could not fetch webhook secret from {leafmesh_url}: {e}")
        return 0
    secret = (secret_data or {}).get("webhook_secret")
    if not secret:
        print("Server is not configured for webhook auth — set LEAFMESH_LICENSE_KEY or LEAFMESH_WEBHOOK_SECRET.")
        return 0

    body = json.dumps(
        {"session_id": session_id, "decision": decision, "message": message}
    ).encode("utf-8")
    timestamp = str(int(_time.time()))
    nonce = _secrets.token_urlsafe(16)
    signed_material = f"{timestamp}.{nonce}.".encode("utf-8") + body
    sig = _hmac.new(secret.encode("utf-8"), signed_material, _hashlib.sha256).hexdigest()

    req = _ur.Request(
        f"{leafmesh_url}/webhook/{entry_point}",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-LeafMesh-Signature": f"sha256={sig}",
            "X-LeafMesh-Timestamp": timestamp,
            "X-LeafMesh-Nonce": nonce,
        },
    )
    try:
        with _ur.urlopen(req, timeout=10) as resp:
            return resp.status
    except Exception as e:
        print(f"POST failed: {e}")
        return 0


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 9999), StubHandler)
    print(f"HITL Stub Receiver listening on http://127.0.0.1:9999")
    print(f"Waiting for outbound webhook notifications from LeafMesh...\n")
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
