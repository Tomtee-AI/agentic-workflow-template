"""
Specialist: Research Agent
Searches, retrieves, and synthesizes information from allowed sources.
"""

import uuid
from src.shared.contracts import AgentResponse, TaskEnvelope
from src.tier3_agents.base_agent import BaseAgent, CapabilityManifest
from src.tier2_orchestrator.router import register_agent


class ResearchAgent(BaseAgent):
    manifest = CapabilityManifest(
        capability="research",
        version="1.0.0",
        allowed_tools=["web_search", "document_fetch", "vector_search"],
        input_schema={"query": "string", "max_sources": "integer"},
        output_schema={"summary": "string", "sources": "array"},
        cost_class="medium",
        latency_class="batch",
        safety_class="read-only",
    )

    def run(self, envelope: TaskEnvelope, inputs: dict) -> AgentResponse:
        # TODO: implement LLM call with scoped system prompt from config/prompts/
        return AgentResponse(
            agent_id="research",
            run_id=str(uuid.uuid4()),
            output={"summary": "", "sources": []},
        )


register_agent("research", ResearchAgent)
