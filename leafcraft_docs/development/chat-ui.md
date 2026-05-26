# Agent Chat UI

Building interactive chat interfaces for LeafMesh agents using the FastAPI services.

## API-Based Chat

Use the LeafMesh API server to build chat interfaces:

```python
from leafmesh import LeafMesh
import asyncio

leafmesh = LeafMesh.from_yaml("config.yaml")

async def chat_loop():
    await leafmesh.start()
    session_id = "chat_session_001"

    print("Chat with the agent (type 'quit' to exit)")
    while True:
        user_input = input("You: ")
        if user_input.lower() == "quit":
            break

        result = await leafmesh.mesh_call(
            "chat_agent",
            input_data={"user_message": user_input},
            session_id=session_id
        )

        response = result.get("response", str(result))
        print(f"Agent: {response}")

    await leafmesh.stop()

asyncio.run(chat_loop())
```

## FastAPI Chat Endpoint

Expose chat functionality as an API:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from leafmesh import LeafMesh

app = FastAPI()
leafmesh = LeafMesh.from_yaml("config.yaml")

class ChatRequest(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    response: str
    session_id: str
    agent: str

@app.on_event("startup")
async def startup():
    await leafmesh.start()

@app.on_event("shutdown")
async def shutdown():
    await leafmesh.stop()

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = await leafmesh.mesh_call(
        "chat_agent",
        input_data={"user_message": request.message},
        session_id=request.session_id
    )
    return ChatResponse(
        response=result.get("response", str(result)),
        session_id=request.session_id,
        agent=result.get("_agent", "chat_agent")
    )
```

## Streaming Responses

For real-time chat interfaces, use streaming mode:

```yaml
agents:
  chat_agent:
    model: "gpt-4o"
    stream: true
    prompt: "You are a helpful assistant."
    yields:
      response: "string"
```

When `stream: true`, the LLM response is streamed token-by-token. Yields validation runs on the complete response.

## Session Management

Each chat session maintains conversation history automatically. The full transcript — role, content, agent attribution, timestamps — is browsable in **Studio's Sessions tab**, or available via the session REST endpoint (`GET /session/{session_id}`) for embedding into your own UI.

## Multi-Agent Chat

A chat interface that routes to different agents based on the conversation:

```yaml
agents:
  router:
    model: "gpt-4o-mini"
    prompt: "Classify the user's request and route to the right specialist."
    yields:
      intent: "string"
    can_call:
      - agent: "tech_support"
        condition: "intent == 'technical'"
      - agent: "billing_support"
        condition: "intent == 'billing'"
      - agent: "general_chat"
        condition: "intent not in ['technical', 'billing']"
```

The user interacts with a single chat interface, but different agents handle different request types transparently.

## Next Steps

- **[Agent Studio](agent-studio)** — Development environment
- **[FastAPI Integration](../deployment/production)** — Production API setup
- **[Session Management](../core-concepts/sessions)** — Session lifecycle

---

*LeafMesh — Interactive chat interfaces*
