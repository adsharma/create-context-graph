"""Project configuration model."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, computed_field


SUPPORTED_FRAMEWORKS = [
    "pydanticai",
    "claude-agent-sdk",
    "strands",
    "google-adk",
    "openai-agents",
    "langgraph",
    "crewai",
    "maf",
]

FRAMEWORK_DISPLAY_NAMES = {
    "pydanticai": "PydanticAI",
    "claude-agent-sdk": "Claude Agent SDK",
    "strands": "Strands (AWS)",
    "google-adk": "Google ADK",
    "openai-agents": "OpenAI Agents SDK",
    "langgraph": "LangGraph",
    "crewai": "CrewAI",
    "maf": "MAF (Modular Agent Framework)",
}

FRAMEWORK_DEPENDENCIES = {
    "pydanticai": ["pydantic-ai>=0.1"],
    "claude-agent-sdk": ["claude-agent-sdk>=0.1"],
    "strands": ["strands-agents>=0.1"],
    "google-adk": ["google-adk>=0.1"],
    "openai-agents": ["openai-agents>=0.1"],
    "langgraph": ["langgraph>=0.1"],
    "crewai": ["crewai>=0.1"],
    "maf": ["maf>=0.1"],
}


class ProjectConfig(BaseModel):
    """All configuration collected from the wizard or CLI flags."""

    project_name: str = Field(description="Human-readable project name")
    domain: str = Field(description="Domain ID from ontology YAML")
    framework: str = Field(description="Agent framework key")
    data_source: Literal["demo", "saas"] = Field(default="demo")
    neo4j_uri: str = Field(default="neo4j://localhost:7687")
    neo4j_username: str = Field(default="neo4j")
    neo4j_password: str = Field(default="password")
    neo4j_type: Literal["aurads", "aura-free", "docker", "existing"] = Field(
        default="docker"
    )
    anthropic_api_key: str | None = Field(default=None)
    openai_api_key: str | None = Field(default=None)
    generate_data: bool = Field(default=False)

    @computed_field
    @property
    def project_slug(self) -> str:
        """Kebab-case slug derived from project name."""
        slug = self.project_name.lower().strip()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        return slug.strip("-")

    @property
    def framework_display_name(self) -> str:
        return FRAMEWORK_DISPLAY_NAMES.get(self.framework, self.framework)

    @property
    def framework_deps(self) -> list[str]:
        return FRAMEWORK_DEPENDENCIES.get(self.framework, [])
