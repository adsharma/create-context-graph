"""Shared test fixtures."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from create_context_graph.config import ProjectConfig
from create_context_graph.ontology import load_domain


@pytest.fixture
def tmp_output(tmp_path: Path) -> Path:
    """Provide a clean temporary output directory."""
    out = tmp_path / "test-project"
    out.mkdir()
    return out


@pytest.fixture
def financial_config() -> ProjectConfig:
    """A minimal config for the financial-services domain."""
    return ProjectConfig(
        project_name="Test Financial App",
        domain="financial-services",
        framework="pydanticai",
        neo4j_uri="neo4j://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="password",
        neo4j_type="docker",
    )


@pytest.fixture
def healthcare_config() -> ProjectConfig:
    """A config for the healthcare domain with Claude Agent SDK."""
    return ProjectConfig(
        project_name="Test Health App",
        domain="healthcare",
        framework="claude-agent-sdk",
        neo4j_uri="neo4j://localhost:7687",
        neo4j_username="neo4j",
        neo4j_password="password",
        neo4j_type="docker",
    )


@pytest.fixture
def financial_ontology():
    """Load the financial-services ontology."""
    return load_domain("financial-services")


@pytest.fixture
def healthcare_ontology():
    """Load the healthcare ontology."""
    return load_domain("healthcare")
