"""External Agent Reference — ALL external integrations documented here.

NOTE: This file is named external_agents.py (NOT *_agent.py) so auto_discover
skips it. Everything here is COMMENTED OUT — uncomment what you need.

Each section includes:
  - Required environment variables
  - YAML config to add to config.yaml
  - Python implementation code

All connectors are included with `pip install leafmesh` — no extra installs needed.

For each integration, you have TWO options:
  1. Add the YAML config to config.yaml as an external agent
  2. Use helper factories to wire into an existing agent's pipeline
     (works with @pre_compose, @chain, and @conditional_chain)
"""

# ===================================================================
# 1. CREWAI — Delegate to a CrewAI crew
# ===================================================================
#
# YAML config (add to agents: section in config.yaml):
#   crewai_research:
#     name: "crewai_research"
#     agent_type: "external"
#     framework: "crewai"
#     description: "Delegates research tasks to a CrewAI crew"
#     connector_config:
#       endpoint: "http://localhost:9000"
#       api_key: "${CREWAI_API_KEY:}"
#     yields:
#       research_result: "string"
#       sources: "list"
#     can_call:
#       - agent: "advisor_agent"
#
# Python (create agency/crewai_research_agent.py):
# from leafmesh import pre_compose
#
# async def crewai_research_agent(external_response, input_data, context):
#     """Post-process CrewAI crew results."""
#     return {
#         "research_result": external_response.get("output", ""),
#         "sources": external_response.get("sources", []),
#     }


# ===================================================================
# 2. LANGGRAPH — Delegate to a LangGraph graph
# ===================================================================
#
# YAML config:
#   langgraph_workflow:
#     name: "langgraph_workflow"
#     agent_type: "external"
#     framework: "langgraph"
#     description: "Runs a LangGraph stateful workflow"
#     connector_config:
#       endpoint: "${LANGGRAPH_API_URL:http://localhost:8123}"
#       api_key: "${LANGGRAPH_API_KEY:}"
#       graph_id: "my_graph"
#     yields:
#       workflow_result: "object"
#
# Python (create agency/langgraph_workflow_agent.py):
# async def langgraph_workflow_agent(external_response, input_data, context):
#     return {"workflow_result": external_response}


# ===================================================================
# 3. AUTOGEN — Delegate to an AutoGen agent group
# ===================================================================
#
# YAML config:
#   autogen_team:
#     name: "autogen_team"
#     agent_type: "external"
#     framework: "autogen"
#     description: "Multi-agent conversation via AutoGen"
#     connector_config:
#       endpoint: "http://localhost:8081"
#     yields:
#       team_result: "string"
#
# Python (create agency/autogen_team_agent.py):
# async def autogen_team_agent(external_response, input_data, context):
#     return {"team_result": external_response.get("output", "")}


# ===================================================================
# 4. A2A (Agent-to-Agent Protocol) — Google's interop standard
# ===================================================================
#
# YAML config:
#   a2a_partner:
#     name: "a2a_partner"
#     agent_type: "external"
#     framework: "a2a"
#     description: "Communicates with an A2A-compatible agent"
#     connector_config:
#       endpoint: "http://partner-agent:8080"
#       agent_card_url: "http://partner-agent:8080/.well-known/agent.json"
#     yields:
#       partner_response: "object"
#
# Python (create agency/a2a_partner_agent.py):
# async def a2a_partner_agent(external_response, input_data, context):
#     return {"partner_response": external_response}


# ===================================================================
# 5. MCP (Model Context Protocol) — Tool servers
# ===================================================================
#
# Two transport modes: HTTP (SSE) and stdio
#
# YAML config (HTTP mode):
#   mcp_tools:
#     name: "mcp_tools"
#     agent_type: "external"
#     framework: "mcp"
#     description: "Access tools from an MCP server"
#     connector_config:
#       transport: "http"
#       endpoint: "http://localhost:3000/sse"
#     yields:
#       tool_results: "object"
#
# YAML config (stdio mode):
#   mcp_local:
#     name: "mcp_local"
#     agent_type: "external"
#     framework: "mcp"
#     description: "Local MCP tool server via stdio"
#     connector_config:
#       transport: "stdio"
#       command: "npx"
#       args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
#     yields:
#       tool_results: "object"
#
# Python (create agency/mcp_tools_agent.py):
# async def mcp_tools_agent(external_response, input_data, context):
#     return {"tool_results": external_response}


# ===================================================================
# 6. ZAPIER — Natural Language Actions
# ===================================================================
#
# Set env: ZAPIER_NLA_API_KEY=your-key
#
# YAML config:
#   zapier_actions:
#     name: "zapier_actions"
#     agent_type: "external"
#     framework: "zapier"
#     description: "Trigger Zapier NLA actions"
#     connector_config:
#       api_key: "${ZAPIER_NLA_API_KEY:}"
#     yields:
#       action_result: "object"
#
# Python (create agency/zapier_actions_agent.py):
# async def zapier_actions_agent(external_response, input_data, context):
#     return {"action_result": external_response}


# ===================================================================
# 7. COMPOSIO — Managed tool integrations (GitHub, Slack, etc.)
# ===================================================================
#
# Set env: COMPOSIO_API_KEY=your-key
#
# YAML config:
#   composio_tools:
#     name: "composio_tools"
#     agent_type: "external"
#     framework: "composio"
#     description: "Access Composio-managed integrations"
#     connector_config:
#       api_key: "${COMPOSIO_API_KEY:}"
#       actions: ["github_star_repo", "slack_send_message"]
#     yields:
#       integration_result: "object"
#
# Python (create agency/composio_tools_agent.py):
# async def composio_tools_agent(external_response, input_data, context):
#     return {"integration_result": external_response}


# ===================================================================
# 8. N8N — Workflow automation
# ===================================================================
#
# Set env: N8N_BASE_URL=http://localhost:5678, N8N_API_KEY=your-key
#
# YAML config:
#   n8n_workflow:
#     name: "n8n_workflow"
#     agent_type: "external"
#     framework: "n8n"
#     description: "Trigger n8n workflows"
#     connector_config:
#       base_url: "${N8N_BASE_URL:http://localhost:5678}"
#       api_key: "${N8N_API_KEY:}"
#       workflow_id: "your-workflow-id"
#     yields:
#       workflow_result: "object"
#
# Python (create agency/n8n_workflow_agent.py):
# async def n8n_workflow_agent(external_response, input_data, context):
#     return {"workflow_result": external_response}


# ===================================================================
# 9. HELPER FACTORIES — Wire integrations into agent decorators
#
# These work with @pre_compose (before LLM), @chain (after agent),
# and @conditional_chain (conditional post-processing).
# ===================================================================
#
# from leafmesh import pre_compose, chain, conditional_chain, mcp, zapier, composio, n8n
#
# # ── @pre_compose: run BEFORE the LLM call ──
# @pre_compose(context_processor=mcp("https://mcp.example.com", "get_weather", args={"city": "NYC"}))
# def weather_agent(llm_response, input_data, context):
#     return {"result": llm_response}
#
# # ── @chain: run AFTER the agent completes ──
# @chain(zapier("send_slack_message", connection="slack"))
# async def notify_agent(llm_response, input_data, context):
#     return {"message": llm_response.get("summary")}
#
# # ── @conditional_chain: run conditionally after the agent ──
# @conditional_chain(lambda r, ctx: r.get("needs_enrichment"), composio("GITHUB_STAR_REPO"))
# async def enricher(llm_response, input_data, context):
#     return {"needs_enrichment": True, "data": llm_response}
#
# # ── n8n webhook as a chain step ──
# @chain(n8n("https://my-n8n.example.com/webhook/notify"))
# async def alert_agent(llm_response, input_data, context):
#     return {"event": "completed", "data": llm_response}


# ===================================================================
# 10. CUSTOM CONNECTOR — Build your own integration
# ===================================================================
#
# from leafmesh.external.connectors.base_connector import ExternalConnector
#
# class MyCustomConnector(ExternalConnector):
#     """Custom connector for your proprietary system."""
#
#     async def connect(self):
#         """Initialize connection to the external system."""
#         self.client = await create_my_client(self.config)
#
#     async def execute(self, input_data: dict) -> dict:
#         """Send data to the external system and return results."""
#         response = await self.client.run(input_data)
#         return {"result": response}
#
#     async def disconnect(self):
#         """Clean up resources."""
#         await self.client.close()
#
# # Register in connector_registry:
# from leafmesh.external.connectors.connector_registry import ConnectorRegistry
# ConnectorRegistry.register("my_system", MyCustomConnector)
#
# # Then use in YAML:
# #   my_agent:
# #     agent_type: "external"
# #     framework: "my_system"
# #     connector_config:
# #       endpoint: "http://my-system:8080"
