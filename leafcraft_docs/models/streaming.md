# Streaming

LeafMesh supports streaming LLM responses for real-time output delivery. When streaming is enabled, the LLM sends response tokens as they are generated rather than waiting for the complete response.

## Configuration

Enable streaming in the agent's model configuration:

```yaml
agents:
  streaming_agent:
    name: "streaming_agent"
    model: "gpt-4o"
    prompt: |
      Provide detailed analysis of the input data.
    yields:
      analysis: "string"
      confidence: "number"
```

Streaming is supported whenever the underlying provider supports it -- OpenAI, Anthropic, and Google all support streaming.

## Integration Pattern

Streaming works through the API layer. When an external system connects via the FastAPI endpoints with streaming enabled, the response is delivered progressively:

```
Client Request → API Server → LLM Provider (streaming)
                                    │
                                    ├── Token 1 → Client
                                    ├── Token 2 → Client
                                    ├── Token 3 → Client
                                    └── Final   → Client
```

The unified LLM request includes a `stream` flag that activates streaming mode.

## Yields and Streaming

When streaming is active, the yields schema is still enforced — but parsing happens on the complete response after all tokens have been received. The stream provides progressive output to the client while the pipeline validation runs on the final assembled response.

## When to Use Streaming

| Use Case | Streaming? |
|----------|-----------|
| Real-time user interfaces | Yes — progressive display |
| API-to-API calls | Usually no — wait for complete response |
| Agent-to-agent mesh calls | No — can_call needs complete yields |
| Long-form generation | Yes — reduces perceived latency |

## Next Steps

- **[LLM Providers](providers)** — Provider-specific streaming support
- **[Structured Output](structured-output)** — Output formatting and validation

---

*LeafMesh — Progressive response delivery*
