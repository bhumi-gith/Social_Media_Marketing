# LLM Providers

LeafMesh provides a unified interface across multiple LLM providers. Specify any supported model in the `model:` field of an agent and the platform routes the request to the correct provider automatically. No provider-specific code is needed.

## Supported Providers

| Provider | Example Models |
|----------|----------------|
| OpenAI | gpt-4o, gpt-4o-mini, gpt-4-turbo, o1, o3-mini |
| Anthropic | claude-3.5-sonnet, claude-sonnet-4, claude-opus-4 |
| Google | gemini-1.5-pro, gemini-2.0-flash |
| DeepSeek | deepseek-chat, deepseek-coder, deepseek-reasoner |
| Amazon Bedrock | bedrock/claude-3.5-sonnet, bedrock/llama3-70b, bedrock/mistral-large |
| Google Vertex AI | vertex/gemini-2.5-flash, vertex/claude-sonnet-4-20250514, vertex/mistral-large |
| Microsoft Foundry | foundry/gpt-4o, foundry/DeepSeek-R1, foundry/Meta-Llama-3.1-70B, foundry/Mistral-Large |
| Local | llama3.1, mistral, codellama (or any model served behind a `custom_endpoint`) |

---

## Provider Setup

### OpenAI

```yaml
agents:
  openai_agent:
    name: "openai_agent"
    model: "gpt-4o"              # GPT-4 Omni
    # model: "gpt-4o-mini"       # Cost-effective option
    # model: "gpt-4-turbo"       # GPT-4 Turbo
    # model: "o1"                # Reasoning model
    # model: "o3-mini"           # Small reasoning model
```

**Environment variables:**
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: custom endpoint
```

### Anthropic

```yaml
agents:
  claude_agent:
    name: "claude_agent"
    model: "claude-3.5-sonnet"   # Claude 3.5 Sonnet
    # model: "claude-sonnet-4"   # Claude Sonnet 4
    # model: "claude-opus-4"     # Claude Opus 4
    # model: "claude-3.5-haiku"  # Fast, cost-effective
```

**Environment variables:**
```env
ANTHROPIC_API_KEY=sk-ant-your-anthropic-api-key
```

### Google Gemini

```yaml
agents:
  gemini_agent:
    name: "gemini_agent"
    model: "gemini-1.5-pro"      # Gemini 1.5 Pro
    # model: "gemini-2.0-flash"  # Fast Gemini model
    # model: "gemini-1.5-flash"  # Cost-effective Gemini
```

**Environment variables:**
```env
GOOGLE_API_KEY=your-google-api-key
```

### DeepSeek

```yaml
agents:
  deepseek_agent:
    name: "deepseek_agent"
    model: "deepseek-chat"       # DeepSeek Chat
    # model: "deepseek-coder"    # Code-focused model
    # model: "deepseek-reasoner" # Reasoning model
```

**Environment variables:**
```env
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### Local Models (Ollama, vLLM, LM Studio)

Run models locally for data privacy and cost control. The local provider supports Ollama native, OpenAI-compatible (vLLM, LM Studio, LocalAI), Text Generation Web UI, and Hugging Face Inference endpoints.

#### Ollama

```yaml
agents:
  local_agent:
    name: "local_agent"
    model: "llama3.1"            # Model name as shown by `ollama list`
    # model: "mistral"
    # model: "codellama"
```

**Environment variables:**
```env
LOCAL_MODEL_ENDPOINT=http://localhost:11434/api/generate
```

Start Ollama and pull a model:
```bash
# Install Ollama (macOS)
brew install ollama

# Start the server
ollama serve

# Pull a model
ollama pull llama3.1
```

#### vLLM (OpenAI-compatible)

```yaml
agents:
  vllm_agent:
    name: "vllm_agent"
    model: "mistral-7b"
```

**Environment variables:**
```env
LOCAL_MODEL_ENDPOINT=http://localhost:8000/v1/chat/completions
```

Start vLLM:
```bash
python -m vllm.entrypoints.openai.api_server \
  --model mistralai/Mistral-7B-Instruct-v0.2 \
  --port 8000
```

#### LM Studio

```yaml
agents:
  lmstudio_agent:
    name: "lmstudio_agent"
    model: "local-model"
```

**Environment variables:**
```env
LOCAL_MODEL_ENDPOINT=http://localhost:1234/v1/chat/completions
```

LM Studio serves an OpenAI-compatible API by default. Start the server from the LM Studio UI, then point LeafMesh at it.

#### Supported Local Server Formats

| Format | Examples | Features |
|--------|----------|----------|
| OpenAI-compatible (chat completions) | vLLM, LM Studio, LocalAI, Ollama /v1 | Tool calling, structured output, streaming |
| Text Generation Web UI | oobabooga | Basic text generation |
| Hugging Face Inference API | HF Inference Endpoints | Basic text generation |
| Ollama native | Standard Ollama | Basic text generation |

Set `LOCAL_MODEL_ENDPOINT` to the URL of your local server -- the platform handles the payload format automatically.

### Amazon Bedrock

Route all LLM calls through AWS Bedrock for unified billing, VPC networking, and IAM-based access control. Bedrock hosts models from multiple providers (Anthropic, Meta, Mistral, Cohere, Amazon) behind a single API.

Use the `bedrock/` prefix to route any model through Bedrock instead of calling the provider directly:

```yaml
mesh:
  bedrock:
    region: "us-east-1"             # AWS region (default: us-east-1)
    # profile: "prod-profile"       # Optional: AWS CLI profile name
    # endpoint_url: "https://..."   # Optional: VPC endpoint

agents:
  analyst:
    name: "analyst"
    model: "bedrock/claude-3.5-sonnet"   # Claude via Bedrock

  condenser:
    name: "condenser"
    model: "bedrock/llama3-70b"          # Llama via Bedrock

  classifier:
    name: "classifier"
    model: "bedrock/mistral-large"       # Mistral via Bedrock
```

**Authentication:** Uses standard AWS credential chain -- environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`), `~/.aws/credentials` profile, or IAM role (EC2/ECS/Lambda).

Bedrock support (boto3) is included with `pip install leafmesh`.

**Available aliases:**

| Alias | Bedrock Model ID |
|-------|-----------------|
| `claude-3.5-sonnet` | `anthropic.claude-3-5-sonnet-20241022-v2:0` |
| `claude-3-haiku` | `anthropic.claude-3-haiku-20240307-v1:0` |
| `claude-3-opus` | `anthropic.claude-3-opus-20240229-v1:0` |
| `llama3-70b` | `meta.llama3-70b-instruct-v1:0` |
| `llama3-8b` | `meta.llama3-8b-instruct-v1:0` |
| `mistral-large` | `mistral.mistral-large-2402-v1:0` |
| `titan-text-express` | `amazon.titan-text-express-v1` |
| `command-r-plus` | `cohere.command-r-plus-v1:0` |

You can also pass full Bedrock model IDs directly: `bedrock/anthropic.claude-3-sonnet-20240229-v1:0`.

### Google Vertex AI

Route all LLM calls through Google Cloud Vertex AI for unified billing, IAM, and access to models from multiple publishers (Google, Anthropic, Mistral, Meta) through a single control plane.

Use the `vertex/` prefix to route any model through Vertex AI:

```yaml
mesh:
  vertex:
    project: "my-gcp-project"       # Required: GCP project ID
    location: "us-central1"         # Default: us-central1

agents:
  analyst:
    name: "analyst"
    model: "vertex/gemini-2.5-flash"            # Google Gemini via Vertex

  reviewer:
    name: "reviewer"
    model: "vertex/claude-sonnet-4-20250514"    # Claude via Vertex

  coder:
    name: "coder"
    model: "vertex/mistral-large"               # Mistral via Vertex

  condenser:
    name: "condenser"
    model: "vertex/llama-4-scout"               # Llama via Vertex
```

**Authentication:** Uses Google Cloud Application Default Credentials (ADC).

```bash
# Local development
gcloud auth application-default login

# Or set service account key
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json

# GKE / Cloud Run: automatic via attached service account
```

Vertex AI support (google-auth) is included with `pip install leafmesh`.

**Available aliases:**

| Alias | Publisher | Vertex Model ID |
|-------|-----------|----------------|
| `gemini-2.5-pro` | Google | `gemini-2.5-pro` |
| `gemini-2.5-flash` | Google | `gemini-2.5-flash` |
| `gemini-2.0-flash` | Google | `gemini-2.0-flash` |
| `claude-sonnet-4-20250514` | Anthropic | `claude-sonnet-4@20250514` |
| `claude-opus-4` | Anthropic | `claude-opus-4@20250514` |
| `claude-3.5-sonnet` | Anthropic | `claude-3-5-sonnet-v2@20241022` |
| `mistral-large` | Mistral | `mistral-large@2411` |
| `codestral` | Mistral | `codestral@2501` |
| `llama-4-scout` | Meta | `llama-4-scout-17b-16e-instruct-maas` |
| `llama-4-maverick` | Meta | `llama-4-maverick-17b-128e-instruct-maas` |

The platform handles the request format for each publisher automatically -- Gemini, Anthropic, Mistral, and Meta models all work through the same `vertex/` prefix.

### Microsoft Foundry

Route all LLM calls through Microsoft Foundry (Azure AI Foundry) for unified billing and access to any model deployed in your Azure AI resource -- OpenAI, DeepSeek, Llama, Mistral, Grok, Phi, Cohere, and more.

Use the `foundry/` prefix followed by your deployment name:

```yaml
mesh:
  foundry:
    endpoint: "https://my-resource.openai.azure.com"   # Required: your Foundry endpoint
    # api_version: "2024-10-21"                        # Optional: use legacy versioned API

agents:
  analyst:
    name: "analyst"
    model: "foundry/gpt-4o"                    # OpenAI via Foundry

  reasoner:
    name: "reasoner"
    model: "foundry/DeepSeek-R1"               # DeepSeek via Foundry

  condenser:
    name: "condenser"
    model: "foundry/Meta-Llama-3.1-70B"        # Llama via Foundry

  coder:
    name: "coder"
    model: "foundry/Mistral-Large-2411"        # Mistral via Foundry
```

**Authentication:** API key or Entra ID (Bearer token).

```bash
# API key auth (recommended for getting started)
export AZURE_FOUNDRY_API_KEY="your-api-key"

# Or Entra ID / managed identity token
export AZURE_FOUNDRY_TOKEN="your-bearer-token"
```

No extra dependencies -- Foundry uses the OpenAI-compatible endpoint, and `openai` is already a core dependency.

**How it works:** Models are deployed in your Azure AI resource first (via Azure Portal or CLI). The deployment name becomes the model identifier after the `foundry/` prefix. Foundry exposes an OpenAI-compatible `/openai/v1/` endpoint, so all standard features (tool calling, structured output, streaming) work across every model.

**Two API modes:**
- **v1 (default, recommended):** Omit `api_version`. Uses the new `/openai/v1/` unified endpoint -- no version parameter needed.
- **Legacy versioned:** Set `api_version: "2024-10-21"`. Uses Azure's `/openai/deployments/{name}/...?api-version=X` path via the `AzureOpenAI` client. Use this for older Azure OpenAI resources or features only available in preview API versions.

---

## Automatic Provider Routing

You never configure a provider explicitly -- just set the model. The platform routes the request to the correct provider automatically:

```yaml
agents:
  solver:
    name: "solver"
    model: "gpt-4o-mini"          # Routes to OpenAI

  analyst:
    name: "analyst"
    model: "claude-3.5-sonnet"    # Routes to Anthropic

  translator:
    name: "translator"
    model: "gemini-2.0-flash"     # Routes to Google

  coder:
    name: "coder"
    model: "deepseek-coder"       # Routes to DeepSeek

  private:
    name: "private"
    model: "llama3.1"             # Routes to a local model server
```

For cloud gateways, prefix the model name in your YAML: `bedrock/...`, `vertex/...`, or `foundry/...`. Custom providers may register their own model name prefixes via the SDK.

### Startup Behavior

At startup, LeafMesh checks for API keys and connectivity for each provider in use. Providers that are not available (missing API keys, unreachable endpoints) are skipped with a warning but do not prevent the system from starting. At least one provider must be available.

---

## Model Configuration

### Per-Agent Settings

Each agent configures its own model parameters directly in YAML:

```yaml
agents:
  precise_agent:
    name: "precise_agent"
    model: "gpt-4o"
    temperature: 0.1           # Low randomness for consistency
    max_tokens: 500            # Limit response length

  creative_agent:
    name: "creative_agent"
    model: "claude-3.5-sonnet"
    temperature: 0.8           # Higher randomness for creativity
    max_tokens: 2000           # Longer responses
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | required | Model identifier (e.g., `"gpt-4o"`) |
| `temperature` | float | 0.1 | Sampling temperature (0.0-2.0) |
| `max_tokens` | int | 1000 | Maximum response tokens |
| `top_p` | float | 1.0 | Nucleus sampling threshold |
| `tool_choice` | string | `"auto"` | Tool calling mode |
| `max_tool_calls_per_message` | int | 5 | Maximum tool calls per execution (range 0-20) |
| `optimization_strategy` | string | none | Adaptive model selection: `"performance"`, `"cost"`, or `"speed"` |

---

## Multi-Provider Architecture

Different agents in the same system can use different providers. This reduces systematic bias from any single model, provides natural redundancy against provider outages, and enables cost optimization.

### Practical Multi-Provider Configuration

```yaml
name: "multi_provider_system"
architecture: "managed_mesh"

agents:
  # Fast, cheap classification
  triage:
    name: "triage"
    model: "gpt-4o-mini"
    temperature: 0.1
    prompt: |
      Classify the incoming request into one of: billing, technical, general.
    yields:
      category: "string"
      urgency: "number"
    can_call:
      - agent: "specialist"
        condition: "category == 'technical'"
      - agent: "billing_handler"
        condition: "category == 'billing'"

  # Strong reasoning for complex analysis
  specialist:
    name: "specialist"
    model: "claude-3.5-sonnet"
    temperature: 0.3
    prompt: |
      You are a technical specialist. Analyze the issue and provide a solution.
    yields:
      solution: "string"
      confidence: "number"

  # Cost-effective for structured tasks
  billing_handler:
    name: "billing_handler"
    model: "gpt-4o-mini"
    temperature: 0.0
    prompt: |
      You handle billing inquiries. Look up account details and resolve issues.
    yields:
      resolution: "string"
      amount: "number"
```

### Provider Failure Isolation

If one provider experiences downtime, only agents using that provider are affected. Other agents continue operating normally:

```
Agents 1-3 use OpenAI    --> OpenAI outage --> Agents 1-3 unavailable
Agents 4-5 use Anthropic --> Unaffected    --> Continue operating
Agents 6-7 use Google    --> Unaffected    --> Continue operating
```

LeafMesh's self-healing detects elevated failure rates, reroutes traffic away from affected agents, and restores normal routing automatically when the provider recovers.

---

## Custom Provider Registration

Register custom providers at runtime for internal model serving infrastructure:

```python
from leafmesh import LLMProvider, LLMRequest, LLMResponse

class InternalProvider(LLMProvider):
    def is_available(self) -> bool:
        # Check if your internal endpoint is reachable
        return True

    async def generate(self, request: LLMRequest) -> LLMResponse:
        # Forward request to your internal model serving
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://internal-models.company.com/v1/generate",
                json={"prompt": request.prompt, "model": request.model}
            ) as resp:
                data = await resp.json()

        return LLMResponse(
            content=data["text"],
            model=request.model,
            usage={"prompt_tokens": data.get("prompt_tokens", 0),
                   "completion_tokens": data.get("completion_tokens", 0)},
            provider="internal",
            success=True
        )
```

Register the provider with optional model name prefixes:

```python
# Register with model prefix routing
leafmesh.register_llm_provider("internal", InternalProvider, model_prefixes=["internal-", "company-"])
```

After registration, any agent with `model: "internal-llama-70b"` or `model: "company-gpt"` will automatically route to your custom provider.

---

## LLM Cost Tracking

LeafMesh tracks the cost of every LLM call -- model used, token counts, estimated cost, response time, and whether the response was served from cache. A built-in pricing table covers the major OpenAI, Anthropic, and Google models; models not in the table (including local models) use a fallback estimate.

```python
# Get aggregated cost and usage statistics
analytics = await leafmesh.get_usage_analytics()
cache_stats = await leafmesh.get_llm_cache_stats()
```

Identical requests are deduplicated through the response cache -- see **[LLM Response Caching](caching)**.

---

## Unified LLM Request

LeafMesh exposes a single LLM interface that works across every supported provider, handling differences in message format, tool calling syntax, and response parsing:

```python
# Direct LLM call from an intelligence function
response = await leafmesh.call_llm(
    prompt="Summarize this data",
    model="gpt-4o",
    temperature=0.3,
    max_tokens=500
)
```

The unified request supports: messages, model, temperature, max_tokens, tools, tool_choice, response_format, stream flag, files, custom endpoints, and custom headers.

---

## LLM Types Reference

These types are exported from the `leafmesh` package for custom provider implementation and direct LLM calls.

### LLMRequest

Standard request structure sent to all LLM providers. Supports multimodal input, tool calling, streaming, and reasoning enhancement.

```python
from leafmesh import LLMRequest
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prompt` | `str` | required | The prompt text |
| `model` | `str` | `"gpt-4o-mini"` | Model identifier |
| `temperature` | `float` | `0.1` | Sampling temperature |
| `max_tokens` | `int` | `800` | Maximum response tokens |
| `system_prompt` | `str` | `None` | System prompt |
| `context` | `dict` | `{}` | Additional context |
| `tools` | `list` | `[]` | Tool schemas for function calling |
| `tool_choice` | `str` | `None` | Tool calling mode (`"auto"`, `"required"`, `"none"`) |
| `tool_call_depth` | `int` | `0` | Current recursion depth in tool call loop |
| `max_tool_calls` | `int` | `5` | Maximum tool calls per conversation |
| `messages` | `list` | `[]` | Conversation messages array |
| `response_format` | `dict` | `None` | JSON schema for structured output |
| `stream` | `bool` | `False` | Enable streaming response |
| `files` | `list` | `[]` | File objects or URLs for multimodal input |
| `reasoning` | `bool` | `False` | Enable chain-of-thought reasoning tools |
| `custom_endpoint` | `str` | `None` | Custom API endpoint URL |
| `custom_headers` | `dict` | `{}` | Custom HTTP headers |

### LLMResponse

Standard response structure returned by all LLM providers.

```python
from leafmesh import LLMResponse
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `content` | `str` | required | Response text content |
| `model` | `str` | required | Model that generated the response |
| `usage` | `dict` | required | Token usage (`{"prompt_tokens": N, "completion_tokens": N}`) |
| `provider` | `str` | required | Provider name (e.g. `"openai"`, `"anthropic"`) |
| `success` | `bool` | `True` | Whether the call succeeded |
| `error` | `str` | `None` | Error message if `success` is `False` |
| `tool_calls` | `list` | `None` | Tool calls requested by the LLM |
| `finish_reason` | `str` | `None` | Why generation stopped (e.g. `"stop"`, `"tool_calls"`) |
| `stream_chunks` | `list` | `None` | Collected chunks for streaming responses |
| `structured_output` | `dict` | `None` | Parsed JSON for structured responses |

### LLMProvider (Abstract Base Class)

Base class for implementing custom LLM providers.

```python
from leafmesh import LLMProvider, LLMRequest, LLMResponse
```

| Method | Signature | Description |
|--------|-----------|-------------|
| `generate` | `async def generate(self, request: LLMRequest) -> LLMResponse` | Generate a response from the LLM (required) |
| `is_available` | `def is_available(self) -> bool` | Check if provider is properly configured (required) |

The base class also handles automatic context truncation on provider context-length errors and reasoning-tool injection when `reasoning=True` is set on a request.

---

## Model Selection Guide

| Use Case | Recommended Model | Why |
|----------|-------------------|-----|
| Triage / classification | `gpt-4o-mini` | Fast, cheap, accurate for structured tasks |
| Complex analysis | `gpt-4o` or `claude-3.5-sonnet` | Strong reasoning, broad capability |
| High-volume processing | `gemini-2.0-flash` | Fast response time, cost-efficient |
| Code generation | `gpt-4o` or `deepseek-coder` | Strong code capabilities |
| Reasoning-heavy tasks | `o1` or `deepseek-reasoner` | Built for multi-step reasoning |
| Sensitive data | Local model (Ollama/vLLM) | Data never leaves the network |
| Creative content | `claude-3.5-sonnet` | Strong creative writing |
| Budget-conscious | `gpt-4o-mini` or `gemini-2.0-flash` | Lowest per-token cost |
| Unified cloud billing | `bedrock/*`, `vertex/*`, or `foundry/*` | Single bill, IAM access control |
| Multi-model via AWS | `bedrock/claude-3.5-sonnet` | AWS VPC, IAM roles, CloudTrail |
| Multi-model via GCP | `vertex/gemini-2.5-flash` | GCP IAM, single project billing |
| Multi-model via Azure | `foundry/gpt-4o` | Azure IAM, unified Azure billing |

---

## Next Steps

- **[Adaptive Execution](adaptive-execution)** -- Automatic model selection based on request characteristics
- **[Agent Configuration](../api-reference/agent-config)** -- Full YAML reference including model settings
- **[Tools](../tools/overview)** -- Extend agents with tool calling across providers
- **[Architecture Guide](../core-concepts/architecture)** -- How LLM calls fit into the control plane

---

*LeafMesh -- One interface, any model, automatic routing*
